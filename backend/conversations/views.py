from rest_framework import viewsets 
from .models import Conversation
from .serializers import ConversationSerializer
from rest_framework.permissions import IsAdminUser

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAdminUser]
    
