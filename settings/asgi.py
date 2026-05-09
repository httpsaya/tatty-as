# settings/asgi.py
import os
import sys

# Сначала настройка окружения - это должно быть ПЕРВЫМ!
from settings.conf import ENV_ID, ENV_POSSIBLE_OPTIONS

assert ENV_ID in ENV_POSSIBLE_OPTIONS, f"Set correct DJANGORLAR_ENV_ID env var. Possible options: {ENV_POSSIBLE_OPTIONS}"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'settings.env.{ENV_ID}')

# Теперь инициализируем Django
from django.core.asgi import get_asgi_application

# ЭТО ВАЖНО: вызываем get_asgi_application() до импорта любых других модулей
django_asgi_app = get_asgi_application()

# Теперь можно импортировать остальное
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.canteen.websockets.routers import ws_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(ws_urlpatterns)
    ),
})