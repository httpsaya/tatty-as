# Django Modules
from django.contrib.admin import register, ModelAdmin

# Project Modules
from .models import Notification

@register(Notification)
class NotificationAdminModel(ModelAdmin):
    """Admin model for CustomUser."""
    list_display = (
        "id",
        "user",
        "type",
        "title",
        "message",
        'is_read',
        'link',
        'related_object_id',
        'related_object_type',
    )
    search_fields = ('user__email', 'user__username', 'title', 'message')
    list_filter = ('type', 'is_read', 'created_at')
    ordering = ("user",)