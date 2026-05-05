# Python Modules
from uuid import uuid4

# Django Modules
from django.db.models import (
    UUIDField,
    ForeignKey,
    CharField,
    CASCADE,
    TextField,
    BooleanField,
    URLField,
    TextChoices,
    )

# Project Modules
from apps.auths.models import CustomUser
from apps.abstracts.models import AbstractBaseModel


class Notification(AbstractBaseModel):
     """Notification model with common fields."""
     
     class NotificationTypes(TextChoices):
        COMMENT = 'comment', 'Comment'
        LIKE = 'like', 'Like'
        FOLLOW = 'follow', 'Follow'
        EVENT = 'event', 'Event'
        COMMUNITY = 'community', 'Community'
        POST = 'post', 'Post'
         
     id = UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False
        )
     user = ForeignKey(
        to=CustomUser,
        on_delete=CASCADE,
        related_name='notifications'
        )
     type = CharField(
        max_length=20,
        choices=NotificationTypes.choices,
        default='post'
        )
     title = CharField(
        max_length=200,
        blank=True
        )
     message = TextField()
     is_read = BooleanField(default=False)
     link = URLField(
        blank=True,
        null=True
        )
     related_object_id = UUIDField(
        null=True,
        blank=True,
        help_text="ID связанного объекта (пост, комментарий, событие и тд)"
        )
     related_object_type = CharField(
        max_length=50,
        blank=True,
        help_text="Тип связанного объекта (post, comment, event и тд)"
        )
     
     class Meta:
        ordering = ['-created_at']
        def __str__(self):
            return f"{self.type} notification for {self.user.username}"