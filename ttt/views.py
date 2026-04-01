from django.shortcuts import render, redirect, get_object_or_404
from .models import GameRoom

def ensure_session(request):
    if not request.session.session_key:
        request.session.create()
    if not request.session.get('has_session'):
        request.session['has_session'] = True

def home(request):
    ensure_session(request)
    rooms = GameRoom.objects.filter(status__in=['waiting', 'active']).order_by('-created_at')[:10]
    return render(request, 'home.html', {
        'recent_rooms': rooms,
        'player_name': request.session.get('player_name', ''),
    })

def set_name(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()[:30]
        if name:
            request.session['player_name'] = name
    return redirect('home')

def create_room(request):
    if request.method == 'POST':
        ensure_session(request)
        player_name = request.session.get('player_name', 'Player X')
        room = GameRoom.objects.create(
            player_x=request.session.session_key,
            player_x_name=player_name,
        )
        return redirect('tictactoe_game', room_id=room.room_id)
    return redirect('home')

def join_room(request):
    if request.method == 'POST':
        room_code = request.POST.get('room_code', '').strip()
        try:
            room = GameRoom.objects.get(room_code=room_code)
            return redirect('tictactoe_game', room_id=room.room_id)
        except (GameRoom.DoesNotExist, ValueError, TypeError):
            rooms = GameRoom.objects.filter(status__in=['waiting', 'active']).order_by('-created_at')[:10]
            return render(request, 'home.html', {
                'error': 'Room not found. Check the 5-digit code and try again.',
                'recent_rooms': rooms,
                'player_name': request.session.get('player_name', ''),
            })
    return redirect('home')

def tictactoe_game(request, room_id):
    room = get_object_or_404(GameRoom, room_id=room_id)

    ensure_session(request)
    session_id = request.session.session_key

    player_role = None

    if room.player_x == session_id:
        player_role = 'X'
    elif room.player_o == session_id:
        player_role = 'O'
    elif not room.player_o and room.status == 'waiting' and room.player_x != session_id:
        # second player joining
        player_name = request.session.get('player_name', 'Player O')
        room.player_o = session_id
        room.player_o_name = player_name
        room.status = 'active'
        room.save()
        player_role = 'O'

    return render(request, 'ttt.html', {
        'room': room,
        'player_role': player_role,
        'room_id': str(room_id),
        'room_code': room.room_code,
    })
def tictactoe_mode(request):
    return render(request, 'ttt.html')

def tictactoe_offline(request):
    return render(request, 'ttt_offline.html')
# # Create your views here.

# def ttt(request):
#     return render(request, 'ttt.html')

# def ttt_offline(request):
#     return render(request, 'ttt_offline.html')