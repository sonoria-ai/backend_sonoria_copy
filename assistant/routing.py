from django.urls import re_path
from . import websocket_handler

websocket_urlpatterns = [
    re_path(r'assistant/media-stream$', websocket_handler.MediaStreamConsumer.as_asgi()),
]
