from django.urls import path
from .views import ConversationViewSet,stats
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register('', ConversationViewSet, basename='conversations')
urlpatterns = [
    path('stats/', stats),
] + router.urls
