# apps/canteen/websockets/routers.py
from django.urls import path
from .consumers import CommentConsumer

ws_urlpatterns = [
    path('ws/comments/dish/<int:dish_id>/', CommentConsumer.as_asgi()),
]