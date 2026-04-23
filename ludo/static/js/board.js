// board.js

class LudoBoard {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        // Clean container and add classes
        this.container.innerHTML = '';
        this.container.classList.add('ludo-board-grid');

        this.colors = ['red', 'green', 'yellow', 'blue'];

        // Piece DOM elements
        this.pieceElements = {
            red: [], green: [], yellow: [], blue: []
        };

        // Mapping from 0-51 path to (row, col) in CSS Grid (1-indexed)
        this.pathCoords = this.generatePathCoordinates();
        // Mapping from 0-4 home path to (row, col)
        this.homeCoords = this.generateHomeCoordinates();

        this.onClickCallback = null;

        this.initGrid();
    }

    onPieceClick(callback) {
        this.onClickCallback = callback;
    }

    generatePathCoordinates() {
        let coords = [];
        // Left Arm (moving right)
        for (let c = 2; c <= 6; c++) coords.push({ r: 7, c: c });

        // Top Arm (moving up)
        for (let r = 6; r >= 1; r--) coords.push({ r: r, c: 7 });
        // Top Tip
        coords.push({ r: 1, c: 8 });
        // Top Arm (moving down)
        for (let r = 1; r <= 6; r++) coords.push({ r: r, c: 9 });

        // Right Arm (moving right)
        for (let c = 10; c <= 15; c++) coords.push({ r: 7, c: c });
        // Right Tip
        coords.push({ r: 8, c: 15 });
        // Right Arm (moving left)
        for (let c = 15; c >= 10; c--) coords.push({ r: 9, c: c });

        // Bottom Arm (moving down)
        for (let r = 10; r <= 15; r++) coords.push({ r: r, c: 9 });
        // Bottom Tip
        coords.push({ r: 15, c: 8 });
        // Bottom Arm (moving up)
        for (let r = 15; r >= 10; r--) coords.push({ r: r, c: 7 });

        // Left Arm (moving left)
        for (let c = 6; c >= 1; c--) coords.push({ r: 9, c: c });
        // Left Tip
        coords.push({ r: 8, c: 1 });
        // Last cell before start
        coords.push({ r: 7, c: 1 });

        return coords;
    }

    generateHomeCoordinates() {
        return {
            'red': Array.from({ length: 5 }, (_, i) => ({ r: 8, c: 2 + i })),
            'green': Array.from({ length: 5 }, (_, i) => ({ r: 2 + i, c: 8 })),
            'yellow': Array.from({ length: 5 }, (_, i) => ({ r: 8, c: 14 - i })),
            'blue': Array.from({ length: 5 }, (_, i) => ({ r: 14 - i, c: 8 }))
        };
    }

    initGrid() {
        // Safe squares
        const SAFE_SQUARES_COORDES = [
            { r: 7, c: 2 },
            { r: 3, c: 7 },
            { r: 2, c: 9 },
            { r: 7, c: 13 },
            { r: 9, c: 14 },
            { r: 13, c: 9 },
            { r: 14, c: 7 },
            { r: 9, c: 3 },
        ]
        // Create the 15x15 grid cells
        for (let r = 1; r <= 15; r++) {
            for (let c = 1; c <= 15; c++) {
                // Skip rendering standard cells inside the 6x6 corners and 3x3 center,
                // we'll handle those specifically.
                if ((r <= 6 && c <= 6) || (r <= 6 && c >= 10) || (r >= 10 && c >= 10) || (r >= 10 && c <= 6)) continue;
                if (r >= 7 && r <= 9 && c >= 7 && c <= 9) continue;

                const cell = document.createElement('div');
                cell.className = 'cell';
                const issafe = SAFE_SQUARES_COORDES.some(s => s.r === r && s.c === c);
                if (issafe) {
                    cell.classList.add('safe-square');
                    const star =
                        document.createElement('span');
                    star.className = 'safe-star';
                    star.textContent = '⭐';
                    cell.appendChild(star);
                }
                cell.style.gridRow = r;
                cell.style.gridColumn = c;

                // Add specific coloring based on path mapping
                // if (r === 7 && c >= 2 && c <= 6) cell.classList.add('path-red');
                if (r === 8 && c >= 2 && c <= 7) cell.classList.add('path-red'); // red home row
                // if (r >= 2 && r <= 6 && c === 7) cell.classList.add('path-green');
                if (r >= 2 && r <= 7 && c === 8) cell.classList.add('path-green'); // green home row
                // if (r === 9 && c >= 10 && c <= 14) cell.classList.add('path-yellow');
                if (r === 8 && c >= 9 && c <= 14) cell.classList.add('path-yellow'); // yellow home row
                // if (r >= 10 && r <= 14 && c === 9) cell.classList.add('path-blue');
                if (r >= 9 && r <= 14 && c === 8) cell.classList.add('path-blue'); // blue home row

                // Start cells
                if (r === 7 && c === 2) cell.style.backgroundColor = 'rgba(255, 59, 48, 0.4)';
                if (r === 2 && c === 9) cell.style.backgroundColor = 'rgba(52, 199, 89, 0.4)';
                if (r === 9 && c === 14) cell.style.backgroundColor = 'rgba(255, 204, 0, 0.4)';
                if (r === 14 && c === 7) cell.style.backgroundColor = 'rgba(0, 122, 255, 0.4)';

                this.container.appendChild(cell);
            }
        }

        // Add 4 Bases
        this.addBase('red', 1, 1);
        this.addBase('green', 1, 10);
        this.addBase('yellow', 10, 10);
        this.addBase('blue', 10, 1);

        // Add Center
        const center = document.createElement('div');
        center.className = 'home-center';
        center.innerHTML = '<span style="font-size: 2rem;">🏆</span>';
        this.container.appendChild(center);

        // Init pieces
        this.colors.forEach(color => {
            for (let i = 0; i < 4; i++) {
                const piece = document.createElement('div');
                piece.className = `piece ${color}`;
                piece.dataset.color = color;
                piece.dataset.index = i;

                piece.addEventListener('click', (e) => {
                    if (this.onClickCallback) this.onClickCallback(color, i);
                });

                this.pieceElements[color].push(piece);
                this.container.appendChild(piece);
            }
        });

    }

    addBase(color, row, col) {
        const base = document.createElement('div');
        base.className = `base base-${color}`;

        // Inner 2x2 grid for spots
        const inner = document.createElement('div');
        inner.className = 'base-inner';

        for (let i = 0; i < 4; i++) {
            const spot = document.createElement('div');
            spot.className = 'piece-spot';
            inner.appendChild(spot);
        }

        base.appendChild(inner);
        this.container.appendChild(base);

        // Note: The player avatars and dice will be injected into this base div in local_game.html!
    }

    draw(state) {
        if (!state || !state.pieces) return;

        const cellMap = {};
        const pieceDataList = [];

        for (const [color, positions] of Object.entries(state.pieces)) {
            positions.forEach((pos, idx) => {
                const { gridR, gridC } = this.getGridCoords(color, idx, pos);
                pieceDataList.push({ color, idx, pos, gridR, gridC });
                const key = `${gridR},${gridC}`;
                if (!cellMap[key]) cellMap[key] = [];
                cellMap[key].push({ color, idx });
            });
        }

        pieceDataList.forEach(p => {
            const key = `${p.gridR},${p.gridC}`;
            const total = cellMap[key].length;
            const offsetIdx = cellMap[key].findIndex(cp => cp.color === p.color && cp.idx === p.idx);
            this.updatePiecePosWithOffset(p.color, p.idx, p.pos, p.gridR, p.gridC, offsetIdx, total);
        });
    }

    getGridCoords(color, idx, pos) {
        let gridR = 1, gridC = 1;

        if (pos === -1) {
            // In base
            const offsets = {
                'red': { r: 2, c: 2 }, 'green': { r: 2, c: 11 },
                'yellow': { r: 11, c: 11 }, 'blue': { r: 11, c: 2 }
            };
            gridR = offsets[color].r + Math.floor(idx / 2) * 2;
            gridC = offsets[color].c + (idx % 2) * 2;
        } else if (pos >= 0 && pos <= 51) {
            let shiftedPos = pos;
            if (color === 'green') shiftedPos = (pos + 13) % 52;
            else if (color === 'yellow') shiftedPos = (pos + 26) % 52;
            else if (color === 'blue') shiftedPos = (pos + 39) % 52;

            const coord = this.pathCoords[Math.min(shiftedPos, 51)];
            if (coord) {
                gridR = coord.r;
                gridC = coord.c;
            }
        } else if (pos >= 100 && pos <= 105) {
            const hPos = pos - 100;
            if (hPos >= 5) {
                gridR = 8;
                gridC = 8;
            } else {
                const coord = this.homeCoords[color][hPos];
                if (coord) {
                    gridR = coord.r;
                    gridC = coord.c;
                }
            }
        }
        return { gridR, gridC };
    }

    updatePiecePosWithOffset(color, idx, pos, gridR, gridC, offsetIdx, total) {
        const piece = this.pieceElements[color][idx];
        if (!piece) return;

        // Calculate absolute top/left based on grid coordinates (1-indexed)
        const cellW = 100 / 15;
        let leftPct = (gridC - 1) * cellW + cellW * 0.15;
        let topPct = (gridR - 1) * cellW + cellW * 0.15;
        let scale = 1;

        if (total > 1 && pos >= 0) {
            scale = 0.75; // Shrink pieces a bit
            const maxCols = Math.ceil(Math.sqrt(total));
            const c = offsetIdx % maxCols;
            const r = Math.floor(offsetIdx / maxCols);

            // Adjust leftPct and topPct based on row and column within the cell
            const step = cellW * 0.3;
            leftPct += (c - (maxCols - 1) / 2) * step;
            topPct += (r - (maxCols - 1) / 2) * step;
        }

        piece.style.top = `${topPct}%`;
        piece.style.left = `${leftPct}%`;
        piece.style.transform = `scale(${scale})`;
        piece.style.zIndex = pos >= 0 ? (10 + offsetIdx) : 5;

        // Trigger hop animation if position changed
        if (piece.dataset.lastPos != pos) {
            piece.dataset.lastPos = pos;
            piece.classList.remove('hopping');
            void piece.offsetWidth; // trigger reflow
            piece.classList.add('hopping');
        }
    }
}
