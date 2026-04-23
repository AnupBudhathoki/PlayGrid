"""
Ludo Game Logic Engine
Pure-Python implementation of all Ludo rules.
This is used server-side for online games and mirrored in JS for local play.
"""

import random
import copy

# ── Board Constants ──────────────────────────────────────────────────────────

TOTAL_TRACK_SQUARES = 52
HOME_COLUMN_LENGTH = 6
PIECES_PER_PLAYER = 4

# Each player's starting position on the common track (where they enter after rolling 6)
PLAYER_START_POSITIONS = {
    'red': 0,
    'green': 13,
    'yellow': 26,
    'blue': 39,
}

# Safe squares on the common track (0-indexed)
SAFE_SQUARES = {0, 8, 13, 21, 26, 34, 39, 47}

# Colors in turn order
TURN_ORDER = ['red', 'green', 'yellow', 'blue']


def create_initial_state(player_colors):
    """Create the initial game state for given player colors."""
    state = {
        'players': {},
        'current_turn_color': player_colors[0],
        'dice_value': None,
        'consecutive_sixes': 0,
        'winner': None,
        'turn_order': player_colors,
        'phase': 'roll',  # 'roll' or 'move'
        'movable_pieces': [],
        'game_log': [],
    }
    for color in player_colors:
        state['players'][color] = {
            'pieces': [
                {'position': -1, 'home_progress': 0, 'finished': False}
                for _ in range(PIECES_PER_PLAYER)
            ],
            'finished_count': 0,
            'has_started': False,
            'rolls_count': 0,
        }
    return state


def roll_dice():
    """Roll a single die, return 1-6."""
    return random.randint(1, 6)


def get_movable_pieces(state, color, dice_value):
    """
    Return list of piece indices that can legally move with the given dice roll.
    """
    player = state['players'][color]
    movable = []

    for i, piece in enumerate(player['pieces']):
        if piece['finished']:
            continue

        # Piece is in base — needs a 6 or 1 to come out (house rule)
        if piece['position'] == -1:
            if dice_value == 6 or dice_value == 1:
                movable.append(i)
            continue

        # Piece is on the home column
        if piece['home_progress'] > 0:
            new_progress = piece['home_progress'] + dice_value
            if new_progress <= HOME_COLUMN_LENGTH:
                movable.append(i)
            continue

        # Piece is on the common track
        start_pos = PLAYER_START_POSITIONS[color]
        # Calculate how far this piece has traveled from its start
        if piece['position'] >= start_pos:
            distance_traveled = piece['position'] - start_pos
        else:
            distance_traveled = (TOTAL_TRACK_SQUARES - start_pos) + piece['position']

        new_distance = distance_traveled + dice_value

        if new_distance < TOTAL_TRACK_SQUARES:
            # Still on the common track
            movable.append(i)
        elif new_distance < TOTAL_TRACK_SQUARES + HOME_COLUMN_LENGTH:
            # Entering home column
            movable.append(i)
        elif new_distance == TOTAL_TRACK_SQUARES + HOME_COLUMN_LENGTH:
            # Exact roll to finish
            movable.append(i)
        # else: overshot — can't move

    return movable


