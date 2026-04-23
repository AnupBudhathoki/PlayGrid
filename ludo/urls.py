from django.urls import path
from .views import *

urlpatterns = [
    path('', ludo_home, name='ludo_home'),
    path('play/local/', ludo_offline, name='ludo_offline'),
    path('play/create/', create_room, name='create_room'),
    path('play/join/', join_room, name='join_room'),
    path('play/lobby/<str:room_code>/', lobby, name='lobby'),
    path('play/online/<str:room_code>/', online_game, name='online_game'),
]
