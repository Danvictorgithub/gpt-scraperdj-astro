
from django.urls import path,include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView,TokenVerifyView
from .views import ConfirmEmailView
urlpatterns = [
    path(
        'auth/register/account-confirm-email/<str:key>/',
        ConfirmEmailView.as_view(),
        name='account_confirm_email'
    ),
    path('auth/', include("dj_rest_auth.urls")),
    path('auth/register/', include("dj_rest_auth.registration.urls")),
    path('auth/token/', TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/',include('users.urls')),
]
