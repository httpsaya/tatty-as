# Python Modules
from typing import Any

# Django Modules
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

# Project Modules
from apps.canteen.models import (
    Canteen,
    DailyMenu,
    Dish,
    Comment,
    DishReaction,
    MenuReaction,
)
from apps.notifications.models import Notification  # вынеси в отдельное приложение

# Channel Modules
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


# ───────────────────────────────────────────────
# helpers
# ───────────────────────────────────────────────

def _send_to_group(group: str, event_type: str, data: dict) -> None:
    """Отправить сообщение в WebSocket-группу."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": event_type,   # consumers должен иметь метод с таким именем
            "data": data,
        },
    )


# ───────────────────────────────────────────────
# DailyMenu → WebSocket broadcast
# ───────────────────────────────────────────────

@receiver(post_save, sender=DailyMenu)
def notify_daily_menu(
    sender,
    instance: DailyMenu,
    created: bool,
    **kwargs: dict[str, Any],
) -> None:
    """Оповестить всех подключённых клиентов об изменении меню."""
    payload = {
        "dailymenu_id": instance.id,
        "canteen":      instance.canteen.name,
        "date":         instance.date.isoformat(),
        "school":       instance.canteen.school.name,
        "created_at":   instance.created_at.isoformat(),
        "is_new":       created,
        "message": (
            f"Меню столовой «{instance.canteen.name}» "
            f"{'создано' if created else 'обновлено'}!"
        ),
    }
    _send_to_group("post_stream", "post.message", payload)


# ───────────────────────────────────────────────
# Comment → Notification + WebSocket
# ───────────────────────────────────────────────

@receiver(post_save, sender=Comment)
def on_comment_created(
    sender,
    instance: Comment,
    created: bool,
    **kwargs: dict[str, Any],
) -> None:
    """
    При создании нового комментария:
    1. Создать Notification для владельца блюда / меню (если это не сам автор).
    2. Отправить событие в WebSocket-группу столовой.
    """
    if not created:
        return

    # ── 1. Определяем получателя уведомления ──────────────────────────────
    # Комментарий привязан либо к Dish, либо к DailyMenu (см. модель Comment)
    canteen = None

    if instance.dish:
        # Уведомляем администратора столовой — у School есть canteen (OneToOne)
        canteen = instance.dish.category  # доходим до столовой через меню
        """
        Получатель = тот, кто управляет столовой; если такой логики нет,
        можно пропустить создание Notification и оставить только WS.
        """
        recipient = _resolve_canteen_admin(instance.dish)
    elif instance.daily_menu:
        canteen = instance.daily_menu.canteen
        recipient = _resolve_canteen_admin_from_canteen(canteen)
    else:
        return  # Comment.clean() не допускает такого, но на всякий случай

    # Не уведомляем, если автор комментария == получатель уведомления
    if recipient and instance.author != recipient:
        Notification.objects.create(
            recipient=recipient,
            comment=instance,
        )

    # ── 2. WebSocket: транслируем новый комментарий в группу столовой ──────
    if canteen:
        _send_to_group(
            f"canteen_{canteen.id}",   # отдельная группа на каждую столовую
            "comment.new",
            {
                "comment_id": instance.id,
                "author":     str(instance.author),
                "text":       instance.text,
                "dish_id":    instance.dish_id,
                "menu_id":    instance.daily_menu_id,
                "created_at": instance.created_at.isoformat(),
            },
        )


# ───────────────────────────────────────────────
# DishReaction / MenuReaction → WebSocket counter
# ───────────────────────────────────────────────

@receiver(post_save, sender=DishReaction)
def on_dish_reaction(
    sender,
    instance: DishReaction,
    created: bool,
    **kwargs: dict[str, Any],
) -> None:
    """Транслировать обновлённые счётчики реакций на блюдо."""
    _broadcast_dish_reactions(instance.dish)


@receiver(post_save, sender=MenuReaction)
def on_menu_reaction(
    sender,
    instance: MenuReaction,
    created: bool,
    **kwargs: dict[str, Any],
) -> None:
    """Транслировать обновлённые счётчики реакций на меню."""
    _broadcast_menu_reactions(instance.daily_menu)


# ───────────────────────────────────────────────
# private helpers
# ───────────────────────────────────────────────

def _broadcast_dish_reactions(dish: Dish) -> None:
    from django.db.models import Count
    counts = (
        DishReaction.objects
        .filter(dish=dish)
        .values("reaction_type__emoji", "reaction_type__label")
        .annotate(count=Count("id"))
    )
    _send_to_group(
        "post_stream",
        "reaction.updated",
        {
            "target":   "dish",
            "dish_id":  dish.id,
            "reactions": list(counts),
        },
    )


def _broadcast_menu_reactions(menu: DailyMenu) -> None:
    from django.db.models import Count
    counts = (
        MenuReaction.objects
        .filter(daily_menu=menu)
        .values("reaction_type__emoji", "reaction_type__label")
        .annotate(count=Count("id"))
    )
    _send_to_group(
        "post_stream",
        "reaction.updated",
        {
            "target":   "menu",
            "menu_id":  menu.id,
            "reactions": list(counts),
        },
    )


def _resolve_canteen_admin(dish: Dish):
    """
    Заглушка: верни пользователя, который управляет столовой этого блюда.
    Реализуй в зависимости от своей модели пользователей.
    """
    return None


def _resolve_canteen_admin_from_canteen(canteen: Canteen):
    """То же самое, но принимает Canteen напрямую."""
    return None