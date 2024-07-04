from django.http import JsonResponse
from django.urls import path
from .views import BookAPIView

urlpatterns = [
    path("books/",BookAPIView.as_view(),name="book_list"),
    path("",lambda request : JsonResponse({"message":"Welcome to the API"})) 
]
