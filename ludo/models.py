import uuid
from django.db import models


class Game(models.Model):
    MODE_CHOICES = [
        ('local', 'Local'),
        ('online', 'Online'),
    ]
    STATUS_CHOICES = [
        ('waiting', 'Waiting for players'),
        ('playing', 'In progress'),
        ('finished', 'Finished'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_code = models.CharField(max_length=8, unique=True, blank=True, null=True)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='online')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    current_turn = models.IntegerField(default=0)  # index into players
    game_state = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.room_code:
            self.room_code = uuid.uuid4().hex[:6].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Game {self.room_code} ({self.get_status_display()})"


class Player(models.Model):
    COLOR_CHOICES = [
        ('red', 'Red'),
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('blue', 'Blue'),
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=10, choices=COLOR_CHOICES)
    is_host = models.BooleanField(default=False)
    channel_name = models.CharField(max_length=255, blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('game', 'color')

    def __str__(self):
        return f"{self.name} ({self.color}) in {self.game.room_code}"
