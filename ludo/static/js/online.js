// online.js

document.addEventListener('DOMContentLoaded', () => {
    const roomCode = JSON.parse(document.getElementById('room-code').textContent);
    let myColor = "null";
    try {
        myColor = JSON.parse(document.getElementById('my-color').textContent);
    } catch (e) { }

    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const gameSocket = new WebSocket(
        wsScheme + '://' + window.location.host + '/ws/game/' + roomCode + '/'
    );

    const board = new LudoBoard('ludo-board');
    const statusEl = document.getElementById('game-status');
    const connStatusEl = document.getElementById('connection-status');
    const colors = ['red', 'green', 'yellow', 'blue'];

    // UI Elements
    const diceDisplays = {};
    const playerPanels = {};
    const nameDisplays = {};

    // Inject Avatars and Dice into corners
    const boardContainer = document.getElementById('board-container');
    boardContainer.style.position = 'relative'; // Anchor for the corner cards

    colors.forEach(c => {
        const baseEl = document.querySelector(`.base-${c}`);
        if (baseEl) {
            const cornerInfo = document.createElement('div');
            cornerInfo.className = `corner-player-info corner-${c}`;
            cornerInfo.id = `panel-${c}`;
            cornerInfo.style.display = 'none'; // Hidden until player joins

            const avatar = document.createElement('img');
            avatar.src = 'https://ui-avatars.com/api/?name=P&background=random&color=fff';
            avatar.className = `player-avatar border-${c}`;

            const nameEl = document.createElement('div');
            nameEl.className = 'fw-bold mb-1 text-white text-center';
            nameEl.style.fontSize = '0.8rem';
            nameEl.id = `name-${c}`;
            nameEl.textContent = 'Player';

            const dice = document.createElement('div');
            dice.className = 'corner-dice disabled';
            dice.id = `dice-${c}`;
            dice.textContent = '🎲';

            cornerInfo.appendChild(avatar);
            cornerInfo.appendChild(nameEl);
            cornerInfo.appendChild(dice);
            
            // Append to boardContainer (wrapper), NOT inside the board! 
            boardContainer.appendChild(cornerInfo);

            diceDisplays[c] = dice;
            playerPanels[c] = cornerInfo;
            nameDisplays[c] = nameEl;

            const rollAction = (e) => {
                e.stopPropagation();
                if (myColor === 'null') {
                    updateStatusEl("You are currently spectating (no player session). You cannot play.");
                    return;
                }
                if (myColor !== c) {
                    updateStatusEl("That is not your card! You are playing as " + myColor.toUpperCase() + ".");
                    return;
                }
                if (dice.classList.contains('disabled')) {
                    updateStatusEl("You cannot roll right now! Wait for your turn or click a piece to move.");
                    return;
                }
                
                dice.style.transform = 'scale(0.8)';
                setTimeout(() => dice.style.transform = '', 150);
                updateStatusEl("Rolling...");

                gameSocket.send(JSON.stringify({
                    'action': 'roll_dice',
                    'color': c
                }));
            };
            
            dice.addEventListener('click', rollAction);
            cornerInfo.addEventListener('click', rollAction);
            cornerInfo.style.cursor = 'pointer';
        }
    });

    board.draw();

    board.onPieceClick((clickedColor, pieceIndex) => {
        if (myColor && myColor !== 'null' && myColor === clickedColor) {
            gameSocket.send(JSON.stringify({
                'action': 'move_piece',
                'color': myColor,
                'piece_index': pieceIndex
            }));
        }
    });

    gameSocket.onopen = function (e) {
        connStatusEl.textContent = 'Connected';
        connStatusEl.className = 'badge bg-success mt-1';

        gameSocket.send(JSON.stringify({
            'action': 'get_state'
        }));
    };

    gameSocket.onclose = function (e) {
        connStatusEl.textContent = 'Disconnected';
        connStatusEl.className = 'badge bg-danger mt-1';
    };

    gameSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        if (data.type === 'game_started' || data.type === 'dice_rolled' || data.type === 'piece_moved') {
            handleStateUpdate(data.state, data.type === 'dice_rolled' ? data.diceValue : null, data.color, data.players);
        } else if (data.type === 'error') {
            statusEl.textContent = `Error: ${data.message}`;
            statusEl.className = 'alert alert-danger glass-card mt-3 text-center fw-600';
            setTimeout(() => {
                const s = data.state;
                if (s) {
                    if (s.winner) updateStatusEl(`MATCH FINISHED! ${s.winner} wins!`);
                    else updateStatusEl(s.phase === 'roll' ? `Waiting for ${s.currentTurnColor} to roll.` :
                        s.phase === 'move' ? `${s.currentTurnColor} must select a piece.` : s.phase);
                }
            }, 3000);
        }
    };

    function handleStateUpdate(state, diceVal, actionColor, playersList) {
        if (!state) return;

        // Show active players panels
        if (playersList) {
            playersList.forEach(p => {
                if (playerPanels[p.color]) {
                    playerPanels[p.color].style.display = 'flex';
                    nameDisplays[p.color].textContent = p.name;
                    // Optional: Update avatar initials
                    const img = playerPanels[p.color].querySelector('img');
                    img.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(p.name)}&background=random&color=fff`;
                }
            });
        }

        const boardPieces = {};
        if (state.players) {
            for (const [col, pData] of Object.entries(state.players)) {
                boardPieces[col] = pData.pieces.map(piece => {
                    if (piece.position === -1) return -1;
                    if (piece.home_progress > 0) return 99 + piece.home_progress;
                    return piece.position;
                });
            }
        }

        board.draw({ pieces: boardPieces });

        colors.forEach(c => {
            if (playerPanels[c]) playerPanels[c].classList.remove('active-turn');
            if (diceDisplays[c]) diceDisplays[c].classList.add('disabled');
        });

        if (playerPanels[state.currentTurnColor]) {
            playerPanels[state.currentTurnColor].classList.add('active-turn');
        }

        if (state.winner) {
            updateStatusEl(`MATCH FINISHED! ${state.winner} wins!`);
        } else if (state.phase === 'roll') {
            updateStatusEl(`Waiting for ${state.currentTurnColor} to roll.`);
            if (myColor === state.currentTurnColor) {
                diceDisplays[myColor].classList.remove('disabled');
            }
        } else if (state.phase === 'move') {
            updateStatusEl(`${state.currentTurnColor} rolled a ${state.diceValue}. Click a piece to move.`);
        }

        // Handle dice roll animation
        if (diceVal && actionColor) {
            const dice = diceDisplays[actionColor];
            dice.textContent = getDiceChar(diceVal);
            dice.style.animation = 'hop 0.5s ease';
            setTimeout(() => {
                dice.style.animation = '';
            }, 500);
        } else if (state.diceValue && state.phase === 'move') {
            // For late joiners / refresh
            const dice = diceDisplays[state.currentTurnColor];
            if (dice) dice.textContent = getDiceChar(state.diceValue);
        }
    }

    function updateStatusEl(msg) {
        statusEl.textContent = msg;
        statusEl.className = 'alert alert-info glass-card mt-3 text-center fw-600';
    }

    function getDiceChar(val) {
        const diceChars = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];
        return diceChars[val - 1] || '🎲';
    }
});
