# apps/notifications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Project Modules
from .views import NotificationViewSet, sse_notifications

router = DefaultRouter()
router.register(
    prefix='',               # ← пустой префикс
    viewset=NotificationViewSet,
    basename='notifications'
)

urlpatterns = [
    path('', include(router.urls)),       
    path('stream/', sse_notifications),
]