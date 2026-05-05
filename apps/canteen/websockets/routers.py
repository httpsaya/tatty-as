# websockets/routing.py
from django.urls import re_path
from .consumers import CommentConsumer

ws_urlpatterns = [
    re_path(r"^ws/comments/dish/(?P<dish_id>\d+)/$",  CommentConsumer.as_asgi()),
    re_path(r"^ws/comments/menu/(?P<menu_id>\d+)/$",  CommentConsumer.as_asgi()),
]