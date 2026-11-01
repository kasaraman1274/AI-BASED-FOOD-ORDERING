from django.urls import path
from . import views

urlpatterns = [
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/chat/add-to-cart/', views.add_to_cart_api, name='chat_add_to_cart_api'),
]
