# DRF Modules
from rest_framework.serializers import ModelSerializer

# Project Modules
from .models import Notification


class NotificationSerializer(ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            'user',
            "type",
            "title",
            "message",
            "is_read",
            "link",
            "related_object_id",
            "related_object_type",
            "created_at",
        ]