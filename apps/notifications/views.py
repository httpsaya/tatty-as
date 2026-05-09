import asyncio
import json
from typing import Any

from django.http.response import StreamingHttpResponse
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.pagination import PageNumberPagination
from rest_framework.status import HTTP_200_OK
from channels.layers import get_channel_layer

from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification
from .serializers import NotificationSerializer

User = get_user_model()


async def sse_notifications(request):
    canteen_id = request.GET.get('canteen_id')
    token_key  = request.GET.get('token')

    if not canteen_id:
        return StreamingHttpResponse(status=400)

    # ── Аутентификация по токену из query params ──
    try:
        validated = AccessToken(token_key)
        user = await User.objects.aget(id=validated['user_id'])
    except Exception:
        return StreamingHttpResponse(status=401)

    channel_layer = get_channel_layer()

    async def event_stream():
        channel_name = await channel_layer.new_channel()
        group_name   = f'canteen_{canteen_id}'
        await channel_layer.group_add(group_name, channel_name)
        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        channel_layer.receive(channel_name),
                        timeout=30
                    )
                    # Нормализуем тип для фронтенда
                    if message['type'] in ('dailymenu.message', 'daily_menu_created'):
                        payload = message.get('data', message)
                        payload['event'] = 'daily_menu_created'  # фронт ждёт именно это
                        yield f'data: {json.dumps(payload)}\n\n'

                except asyncio.TimeoutError:
                    yield ': ping\n\n'  # keepalive
        finally:
            await channel_layer.group_discard(group_name, channel_name)

    return StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


class NotificationViewSet(ViewSet):

    @action(methods=('GET',), detail=False, url_path='count', url_name='count', permission_classes=(IsAuthenticated,))
    def get_count(self, request: DRFRequest, *args, **kwargs) -> DRFResponse:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return DRFResponse({'unread_count': count})

    @action(methods=('GET',), detail=False, url_path='list', url_name='list', permission_classes=(IsAuthenticated,))
    def get_list(self, request: DRFRequest, *args, **kwargs) -> DRFResponse:
        notifications = Notification.objects.filter(user=request.user)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(notifications, request)  # ← был баг: DRFRequest класс вместо request
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=('POST',), detail=False, url_path='read', url_name='read', permission_classes=(IsAuthenticated,))
    def mark_read(self, request: DRFRequest, *args, **kwargs) -> DRFResponse:
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return DRFResponse({'marked_read': updated}, status=HTTP_200_OK)