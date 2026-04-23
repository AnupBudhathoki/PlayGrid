import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Game, Player
from .game_logic import create_initial_state, process_roll, move_piece, state_to_client


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'game_{self.room_code}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        # Notify others
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_left',
                'message': 'A player disconnected.',
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'player_join':
            await self._handle_player_join(data)
        elif action == 'start_game':
            await self._handle_start_game(data)
        elif action == 'roll_dice':
            await self._handle_roll_dice(data)
        elif action == 'move_piece':
            await self._handle_move_piece(data)
        elif action == 'get_state':
            await self._handle_get_state(data)

    # ── Handlers ─────────────────────────────────────────────────────────

    async def _handle_player_join(self, data):
        player_id = data.get('player_id')
        if player_id:
            await self._update_channel_name(player_id, self.channel_name)

        players = await self._get_players_list()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'lobby_update',
                'players': players,
            }
        )

    async def _handle_start_game(self, data):
        game = await self._get_game()
        players = await self._get_players_list()
        colors = [p['color'] for p in players]

        if len(colors) < 2:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Need at least 2 players to start.',
            }))
            return

        state = create_initial_state(colors)
        await self._save_game_state(state)
        await self._set_game_status('playing')

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_started',
                'state': state_to_client(state),
                'players': players,
            }
        )

    async def _handle_roll_dice(self, data):
        color = data.get('color')
        game = await self._get_game()
        state = game.game_state

        if state.get('current_turn_color') != color:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Not your turn!',
            }))
            return

        new_state, dice_value, movable = process_roll(state, color)
        await self._save_game_state(new_state)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'dice_rolled',
                'color': color,
                'diceValue': dice_value,
                'state': state_to_client(new_state),
            }
        )

    async def _handle_move_piece(self, data):
        color = data.get('color')
        piece_index = data.get('piece_index')
        game = await self._get_game()
        state = game.game_state
        dice_value = state.get('dice_value', 0)

        new_state, events = move_piece(state, color, piece_index, dice_value)
        await self._save_game_state(new_state)

        if new_state.get('winner'):
            await self._set_game_status('finished')

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'piece_moved',
                'color': color,
                'pieceIndex': piece_index,
                'events': events,
                'state': state_to_client(new_state),
            }
        )

    async def _handle_get_state(self, data):
        game = await self._get_game()
        if game.game_state:
            players = await self._get_players_list()
            await self.send(text_data=json.dumps({
                'type': 'game_started',  # Triggers full UI init on client
                'state': state_to_client(game.game_state),
                'players': players,
            }))

    # ── Group message handlers ───────────────────────────────────────────

    async def lobby_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'lobby_update',
            'players': event['players'],
        }))

    async def game_started(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_started',
            'state': event['state'],
            'players': event['players'],
        }))

    async def dice_rolled(self, event):
        await self.send(text_data=json.dumps({
            'type': 'dice_rolled',
            'color': event['color'],
            'diceValue': event['diceValue'],
            'state': event['state'],
        }))

    async def piece_moved(self, event):
        await self.send(text_data=json.dumps({
            'type': 'piece_moved',
            'color': event['color'],
            'pieceIndex': event['pieceIndex'],
            'events': event['events'],
            'state': event['state'],
        }))

    async def player_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_left',
            'message': event['message'],
        }))

    # ── DB helpers ───────────────────────────────────────────────────────

    @database_sync_to_async
    def _get_game(self):
        return Game.objects.get(room_code=self.room_code)

    @database_sync_to_async
    def _get_players_list(self):
        game = Game.objects.get(room_code=self.room_code)
        return list(game.players.values('id', 'name', 'color', 'is_host'))

    @database_sync_to_async
    def _save_game_state(self, state):
        Game.objects.filter(room_code=self.room_code).update(game_state=state)

    @database_sync_to_async
    def _set_game_status(self, status):
        Game.objects.filter(room_code=self.room_code).update(status=status)

    @database_sync_to_async
    def _update_channel_name(self, player_id, channel_name):
        Player.objects.filter(id=player_id).update(channel_name=channel_name)
