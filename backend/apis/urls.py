
from django.urls import path,include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView,TokenVerifyView
from .views import ConfirmEmailView, generate_conversation_gemini,greetings,generate_conversation,generate_conversation_sync
from dj_rest_auth.registration.views import VerifyEmailView
urlpatterns = [
    path('',greetings),
    # path(
    #     'auth/register/account-confirm-email/<str:key>/',
    #     ConfirmEmailView.as_view(),
    #     name='account_confirm_email'
    # ),
    path('auth/', include("dj_rest_auth.urls")),
    path('auth/register/', include("dj_rest_auth.registration.urls")),
    path('auth/register/account-confirm-email/', VerifyEmailView.as_view(), name='account_email_verification_sent'),
    path('auth/token/', TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('users/',include('users.urls')),
    path('conversations/',include('conversations.urls')),
    path('generate_conversation',generate_conversation),
    path('generate_conversation_sync',generate_conversation_sync),
    path('generate_conversation_gemini',generate_conversation_gemini)
]
