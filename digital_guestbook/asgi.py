# digital_guestbook/asgi.py
import os
import django
from dotenv import load_dotenv

load_dotenv()

environment = os.getenv('ENVIRONMENT', 'development')

if environment == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digital_guestbook.settings.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digital_guestbook.settings.dev')

django.setup() 

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from guestbook.routing import websocket_urlpatterns

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})