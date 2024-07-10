from .views import ConversationViewSet
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register('', ConversationViewSet, basename='conversations')
urlpatterns = router.urls