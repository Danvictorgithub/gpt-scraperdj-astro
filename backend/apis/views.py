import os
import time
from time import sleep
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
import requests
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import Http404
from conversations.models import Conversation
from .serializers import ChatRequestGeminiRandomSeralizer, ChatRequestGeminiSeralizer, ChatRequestSerializer
from aiohttp import ClientSession
import asyncio
from adrf.decorators import api_view as async_api_view
from enum import Enum
from asgiref.sync import sync_to_async
from .utils import generate_text, generate_random_subject
from queue import Queue
from threading import Thread, Lock
import logging
from pathlib import Path
import json
import platform
from django.db import connections
from django.db.utils import OperationalError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUEUE_FILE = "conversation_queue.json"
file_lock = Lock()
DB_CONNECTED = False

class FileLock:
    def __init__(self, file):
        self.file = file
        self.platform = platform.system()

    def __enter__(self):
        if self.platform == 'Windows':
            import msvcrt
            self.handle = self.file.fileno()
            msvcrt.locking(self.handle, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(self.file.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.platform == 'Windows':
            import msvcrt
            msvcrt.locking(self.handle, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)

class PersistentQueue:
    def __init__(self):
        self.memory_queue = Queue()
        self.queue_file = Path(QUEUE_FILE)
        self.ensure_queue_file()
        self.load_pending_items()

    def ensure_queue_file(self):
        if not self.queue_file.exists():
            logger.info(f"Creating new queue file: {QUEUE_FILE}")
            self.queue_file.write_text("[]")
        else:
            logger.info(f"Using existing queue file: {QUEUE_FILE}")
            try:
                with open(self.queue_file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Corrupted queue file detected.")
                self.create_backup_and_new_file()

    def create_backup_and_new_file(self):
        backup_file = Path(f"{QUEUE_FILE}.bak")
        if backup_file.exists():
            logger.warning(f"Backup file {backup_file} already exists. Creating a uniquely named backup file.")
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            backup_file = Path(f"{QUEUE_FILE}-{timestamp}.bak")
        self.queue_file.rename(backup_file)
        self.queue_file.write_text("[]")
        logger.info(f"Created backup file: {backup_file}")

    def save_to_file(self, item):
        with file_lock:
            try:
                with open(self.queue_file, 'r+') as f:
                    with FileLock(f):
                        try:
                            items = json.load(f)
                        except json.JSONDecodeError:
                            items = []
                        
                        # Keep only unprocessed items
                        items = [item for item in items if not item.get('processed', False)]
                        
                        # Add new item
                        items.append({
                            'start_response': item[0],
                            'end_response': item[1],
                            'timestamp': time.time(),
                            'processed': False
                        })
                        
                        # Write back with pretty formatting
                        f.seek(0)
                        json.dump(
                            items, 
                            f,
                            indent=2,
                            ensure_ascii=False,
                            separators=(',', ': ')
                        )
                        f.truncate()
            except Exception as e:
                logger.error(f"Error saving to queue file: {e}")

    def load_pending_items(self):
        with file_lock:
            try:
                with open(self.queue_file, 'r') as f:
                    with FileLock(f):
                        items = json.load(f)
                        
                        unprocessed = [item for item in items if not item.get('processed', False)]
                        logger.info(f"Loading {len(unprocessed)} unprocessed items from queue file")
                        
                        for item in unprocessed:
                            self.memory_queue.put((
                                item['start_response'],
                                item['end_response']
                            ))
                            
            except Exception as e:
                logger.error(f"Error loading from queue file: {e}")

    def mark_processed(self, start_response, end_response):
        with file_lock:
            try:
                with open(self.queue_file, 'r+') as f:
                    with FileLock(f):
                        items = json.load(f)
                        
                        # Keep only unprocessed items and items that don't match
                        items = [item for item in items if not (
                            item['start_response'] == start_response and 
                            item['end_response'] == end_response
                        )]
                        
                        # Write back the filtered items
                        f.seek(0)
                        json.dump(
                            items,
                            f,
                            indent=2,
                            ensure_ascii=False,
                            separators=(',', ': ')
                        )
                        f.truncate()
            except Exception as e:
                logger.error(f"Error removing processed item: {e}")

persistent_queue = PersistentQueue()

def check_db_connection():
    global DB_CONNECTED
    db_conn = connections['default']
    try:
        db_conn.ensure_connection()
        DB_CONNECTED = True
        return True
    except OperationalError:
        DB_CONNECTED = False
        return False

def process_queue():
    while True:
        if not check_db_connection():
            logger.warning("Database connection not available. Retrying in 5 seconds...")
            sleep(5)
            continue

        queue_size = persistent_queue.memory_queue.qsize()
        logger.info(f"Current queue size: {queue_size}")
        
        if queue_size > 0:
            start_response, end_response = persistent_queue.memory_queue.get()
            attempt = 0
            max_retries = 3
            retry_delay = 5
            
            process_start_time = time.time()
            conversation = None
            
            while attempt < max_retries:
                try:
                    attempt += 1
                    logger.info(f"Processing conversation: start_response={start_response}, end_response={end_response}")
                    
                    conversation = Conversation.objects.create(
                        start_conversation=start_response,
                        end_conversation=end_response
                    )
                    
                    persistent_queue.mark_processed(start_response, end_response)
                    process_end_time = time.time()
                    process_duration = process_end_time - process_start_time
                    
                    logger.info(f"Successfully created Conversation with ID: {conversation.id}")
                    logger.info(f"Processing time: {process_duration:.2f} seconds")
                    break
                    
                except Exception as e:
                    logger.error(f"Attempt {attempt} failed: {e}")
                    if attempt < max_retries:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        sleep(retry_delay)
                    else:
                        logger.error("Max retries reached, keeping in file queue")
                finally:
                    if attempt >= max_retries or conversation:
                        persistent_queue.memory_queue.task_done()
                        logger.info(f"Queue size: {persistent_queue.memory_queue.qsize()}")
            
            # Rate limiting - wait 1 second between items
            sleep(1)
        else:
            # If queue is empty, wait before checking again
            sleep(5)

def enqueue_conversation(start_response, end_response):
    item = (start_response, end_response)
    persistent_queue.save_to_file(item)
    persistent_queue.memory_queue.put(item)
    if DB_CONNECTED:
        logger.info(f"Enqueued conversation to persistent queue")
        logger.info(f"Queue size: {persistent_queue.memory_queue.qsize()}")

# Start the worker thread
worker_thread = Thread(target=process_queue, daemon=True)
worker_thread.start()

class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
class ConfirmEmailView(APIView):
    def get(self, request, key, *args, **kwargs):
        try:
            confirmation = EmailConfirmationHMAC.from_key(key)
            if not confirmation:
                raise Http404
        except EmailConfirmation.DoesNotExist:
            confirmation = get_object_or_404(EmailConfirmation, key=key)
        
        confirmation.confirm(request)
        return Response({'detail': 'Email confirmed'}, status=status.HTTP_200_OK)



@api_view(['GET'])
def greetings(request):
    return Response({'message':"Welcome to GPT-3 Conversations API. Please use the appropriate endpoints to interact with the API."})

async def fetch_url(url, method: HTTPMethod = HTTPMethod.GET,*args,**kwargs):
    async with ClientSession() as session:
        method_action = {
            HTTPMethod.GET: session.get,
            HTTPMethod.POST: session.post,
            HTTPMethod.DELETE: session.delete,
            HTTPMethod.PUT: session.put,
        }.get(method, session.get)  # Default to GET if method is not found

        async with method_action(url,*args,**kwargs) as response:
            return await response.json()

@async_api_view(['POST'])
async def generate_conversation(request):
    serializer = ChatRequestSerializer(data=request.data)
    if (serializer.is_valid()):
        server_urls = [serializer.data['server_url'] ]
        if ('server_url_2' in serializer.data):
            server_urls.append(serializer.data['server_url_2'])
        else:
            server_urls.append(serializer.data['server_url'])
        try:
            noConversation = 0
            responses = await asyncio.gather(*[fetch_url(f"{url}/start",HTTPMethod.POST) for url in server_urls])
            print("Chat Initalized")
            chatOne = responses[0]["chatId"]
            chatTwo = responses[1]["chatId"]
            # initial_responses = await asyncio.gather(
            #     fetch_url(f"{server_urls[0]}/conversation/",HTTPMethod.POST,data={"chatId":chatOne,"prompt":f"{serializer.data['initial_message']} topic: {serializer.data['topic']}"}),
            #     fetch_url(f"{server_urls[1]}/conversation/",HTTPMethod.POST,data={"chatId":chatTwo,"prompt":f"{serializer.data['initial_message']} topic: {serializer.data['topic']}"})
            #     )
            # print("Chat Initial Message Responded","\n")
            initial_response_one = await fetch_url(
                f"{server_urls[0]}/conversation/",
                HTTPMethod.POST,
                data={"chatId": chatOne, "prompt": f"{serializer.data['initial_message']} topic: {serializer.data['topic']}"}
            )
            print("First chat initial message responded")

            initial_response_two = await fetch_url(
                f"{server_urls[1]}/conversation/",
                HTTPMethod.POST,
                data={"chatId": chatTwo, "prompt": f"{serializer.data['initial_message']} topic: {serializer.data['topic']}"}
            )
            print("Second chat initial message responded")

            print("Chat Initial Messages Responded\n")
            print(f"initial_response_one: {initial_response_one}")
            print(f"initial_response_two: {initial_response_two}")
        except Exception as e:
            return Response({'message':str(e),noConversation:noConversation}, status=status.HTTP_400_BAD_REQUEST)
        try:
            chat_one_response = initial_response_one
            chat_two_response = await fetch_url(f"{server_urls[1]}/conversation/",HTTPMethod.POST,data={"chatId":chatTwo,"prompt":"You start the conversation"})
            for i in range(serializer.data['max_prompt']):
                chat_one_response = await fetch_url(f"{server_urls[0]}/conversation/",HTTPMethod.POST,data={"chatId":chatOne,"prompt":chat_two_response["response"]})
                print("chatOne: ",chat_one_response["response"],"\n")
                sleep(10)
                chat_two_response = await fetch_url(f"{server_urls[1]}/conversation/",HTTPMethod.POST,data={"chatId":chatTwo,"prompt":chat_one_response["response"]})
                print("chattwo: ",chat_two_response["response"],"\n")
                noConversation += 1
                print(f"Chat conversation generated : {noConversation}","\n")
                sleep(10) 
                enqueue_conversation(chat_one_response["response"], chat_two_response["response"])
        except Exception as e:
            return Response({'message':str(e),noConversation:noConversation}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message':"Conversation generated successfully."})
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def generate_conversation_sync(request):
    serializer = ChatRequestSerializer(data=request.data)
    if serializer.is_valid():
        server_urls = [serializer.data['server_url']]
        if 'server_url_2' in serializer.data:
            server_urls.append(serializer.data['server_url_2'])
        else:
            server_urls.append(serializer.data['server_url'])
        try:
            noConversation = 0
            responses = [requests.post(f"{url}/start", json={}).json() for url in server_urls]
            print("Chat Initialized")
            chatOne = responses[0]["chatId"]
            chatTwo = responses[1]["chatId"]
            initial_responses = [
                requests.post(f"{server_urls[0]}/conversation/", json={"chatId": chatOne, "prompt": f"{serializer.data['initial_message']} topic: {serializer.data['topic']}"}).json(),
                requests.post(f"{server_urls[1]}/conversation/", json={"chatId": chatTwo, "prompt": f"{serializer.data['initial_message']} topic: {serializer.data['topic']}"}).json()
            ]
            print("Chat Initial Message Responded", "\n")
        except Exception as e:
            return Response({'message': str(e), 'noConversation': noConversation}, status=400)
        try:
            chat_one_response = initial_responses[0]
            chat_two_response = requests.post(f"{server_urls[1]}/conversation/", json={"chatId": chatTwo, "prompt": "You start the conversation"}).json()
            for i in range(serializer.data['max_prompt']):
                chat_one_response = requests.post(f"{server_urls[0]}/conversation/", json={"chatId": chatOne, "prompt": chat_two_response["response"]}).json()
                print("chatOne: ", chat_one_response["response"], "\n")
                chat_two_response = requests.post(f"{server_urls[1]}/conversation/", json={"chatId": chatTwo, "prompt": chat_one_response["response"]}).json()
                print("chatTwo: ", chat_two_response["response"], "\n")
                noConversation += 1
                print(f"Chat conversation generated: {noConversation}", "\n")
                Conversation.objects.create(start_conversation=chat_one_response["response"], end_conversation=chat_two_response["response"])
        except Exception as e:
            return Response({'message': str(e), 'noConversation': noConversation}, status=400)
        return Response({'message': "Conversation generated successfully."})
    else:
        return Response(serializer.errors, status=400)
    
@api_view(['POST'])
def generate_conversation_gemini(request):
    serializer = ChatRequestGeminiSeralizer(data=request.data)
    if serializer.is_valid():
        try:
            noConversation = 0
            initial_message = f"{serializer.data['initial_message']} topic: {serializer.data['topic']}"
            chat_one_response = generate_text(initial_message)
            chat_two_response = generate_text(initial_message)
            print("Chat Initial Message Responded", "\n")
        except Exception as e:
            return Response({'message': str(e), 'noConversation': noConversation}, status=400)
        try:
            for i in range(serializer.data['max_prompt']):
                chat_one_response = generate_text(chat_two_response)
                print("chatOne: ", chat_one_response, "\n")
                chat_two_response = generate_text(chat_one_response)
                print("chatTwo: ", chat_two_response, "\n")
                noConversation += 1
                print(f"Chat conversation generated: {noConversation}", "\n")
                Conversation.objects.create(start_conversation=chat_one_response, end_conversation=chat_two_response)
        except Exception as e:
            return Response({'message': str(e), 'noConversation': noConversation}, status=400)
        return Response({'message': "Conversation generated successfully."})
    else:
        return Response(serializer.errors, status=400)
    
@api_view(['POST'])
def generate_conversation_gemini_random(request):
    serializer = ChatRequestGeminiRandomSeralizer(data=request.data)
    if serializer.is_valid():
        try:
            topic = generate_random_subject()
            added_text = "Please respond in less than 400 characters if possible"
            noConversation = 0
            initial_message = f"{serializer.data['initial_message']} {added_text} topic: {topic}"
            chat_one_response = generate_text(f"{initial_message}")
            chat_two_response = generate_text(f"{initial_message}")
            print("Chat Initial Message Responded", "\n")
        except Exception as e:
            return Response({'message': str(e), 'noConversation': noConversation}, status=400)
        try:
            for i in range(serializer.data['max_prompt']):
                chat_one_response = generate_text(f"{chat_two_response} {added_text}  topic: {topic}")
                print("chatOne: ", chat_one_response, "\n")
                chat_two_response = generate_text(f"{chat_one_response} {added_text}  topic: {topic}")
                print("chatTwo: ", chat_two_response, "\n")
                noConversation += 1
                print(f"Chat conversation generated: {noConversation}", "\n")
                Conversation.objects.create(start_conversation=chat_one_response, end_conversation=chat_two_response)
        except Exception as e:
            return Response({'message': str(e), 'noConversation': noConversation}, status=400)
        return Response({'message': "Conversation generated successfully."})
    else:
        return Response(serializer.errors, status=400)
# @api_view(['GET'])
# def gemini_api(request):
#     API_KEY = os.getenv("API_KEY")
#     return Response((f"APIKEY: {API_KEY}"))