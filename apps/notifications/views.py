# Python Modules
import asyncio
import json
from typing import Any

# Django Modules
from django.shortcuts import get_object_or_404, render

# Project Modules
from apps.canteen.models import DailyMenu
from apps.notifications.models import Notification
from .serializers import NotificationSerializer

# Channel Modules
from channels.layers import get_channel_layer

# DRF Modules
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_200_OK
from rest_framework.viewsets import ViewSet

# Django async
from django.http.response import StreamingHttpResponse


# ───────────────────────────────────────────────
# SSE — Server-Sent Events
# ───────────────────────────────────────────────

async def sse_notifications(request) -> StreamingHttpResponse:
    """
    Стримит события меню и реакций конкретному пользователю.
    Подписывается на:
      - post_stream          (глобальные обновления меню)
      - canteen_{canteen_id} (обновления конкретной столовой, если известна)
    """
    channel_layer = get_channel_layer()

    # Определяем canteen_id из query-параметра (?canteen_id=1)
    canteen_id: str | None = request.GET.get("canteen_id")

    SUPPORTED_EVENTS = {"post.message", "comment.new", "reaction.updated"}

    async def event_stream():
        channel_name = await channel_layer.new_channel()

        # Подписываемся на глобальную группу
        await channel_layer.group_add("post_stream", channel_name)

        # Подписываемся на группу конкретной столовой
        if canteen_id:
            await channel_layer.group_add(f"canteen_{canteen_id}", channel_name)

        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        channel_layer.receive(channel_name),
                        timeout=30,
                    )
                    if message["type"] in SUPPORTED_EVENTS:
                        data = json.dumps(
                            {"event": message["type"], **message["data"]},
                            ensure_ascii=False,
                        )
                        yield f"data: {data}\n\n"

                except asyncio.TimeoutError:
                    # keepalive ping — браузер не закроет соединение
                    yield ": ping\n\n"

        finally:
            await channel_layer.group_discard("post_stream", channel_name)
            if canteen_id:
                await channel_layer.group_discard(f"canteen_{canteen_id}", channel_name)

    return StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ───────────────────────────────────────────────
# Notifications ViewSet
# ───────────────────────────────────────────────

class NotificationViewSet(ViewSet):
    """
    Эндпоинты для работы с уведомлениями текущего пользователя.

    GET  /notifications/count/  — количество непрочитанных
    GET  /notifications/list/   — список с пагинацией
    POST /notifications/read/   — пометить все как прочитанные
    POST /notifications/read-one/{id}/ — пометить одно как прочитанное
    """

    permission_classes = (IsAuthenticated,)

    # ── GET /count/ ────────────────────────────────────────────────────────

    @action(methods=("GET",), detail=False, url_path="count", url_name="count")
    def get_count(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        unread_count: int = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()
        return DRFResponse({"unread_count": unread_count}, status=HTTP_200_OK)

    # ── GET /list/ ─────────────────────────────────────────────────────────

    @action(methods=("GET",), detail=False, url_path="list", url_name="list")
    def get_list(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        notifications = (
            Notification.objects.filter(recipient=request.user)
            # comment → author, dish, daily_menu → canteen → school
            .select_related(
                "comment__author",
                "comment__dish",
                "comment__daily_menu__canteen__school",
            )
            .order_by("-created_at")
        )

        paginator = PageNumberPagination()
        paginator.page_size = 20
        # ↓ передаём инстанс request, а не класс DRFRequest
        page = paginator.paginate_queryset(notifications, request)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # ── POST /read/ ────────────────────────────────────────────────────────

    @action(methods=("POST",), detail=False, url_path="read", url_name="read")
    def mark_all_read(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """Пометить все непрочитанные уведомления как прочитанные."""
        updated: int = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        return DRFResponse({"marked_read": updated}, status=HTTP_200_OK)

    # ── POST /read-one/{id}/ ───────────────────────────────────────────────

    @action(
        methods=("POST",),
        detail=True,                    # /notifications/{id}/read-one/
        url_path="read-one",
        url_name="read-one",
    )
    def mark_one_read(
        self,
        request: DRFRequest,
        pk: int | None = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """Пометить одно уведомление как прочитанное."""
        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user,   # защита: чужое уведомление → 404
        )
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        return DRFResponse({"marked_read": True}, status=HTTP_200_OK)