import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from ..models import Comment, Dish
from apps.notifications.models import Notification

User = get_user_model()


class CommentConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.dish_id = self.scope['url_route']['kwargs']['dish_id']
        self.room_group_name = f'comments_dish_{self.dish_id}'

        token_str = self.scope['query_string'].decode()
        token = token_str.split('token=')[-1] if 'token=' in token_str else None
        self.user = await self.get_user_from_token(token)

        if self.user:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            comments = await self.get_comment_history()
            await self.send(text_data=json.dumps({
                'type': 'comment.history',
                'comments': comments
            }))
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        text = data.get('text', '').strip()
        if not text or not self.user:
            return

        comment, dish = await self.save_comment(text)

        # Рассылаем комментарий всем в WS группе
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'comment_message',
                'comment_id': str(comment.id),
                'author': self.user.username,
                'text': text,
                'created_at': str(comment.created_at),
            }
        )

        # SSE-уведомление в canteen группу (для фронта)
        canteen_id = await self.get_canteen_id(dish)
        if canteen_id:
            await self.channel_layer.group_send(
                f'canteen_{canteen_id}',
                {
                    'type': 'dailymenu.message',
                    'data': {
                        'event': 'post.message',
                        'message': f'{self.user.username} оставил комментарий к «{dish.name}»',
                    }
                }
            )

    async def comment_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'comment.new',
            'comment_id': event['comment_id'],
            'author': event['author'],
            'text': event['text'],
            'created_at': event['created_at'],
        }))

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            if token:
                access_token = AccessToken(token)
                return User.objects.get(id=access_token['user_id'])
        except Exception:
            pass
        return None

    @database_sync_to_async
    def get_comment_history(self):
        comments = Comment.objects.filter(
            dish_id=self.dish_id, is_visible=True
        ).select_related('author').order_by('created_at')[:50]
        return [
            {'id': str(c.id), 'author': c.author.username, 'text': c.text, 'created_at': str(c.created_at)}
            for c in comments
        ]

    @database_sync_to_async
    def save_comment(self, text):
        dish = Dish.objects.select_related('canteen__school').get(id=self.dish_id)
        comment = Comment.objects.create(
            author=self.user, dish=dish, text=text, is_visible=True
        )

        # Создаём Notification для всех пользователей школы (кроме автора)
        from django.db.models import Q
        from apps.auths.models import CustomUser

        users = CustomUser.objects.filter(
            Q(school=dish.canteen.school) | Q(is_superuser=True),
            is_active=True
        ).exclude(id=self.user.id)

        Notification.objects.bulk_create([
            Notification(
                user=u,
                type='comment',
                title=f'Новый комментарий к «{dish.name}»',
                message=f'{self.user.username}: {text[:100]}',
                is_read=False,
                related_object_type='comment',
            )
            for u in users
        ], ignore_conflicts=True)

        return comment, dish

    @database_sync_to_async
    def get_canteen_id(self, dish):
        return dish.canteen.id