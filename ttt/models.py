from django.db import models
import uuid
import json

# Create your models here.
class GameRoom(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting for players'),
        ('active', 'Active'),
        ('finished', 'Game finished'),
    ]

    room_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    player_x = models.CharField(max_length=100, blank=True, null=True)
    player_o = models.CharField(max_length=100, blank=True, null=True)
    player_x_name=models.CharField(max_length=100,default='Player X', null=True )
    player_o_name=models.CharField(max_length=100,default='Player O', null=True )
    board_state = models.TextField(default='["", "", "", "", "", "", "", "", ""]')  # Store the board as a JSON string
    current_turn = models.CharField(max_length=1, default='X')  # 'X' or 'O'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    winner = models.CharField(max_length=1, blank=True, null=True)  # 'X', 'O', or 'Draw'
    created_at = models.DateTimeField(auto_now_add=True)

    def get_board(self):
        return json.loads(self.board_state)
    def set_board(self, board):
        self.board_state = json.dumps(board)
    def __str__(self):
        return f"GameRoom {self.room_id} - Status: {self.status}"