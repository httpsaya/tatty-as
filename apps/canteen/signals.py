# Python Modules
from typing import Any

# Django Modules
from django.db.models.signals import m2m_changed
from django.db.models import Q
from django.dispatch import receiver

# Project Modules
from apps.canteen.models import DailyMenu

# Channel Modules
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@receiver(m2m_changed, sender=DailyMenu.dishes.through)
def menu_dishes_changed(sender, instance, action, **kwargs: dict[str, Any]):
    if action not in ["post_add", "post_remove", "post_clear"]:
        return

    channel_layer = get_channel_layer()

    message_text = f"Меню на {instance.date.strftime('%d.%m')} в столовой «{instance.canteen.name}» обновлено!"

    payload = {
        "event": "daily_menu_created",
        "message": message_text,
        "canteen": {"id": instance.canteen.id, "name": instance.canteen.name},
        "date": instance.date.isoformat(),
        "dishes": [
            {"id": d.id, "name": d.name, "price": str(d.price)}
            for d in instance.dishes.all()
        ],
    }

    # ── 1. SSE ──
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f'canteen_{instance.canteen.id}',
            {'type': 'dailymenu.message', 'data': payload}
        )

    # ── 2. Уведомления в БД ──
    try:
        from apps.notifications.models import Notification
        from apps.auths.models import CustomUser

        users = CustomUser.objects.filter(
            Q(school=instance.canteen.school) | Q(is_superuser=True),
            is_active=True
        )

        Notification.objects.bulk_create([
            Notification(
                user=user,
                type='post',
                title="Обновление меню",
                message=message_text,
                is_read=False,
                related_object_id=instance.id,
                related_object_type="dailymenu",
            )
            for user in users
        ], ignore_conflicts=True)

    except Exception as e:
        print(f"[SIGNAL] Ошибка создания уведомлений: {e}")