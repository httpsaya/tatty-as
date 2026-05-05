# Django modules
import os
from django.core.asgi import get_asgi_application

# Channel Modules
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Project Modules
from apps.canteen.websockets.routers import ws_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')

# application = get_asgi_application()
application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(ws_urlpatterns)
    ),
})