def move_piece(state, color, piece_index, dice_value):
    """
    Execute a move. Returns (new_state, events) where events is a list of
    strings describing what happened (e.g. 'capture', 'finish', 'enter').
    """
    state = copy.deepcopy(state)
    player = state['players'][color]
    piece = player['pieces'][piece_index]
    events = []

    bonus_turn = False

    if piece['position'] == -1:
        # Moving out of base
        piece['position'] = PLAYER_START_POSITIONS[color]
        piece['home_progress'] = 0
        player['has_started'] = True
        events.append('enter')
        # Check for capture at start position
        capture_event = _check_capture(state, color, piece['position'])
        if capture_event:
            events.append('capture')
            bonus_turn = True
    elif piece['home_progress'] > 0:
        # Moving on the home column
        piece['home_progress'] += dice_value
        if piece['home_progress'] == HOME_COLUMN_LENGTH:
            piece['finished'] = True
            player['finished_count'] += 1
            events.append('finish')
            bonus_turn = True
            if player['finished_count'] == PIECES_PER_PLAYER:
                state['winner'] = color
                events.append('win')
    else:
        # Moving on the common track
        start_pos = PLAYER_START_POSITIONS[color]
        if piece['position'] >= start_pos:
            distance_traveled = piece['position'] - start_pos
        else:
            distance_traveled = (TOTAL_TRACK_SQUARES - start_pos) + piece['position']

        new_distance = distance_traveled + dice_value

        if new_distance < TOTAL_TRACK_SQUARES:
            # Still on common track
            new_position = (start_pos + new_distance) % TOTAL_TRACK_SQUARES
            piece['position'] = new_position
            # Check for capture
            capture_event = _check_capture(state, color, new_position)
            if capture_event:
                events.append('capture')
                bonus_turn = True
        else:
            # Entering home column
            home_progress = new_distance - TOTAL_TRACK_SQUARES + 1
            piece['position'] = -2  # special: on home column
            piece['home_progress'] = home_progress
            if home_progress == HOME_COLUMN_LENGTH:
                piece['finished'] = True
                player['finished_count'] += 1
                events.append('finish')
                bonus_turn = True
                if player['finished_count'] == PIECES_PER_PLAYER:
                    state['winner'] = color
                    events.append('win')
            else:
                events.append('home_column')

    # Handle turn progression
    if dice_value == 6:
        state['consecutive_sixes'] += 1
        if state['consecutive_sixes'] >= 3:
            # Three sixes in a row — lose turn
            events.append('three_sixes')
            state['consecutive_sixes'] = 0
            _advance_turn(state)
        else:
            bonus_turn = True
    else:
        state['consecutive_sixes'] = 0

    if not bonus_turn and dice_value != 6:
        _advance_turn(state)
    elif bonus_turn or dice_value == 6:
        # Player gets another roll (unless three sixes already handled)
        if 'three_sixes' not in events:
            state['phase'] = 'roll'

    if 'win' not in events:
        state['phase'] = 'roll'

    state['dice_value'] = dice_value
    state['movable_pieces'] = []

    return state, events


def process_roll(state, color):
    """
    Process a dice roll for the given color.
    Returns (new_state, dice_value, movable_pieces).
    """
    state = copy.deepcopy(state)

    if state['current_turn_color'] != color or state.get('phase', 'roll') != 'roll':
        return state, 0, []

    dice_value = roll_dice()
    
    player = state['players'].get(color, {})
    if not player.get('has_started', False):
        player['rolls_count'] = player.get('rolls_count', 0) + 1
        if player['rolls_count'] >= 10:
            dice_value = 1
            
    state['dice_value'] = dice_value

    movable = get_movable_pieces(state, color, dice_value)
    state['movable_pieces'] = movable

    if not movable:
        # No valid moves — skip turn
        if dice_value == 6:
            state['consecutive_sixes'] += 1
            if state['consecutive_sixes'] >= 3:
                state['consecutive_sixes'] = 0
                _advance_turn(state)
            else:
                state['phase'] = 'roll'  # roll again
        else:
            state['consecutive_sixes'] = 0
            _advance_turn(state)
    else:
        state['phase'] = 'move'

    return state, dice_value, movable


def _check_capture(state, moving_color, position):
    """Check if landing on `position` captures an opponent. Returns True if captured."""
    if position in SAFE_SQUARES:
        return False

    captured = False
    for opp_color, opp_data in state['players'].items():
        if opp_color == moving_color:
            continue
        for piece in opp_data['pieces']:
            if piece['position'] == position and not piece['finished'] and piece['home_progress'] == 0:
                piece['position'] = -1  # send back to base
                captured = True

    return captured


def _advance_turn(state):
    """Move to the next player's turn."""
    turn_order = state['turn_order']
    current_color = state['current_turn_color']
    current_idx = turn_order.index(current_color)

    # Find next player that hasn't finished
    for i in range(1, len(turn_order) + 1):
        next_idx = (current_idx + i) % len(turn_order)
        next_color = turn_order[next_idx]
        if state['players'][next_color]['finished_count'] < PIECES_PER_PLAYER:
            state['current_turn_color'] = next_color
            state['phase'] = 'roll'
            state['consecutive_sixes'] = 0
            return

    # All players finished (shouldn't normally happen)
    state['phase'] = 'roll'


def state_to_client(state):
    """Convert game state to a JSON-safe dict for sending to clients."""
    return {
        'players': state['players'],
        'currentTurnColor': state['current_turn_color'],
        'diceValue': state['dice_value'],
        'phase': state['phase'],
        'movablePieces': state['movable_pieces'],
        'winner': state['winner'],
        'turnOrder': state['turn_order'],
    }
