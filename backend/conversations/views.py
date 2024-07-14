import datetime
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from .models import Conversation
from .serializers import ConversationSerializer
from rest_framework.permissions import IsAdminUser

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAdminUser]
    
    
@api_view(['GET'])
@permission_classes([IsAdminUser])
def stats(request):
    today = timezone.now().date()
    first_ten_conversations = Conversation.objects.order_by('created_at')[:10]
    serialized_conversations = ConversationSerializer(first_ten_conversations, many=True).data  # Serialize the queryset

    data = {
        "total_conversations": Conversation.objects.count(),
        "conversations_today": Conversation.objects.filter(created_at__date=today).count(),
        "conversations_rate_per_hour": Conversation.objects.filter(created_at__date=today).count() / max(timezone.now().hour, 1),
        "conversations_rate_per_hour_week": [
            Conversation.objects.filter(created_at__date=today - datetime.timedelta(days=i)).count() / (24 if i > 0 else max(timezone.now().hour, 1))
            for i in range(7)
        ][::-1],
        "conversations_day":[
            Conversation.objects.filter(created_at__date=today - datetime.timedelta(days=i)).count()
            for i in range(7)
        ][::-1],
        "first_ten_conversations": serialized_conversations,  # Use the serialized data
    }
    return Response(data)