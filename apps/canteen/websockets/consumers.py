# Python Modules
import json
from typing import Any

# Channel Modules
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

# Project Modules
from apps.canteen.models import Comment, Dish, DailyMenu


class CommentConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer для комментариев.
    Поддерживает два режима:
      ws://…/ws/comments/dish/{dish_id}/
      ws://…/ws/comments/menu/{menu_id}/
    """

    # ── connect ───────────────────────────────────────────────────────────

    async def connect(self) -> None:
        user = self.scope["user"]

        # Закрываем соединение если пользователь не аутентифицирован
        if not user.is_authenticated:
            await self.close(code=4001)
            return

        url_kwargs: dict[str, Any] = self.scope["url_route"]["kwargs"]
        self.dish_id: int | None = url_kwargs.get("dish_id")
        self.menu_id: int | None = url_kwargs.get("menu_id")

        # Формируем имя группы в зависимости от типа объекта
        if self.dish_id:
            self.group_name = f"comments_dish_{self.dish_id}"
        elif self.menu_id:
            self.group_name = f"comments_menu_{self.menu_id}"
        else:
            await self.close(code=4002)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Отправить историю комментариев сразу после подключения
        old_comments = await self.get_comments()
        for comment in old_comments:
            await self.send(text_data=json.dumps({
                "type":       "comment.history",
                "author":     comment["author__email"],
                "text":       comment["text"],
                "created_at": comment["created_at__isoformat"]
                              if "created_at__isoformat" in comment
                              else str(comment.get("created_at", "")),
            }, ensure_ascii=False))

    # ── disconnect ────────────────────────────────────────────────────────

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    # ── receive ───────────────────────────────────────────────────────────

    async def receive(self, text_data: str | None = None) -> None:
        user = self.scope["user"]

        # Двойная проверка — токен мог протухнуть после connect
        if not user.is_authenticated:
            await self.close(code=4001)
            return

        try:
            data: dict = json.loads(text_data or "{}")
            text: str = data["text"].strip()
            if not text:
                raise ValueError("Empty comment")
        except (KeyError, ValueError) as e:
            await self.send(text_data=json.dumps({
                "type":  "error",
                "error": str(e),
            }))
            return

        # Сохраняем в БД
        comment = await self.save_comment(user, text)

        # Рассылаем всем в группе
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type":       "comment.new",   # → метод comment_new
                "comment_id": comment.id,
                "author":     user.email,
                "text":       text,
            },
        )

    # ── handlers ─────────────────────────────────────────────────────────

    async def comment_new(self, event: dict) -> None:
        """Channels вызывает этот метод когда приходит событие comment.new"""
        await self.send(text_data=json.dumps({
            "type":       "comment.new",
            "comment_id": event["comment_id"],
            "author":     event["author"],
            "text":       event["text"],
        }, ensure_ascii=False))

    # ── ORM (sync_to_async) ───────────────────────────────────────────────

    @sync_to_async
    def get_comments(self) -> list[dict]:
        qs = Comment.objects.select_related("author")

        if self.dish_id:
            qs = qs.filter(dish_id=self.dish_id)
        elif self.menu_id:
            qs = qs.filter(daily_menu_id=self.menu_id)

        return list(
            qs.order_by("created_at")
            .values("author__email", "text", "created_at")
        )

    @sync_to_async
    def save_comment(self, user, text: str) -> Comment:
        """
        Создаёт Comment и возвращает инстанс.
        author — объект User, не email.
        """
        kwargs = {"author": user, "text": text}

        if self.dish_id:
            kwargs["dish_id"] = self.dish_id
        elif self.menu_id:
            kwargs["daily_menu_id"] = self.menu_id

        return Comment.objects.create(**kwargs)