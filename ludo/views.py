from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Game, Player
from .game_logic import create_initial_state


def ludo_home(request):
    """Landing page with Play Local and Play Online options."""
    return render(request, 'ludo_home.html')


def local_game(request):
    """Local multiplayer game page."""
    return render(request, 'local_game.html')


def create_room(request):
    """Create a new online game room and redirect to lobby."""
    if request.method == 'POST':
        player_name = request.POST.get('player_name', 'Player 1')
        game = Game.objects.create(mode='online', status='waiting')
        player = Player.objects.create(
            game=game,
            name=player_name,
            color='red',
            is_host=True,
        )
        request.session['player_id'] = player.id
        request.session['game_id'] = str(game.id)
        return redirect('lobby', room_code=game.room_code)
    return redirect('ludo_home')


def join_room(request):
    """Join an existing game room."""
    if request.method == 'POST':
        room_code = request.POST.get('room_code', '').strip().upper()
        player_name = request.POST.get('player_name', 'Player')

        try:
            game = Game.objects.get(room_code=room_code)
        except Game.DoesNotExist:
            return render(request, 'ludo_home.html', {
                'error': f'Room "{room_code}" not found.',
                'show_join': True,
            })

        if game.status != 'waiting':
            return render(request, 'ludo_home.html', {
                'error': 'This game has already started.',
                'show_join': True,
            })

        current_players = game.players.count()
        if current_players >= 4:
            return render(request, 'ludo_home.html', {
                'error': 'Room is full (4 players max).',
                'show_join': True,
            })

        # Assign next available color
        taken_colors = set(game.players.values_list('color', flat=True))
        available_colors = ['red', 'green', 'yellow', 'blue']
        color = next(c for c in available_colors if c not in taken_colors)

        player = Player.objects.create(
            game=game,
            name=player_name,
            color=color,
        )
        request.session['player_id'] = player.id
        request.session['game_id'] = str(game.id)
        return redirect('lobby', room_code=game.room_code)

    return redirect('ludo_home')


def lobby(request, room_code):
    """Waiting room before online game starts."""
    game = get_object_or_404(Game, room_code=room_code)
    player_id = request.session.get('player_id')
    player = None
    if player_id:
        try:
            player = Player.objects.get(id=player_id, game=game)
        except Player.DoesNotExist:
            player = None

    return render(request, 'lobby.html', {
        'game': game,
        'player': player,
        'players': game.players.all(),
        'room_code': room_code,
    })


def online_game(request, room_code):
    """Online multiplayer game board."""
    game = get_object_or_404(Game, room_code=room_code)
    player_id = request.session.get('player_id')
    player = None
    if player_id:
        try:
            player = Player.objects.get(id=player_id, game=game)
        except Player.DoesNotExist:
            player = None

    return render(request, 'online_game.html', {
        'game': game,
        'player': player,
        'room_code': room_code,
    })
