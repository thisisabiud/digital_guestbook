#routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/messages/(?P<event_id>\d+)/$', consumers.GuestbookConsumer.as_asgi()),
]