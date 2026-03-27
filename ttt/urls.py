from django.contrib import admin
from django.urls import path

from .views import *

# urlpatterns = [
#     path('',home, name='home', ),
#     path('ttt', ttt, name='ttt'),
#     path('ttt_offline', ttt_offline, name='ttt_offline'),
#     path('set-name/', set_name, name='set_name'),
#     path('create-room/', create_room, name='create_room'),
#     path('join-room/', join_room, name='join_room'),
#     path('ttt/mode/', tictactoe_mode, name='tictactoe_mode'),
#     path('ttt/offline/', tictactoe_offline, name='tictactoe_offline'),
#     path('ttt/<uuid:room_id>/', tictactoe_game, name='tictactoe_game'),
# ]

urlpatterns = [
    path('', home, name='home'),
    path('set-name/', set_name, name='set_name'),
    path('create-room/', create_room, name='create_room'),
    path('join-room/', join_room, name='join_room'),
    path('ttt/offline/', tictactoe_offline, name='tictactoe_offline'),
    path('ttt/<uuid:room_id>/', tictactoe_game, name='tictactoe_game'),
]