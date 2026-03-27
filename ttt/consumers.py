import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import GameRoom

class TicTacToeConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'ttt_{self.room_id}'

        # join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # send current room state to the player who just connected
        room = await self.get_room()
        if room:
            await self.send(text_data=json.dumps({
                'type': 'room_state',
                'board': room.get_board(),
                'current_turn': room.current_turn,
                'status': room.status,
                'player_x_name': room.player_x_name,
                'player_o_name': room.player_o_name,
                'winner': room.winner,
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')

        if msg_type == 'make_move':
            await self.handle_move(data)
        elif msg_type == 'reset_game':
            await self.handle_reset()
        elif msg_type == 'chat_message':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': data.get('message', ''),
                    'sender': data.get('sender', 'Unknown'),
                }
            )

    async def handle_move(self, data):
        index = data.get('index')
        player = data.get('player')
        room = await self.get_room()

        if not room or room.status != 'active':
            return
        
        board = room.get_board()

        # validate move
        if board[index] != '' or room.current_turn != player:
            return

        # make the move
        board[index] = player
        winner = check_winner(board)
        is_draw = all(cell != '' for cell in board) and not winner

        room.set_board(board)

        if winner:
            room.winner = winner
            room.status = 'finished'
        elif is_draw:
            room.winner = 'D'
            room.status = 'finished'
        else:
            room.current_turn = 'O' if player == 'X' else 'X'

        await self.save_room(room)

        # broadcast updated state to both players
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_update',
                'board': board,
                'current_turn': room.current_turn,
                'status': room.status,
                'winner': room.winner,
                'last_move': index,
            }
        )

    async def handle_reset(self):
        room = await self.get_room()
        if not room:
            return

        room.set_board([""] * 9)
        room.current_turn = 'X'
        room.status = 'active'
        room.winner = ''
        await self.save_room(room)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_update',
                'board': [""] * 9,
                'current_turn': 'X',
                'status': 'active',
                'winner': '',
                'last_move': None,
            }
        )

    # these are called when group_send fires
    async def game_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_update',
            'board': event['board'],
            'current_turn': event['current_turn'],
            'status': event['status'],
            'winner': event['winner'],
            'last_move': event.get('last_move'),
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender': event['sender'],
        }))

    @database_sync_to_async
    def get_room(self):
        try:
            return GameRoom.objects.get(room_id=self.room_id)
        except GameRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def save_room(self, room):
        room.save()


def check_winner(board):
    wins = [
        (0,1,2),(3,4,5),(6,7,8),  # rows
        (0,3,6),(1,4,7),(2,5,8),  # columns
        (0,4,8),(2,4,6)           # diagonals
    ]
    for a, b, c in wins:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None