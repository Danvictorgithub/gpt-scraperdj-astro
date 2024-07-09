from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import Http404

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
