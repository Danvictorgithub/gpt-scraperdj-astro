import os
from time import sleep
import time
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
from  aiohttp import ClientSession
import asyncio
from adrf.decorators import api_view as async_api_view
from enum import Enum
from asgiref.sync import sync_to_async
from .utils import generate_text, generate_random_subject
import queue
from threading import Thread
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the queue
conversation_queue = queue.Queue()
# Define a worker function to process the queue with retry logic, this is important since my db has super role limits
def process_queue():
    while True:
        start_response, end_response = conversation_queue.get()
        attempt = 0
        max_retries = 25
        retry_delay = 5  # seconds

        while attempt < max_retries:
            try:
                attempt += 1
                logger.info(f"Processing conversation: start_response={start_response}, end_response={end_response}")
                # Try to create the Conversation object
                conversation = Conversation.objects.create(
                    start_conversation=start_response,
                    end_conversation=end_response
                )
                # Log the success and set the flag
                logger.info(f"Successfully created Conversation with ID: {conversation.id}")
                logger.info(f"Start_Conversation:{conversation.start_conversation}")
                logger.info(f"End_Conversation:{conversation.end_conversation}")
                break
            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached, giving up.")
            finally:
                # Mark the task as done, even if it failed after max retries
                conversation_queue.task_done()
                logger.info(f"Queue size after processing: {conversation_queue.qsize()}")

    # Start the worker thread (daemon thread will exit when main program exits)
worker_thread = Thread(target=process_queue, daemon=True)
worker_thread.start()

# Helper function to enqueue the conversation creation task
def enqueue_conversation(start_response, end_response):
    conversation_queue.put((start_response, end_response))

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