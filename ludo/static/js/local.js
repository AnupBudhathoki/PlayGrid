// local.js

document.addEventListener('DOMContentLoaded', () => {
    const board = new LudoBoard('ludo-board');
    const statusEl = document.getElementById('game-status');
    const colors = ['red', 'green', 'yellow', 'blue'];

    // UI Elements
    const diceDisplays = {};
    const playerPanels = {};

    // Inject Avatars and Dice into corners
    colors.forEach(c => {
        const baseEl = document.querySelector(`.base-${c}`);
        if (baseEl) {
            const cornerInfo = document.createElement('div');
            cornerInfo.className = 'corner-player-info';
            cornerInfo.id = `panel-${c}`;

            const avatar = document.createElement('img');
            // Using a default placeholder for now
            avatar.src = 'https://ui-avatars.com/api/?name=Player&background=random&color=fff';
            avatar.className = `player-avatar border-${c}`;

            const dice = document.createElement('div');
            dice.className = 'corner-dice';
            dice.id = `dice-${c}`;
            dice.textContent = '🎲';

            cornerInfo.appendChild(avatar);
            cornerInfo.appendChild(dice);
            baseEl.appendChild(cornerInfo);

            diceDisplays[c] = dice;
            playerPanels[c] = cornerInfo;

            dice.addEventListener('click', () => {
                if (state.activeColors[state.currentTurnIndex] !== c) return;
                if (dice.classList.contains('disabled')) return;
                rollDice();
            });
        }
    });

    let state = {
        pieces: {
            red: [-1, -1, -1, -1],
            blue: [-1, -1, -1, -1],
            green: [-1, -1, -1, -1],
            yellow: [-1, -1, -1, -1]
        },
        currentTurnIndex: 0,
        activeColors: ['red', 'green', 'yellow', 'blue'],
        status: 'awaiting_roll',
        hasStarted: { red: false, green: false, yellow: false, blue: false },
        rollsCount: { red: 0, green: 0, yellow: 0, blue: 0 },
        diceValue: null,
        winner: null
    };

    const COLOR_SHIFT = { red: 0, green: 13, yellow: 26, blue: 39 };
    const SAFE_POSITIONS = [0, 8, 13, 21, 26, 34, 39, 47];

    board.draw(state);
    statusEl.classList.remove('d-none');

    function getTurnColor() {
        return state.activeColors[state.currentTurnIndex];
    }

    function updateUI() {
        board.draw(state);
        colors.forEach(c => {
            if (playerPanels[c]) playerPanels[c].classList.remove('active-turn');
            if (diceDisplays[c]) diceDisplays[c].classList.add('disabled');
        });

        if (state.winner) {
            statusEl.textContent = `${state.winner.toUpperCase()} WINS!`;
            statusEl.className = 'alert alert-success glass-card mt-3 text-center fw-600';
            return;
        }

        const tc = getTurnColor();
        if (playerPanels[tc]) playerPanels[tc].classList.add('active-turn');

        if (state.status === 'awaiting_roll') {
            statusEl.textContent = `It is ${tc}'s turn to roll.`;
            if (diceDisplays[tc]) diceDisplays[tc].classList.remove('disabled');
        } else if (state.status === 'awaiting_move') {
            statusEl.textContent = `${tc} rolled a ${state.diceValue}. Select a piece to move.`;
            // Keep dice disabled while moving
            if (diceDisplays[tc]) diceDisplays[tc].classList.add('disabled');
        }
    }

    function rollDice() {
        let val = Math.floor(Math.random() * 6) + 1;
        const tc = getTurnColor();

        if (!state.hasStarted[tc]) {
            state.rollsCount[tc]++;
            if (state.rollsCount[tc] >= 10) {
                val = 1;
            }
        }
        
        state.diceValue = val;

        diceDisplays[tc].textContent = getDiceChar(val);
        diceDisplays[tc].style.animation = 'hop 0.5s ease';
        setTimeout(() => {
            diceDisplays[tc].style.animation = '';
        }, 500);

        setTimeout(() => {
            // Auto check if any piece can move.
            let canMove = false;
            for (let pos of state.pieces[tc]) {
                if (pos === -1 && (val === 6 || val === 1)) canMove = true;
                if (pos !== -1 && pos < 105) {
                    let nextPos = pos + val;
                    if (pos < 51 && nextPos >= 51) {
                        nextPos = 100 + (nextPos - 51);
                    }
                    if (nextPos <= 105) canMove = true;
                }
            }

            if (!canMove) {
                if (val !== 6) advanceTurn();
                else state.status = 'awaiting_roll';
                updateUI();
                return;
            }

            state.status = 'awaiting_move';
            updateUI();
        }, 500);
    }

    board.onPieceClick((clickedColor, pieceIndex) => {
        if (state.status !== 'awaiting_move') return;
        const tc = getTurnColor();

        if (clickedColor !== tc) return; // Only move your own pieces!

        let moved = false;
        const pieces = state.pieces[tc];
        const pos = pieces[pieceIndex];

        if ((state.diceValue === 6 || state.diceValue === 1) && pos === -1) {
            pieces[pieceIndex] = 0; // Move out of base
            state.hasStarted[tc] = true;
            moved = true;
        } else if (pos !== -1 && pos < 105) {
            let nextPos = pos + state.diceValue;
            if (pos < 51 && nextPos >= 51) {
                nextPos = 100 + (nextPos - 51);
            }
            if (nextPos <= 105) {
                pieces[pieceIndex] = nextPos;
                moved = true;
            }
        }

        if (moved) {
            const gotKill = killOpponents(tc, pieces[pieceIndex]);  // ← new line

            checkWinCondition();
            if (!state.winner) {
                if (state.diceValue !== 6 && !gotKill) {
                    advanceTurn();                   // normal: next player's turn
                } else {
                    state.status = 'awaiting_roll'; // bonus turn: rolled 6 OR kill
                }
            }
            updateUI();
        } else {
            statusEl.textContent = 'Invalid piece. Click another.';
        }

    });

    function advanceTurn() {
        state.currentTurnIndex = (state.currentTurnIndex + 1) % state.activeColors.length;
        state.status = 'awaiting_roll';
    }

    function killOpponents(myColor, myPos) {
        if (myPos < 0 || myPos >= 100) return false;
        const myIndex = (myPos + COLOR_SHIFT[myColor]) % 52;

        if (SAFE_POSITIONS.includes(myIndex)) return false;

        let killed = false;

        for (const oppColor of state.activeColors) {
            if (oppColor === myColor) continue;

            for (let i = 0; i < state.pieces[oppColor].length; i++) {
                const oppPos = state.pieces[oppColor][i];

                if (oppPos < 0 || oppPos >= 100) continue;
                const oppIndex = (oppPos + COLOR_SHIFT[oppColor]) % 52;
                if (oppIndex === myIndex) {
                    state.pieces[oppColor][i] = -1;
                    killed = true;
                }
            }
        }
        return killed;
    }

    function checkWinCondition() {
        for (let c of state.activeColors) {
            if (state.pieces[c].every(pos => pos === 105)) {
                state.winner = c;
                state.status = 'finished';
            }
        }
    }

    function getDiceChar(val) {
        const chars = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];
        return chars[val - 1] || '🎲';
    }

    // Init UI 
    updateUI();
});
