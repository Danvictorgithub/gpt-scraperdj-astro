from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
import requests
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import Http404
from conversations.models import Conversation
from .serializers import ChatRequestSerializer
from  aiohttp import ClientSession
import asyncio
from adrf.decorators import api_view as async_api_view
from enum import Enum
from asgiref.sync import sync_to_async
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
            initial_responses = await asyncio.gather(
                fetch_url(f"{server_urls[0]}/conversation/",HTTPMethod.POST,data={"chatId":chatOne,"prompt":f"{serializer.data['initial_message']} topid: {serializer.data['topic']}"}),
                fetch_url(f"{server_urls[1]}/conversation/",HTTPMethod.POST,data={"chatId":chatTwo,"prompt":f"{serializer.data['initial_message']} topid: {serializer.data['topic']}"})
                )
            print("Chat Initial Message Responded","\n")
        except Exception as e:
            return Response({'message':str(e),noConversation:noConversation}, status=status.HTTP_400_BAD_REQUEST)
        try:
            chat_one_response = initial_responses[0]
            chat_two_response = await fetch_url(f"{server_urls[1]}/conversation/",HTTPMethod.POST,data={"chatId":chatTwo,"prompt":"You start the conversation"})
            for i in range(serializer.data['max_prompt']):
                chat_one_response = await fetch_url(f"{server_urls[0]}/conversation/",HTTPMethod.POST,data={"chatId":chatOne,"prompt":chat_two_response["response"]})
                print("chatOne: ",chat_one_response["response"],"\n")
                chat_two_response = await fetch_url(f"{server_urls[1]}/conversation/",HTTPMethod.POST,data={"chatId":chatTwo,"prompt":chat_one_response["response"]})
                print("chattwo: ",chat_two_response["response"],"\n")
                noConversation += 1
                print(f"Chat conversation generated : {noConversation}","\n")
                await sync_to_async(Conversation.objects.create)(start_conversation=chat_one_response["response"], end_conversation=chat_two_response["response"])
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
            responses = []
            for url in server_urls:
                response = requests.post(f"{url}/start", json={})
                if response.status_code == 200:
                    responses.append(response.json())
                else:
                    raise Exception("Failed to start conversation")
            print("Chat Initialized")
            chatOne = responses[0]["chatId"]
            chatTwo = responses[1]["chatId"]
            initial_responses = []
            for url, chatId in zip(server_urls, [chatOne, chatTwo]):
                response = requests.post(f"{url}/conversation/", json={"chatId": chatId, "prompt": f"{serializer.data['initial_message']} topic: {serializer.data['topic']}"})
                if response.status_code == 200:
                    initial_responses.append(response.json())
                else:
                    raise Exception("Failed to send initial message")
            print("Chat Initial Message Responded", "\n")
            # Continue with your logic for the conversation...
        except Exception as e:
            return Response({'message': str(e), 'noConversation': noConversation}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': "Conversation generated successfully."})
    else:
         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)