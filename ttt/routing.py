from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/ttt/(?P<room_id>[0-9a-f-]+)/$', consumers.TicTacToeConsumer.as_asgi()),
]