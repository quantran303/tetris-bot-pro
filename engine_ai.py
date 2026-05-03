import copy

BOARD_WIDTH  = 10
BOARD_HEIGHT = 20

# 7 standard tetrominoes – each rotation is a list of rows (0/1)
PIECES = {
    'I': [
        [[1,1,1,1]],
        [[1],[1],[1],[1]],
    ],
    'O': [
        [[1,1],[1,1]],
    ],
    'T': [
        [[0,1,0],[1,1,1]],
        [[1,0],[1,1],[1,0]],
        [[1,1,1],[0,1,0]],
        [[0,1],[1,1],[0,1]],
    ],
    'S': [
        [[0,1,1],[1,1,0]],
        [[1,0],[1,1],[0,1]],
    ],
    'Z': [
        [[1,1,0],[0,1,1]],
        [[0,1],[1,1],[1,0]],
    ],
    'J': [
        [[1,0,0],[1,1,1]],
        [[1,1],[1,0],[1,0]],
        [[1,1,1],[0,0,1]],
        [[0,1],[0,1],[1,1]],
    ],
    'L': [
        [[0,0,1],[1,1,1]],
        [[1,0],[1,0],[1,1]],
        [[1,1,1],[1,0,0]],
        [[1,1],[0,1],[0,1]],
    ],
}

# ---------------------------------------------------------------------------
# Board helpers
# ---------------------------------------------------------------------------

def matrix_to_board(matrix):
    """Convert vision matrix (list of lists with 0/1) to a flat board
    represented as a list of rows from top to bottom."""
    return [list(row) for row in matrix]

def new_board():
    return [[0]*BOARD_WIDTH for _ in range(BOARD_HEIGHT)]

def can_place(board, piece_matrix, row, col):
    for r, line in enumerate(piece_matrix):
        for c, cell in enumerate(line):
            if cell:
                nr, nc = row + r, col + c
                if nr < 0 or nr >= BOARD_HEIGHT or nc < 0 or nc >= BOARD_WIDTH:
                    return False
                if board[nr][nc]:
                    return False
    return True

def drop_y(board, piece_matrix, col):
    """Return the lowest valid row for hard-drop."""
    row = 0
    while row + 1 <= BOARD_HEIGHT and can_place(board, piece_matrix, row, col):
        row += 1
    row -= 1
    return row if row >= 0 else None

def place_piece(board, piece_matrix, row, col):
    b = copy.deepcopy(board)
    for r, line in enumerate(piece_matrix):
        for c, cell in enumerate(line):
            if cell:
                b[row + r][col + c] = 1
    return b

def clear_lines(board):
    new_b = [row for row in board if any(c == 0 for c in row)]
    cleared = BOARD_HEIGHT - len(new_b)
    new_b = [[0]*BOARD_WIDTH]*cleared + new_b
    return new_b, cleared

# ---------------------------------------------------------------------------
# Board analysis helpers
# ---------------------------------------------------------------------------

def col_heights(board):
    heights = []
    for c in range(BOARD_WIDTH):
        h = 0
        for r in range(BOARD_HEIGHT):
            if board[r][c]:
                h = BOARD_HEIGHT - r
                break
        heights.append(h)
    return heights

def count_holes(board, heights):
    holes = 0
    for c in range(BOARD_WIDTH):
        top_row = BOARD_HEIGHT - heights[c]
        for r in range(top_row + 1, BOARD_HEIGHT):
            if board[r][c] == 0:
                holes += 1
    return holes

def bumpiness(heights):
    return sum(abs(heights[i] - heights[i+1]) for i in range(len(heights)-1))

def count_complete_lines(board):
    return sum(1 for row in board if all(c for c in row))

def well_depth(board, heights):
    """Sum of well depths (columns that are much lower than neighbours).
    A deep well on the left is desired for Tetris setups."""
    total = 0
    for c in range(BOARD_WIDTH):
        left  = heights[c-1] if c > 0 else 100
        right = heights[c+1] if c < BOARD_WIDTH-1 else 100
        depth = min(left, right) - heights[c]
        if depth > 0:
            total += depth
    return total

def count_covered_cells(board, heights):
    """Cells that are empty but have a filled cell above them (blockades)."""
    blocked = 0
    for c in range(BOARD_WIDTH):
        top_row = BOARD_HEIGHT - heights[c]
        found_block = False
        for r in range(BOARD_HEIGHT):
            if board[r][c] == 1:
                found_block = True
            elif found_block and board[r][c] == 0:
                blocked += 1
    return blocked

def detect_tspin_slot(board, heights):
    """Reward positions that look like a T-spin setup:
    a T-shaped cavity (3-wide indent with overhang on both sides)."""
    score = 0
    for c in range(1, BOARD_WIDTH - 1):
        # Center column lower than both neighbours by 2+
        left  = heights[c-1]
        mid   = heights[c]
        right = heights[c+1]
        if left >= mid + 2 and right >= mid + 2:
            score += 1  # potential T-spin Double setup
    return score

# ---------------------------------------------------------------------------
# Scoring – pro-level weights
# ---------------------------------------------------------------------------

# Weights tuned toward tetr.io competitive play:
# Priority: avoid holes > clear lines (Tetris >> singles) > low height > low bumpiness
WEIGHTS = {
    'lines_cleared_1': -0.5,   # single clear (ok but not great)
    'lines_cleared_2': 2.0,    # double
    'lines_cleared_3': 4.0,    # triple
    'lines_cleared_4': 10.0,   # Tetris!  (reward strongly)
    'holes':          -8.0,    # penalise holes heavily
    'blockades':      -3.5,    # cells blocked above holes
    'bumpiness':      -0.8,    # prefer flat surface
    'max_height':     -1.5,    # penalise stacking high
    'sum_heights':    -0.6,    # prefer overall low
    'well_depth':      0.5,    # small reward for a well (Tetris prep)
    'tspin_slot':      3.0,    # reward T-spin setups
    'i_piece_bonus':   2.0,    # extra reward when I-piece clears 4 lines
}

def evaluate(board, lines_cleared, piece_type='?', b2b=False):
    heights = col_heights(board)
    holes   = count_holes(board, heights)
    bumps   = bumpiness(heights)
    maxh    = max(heights)
    sumh    = sum(heights)
    covered = count_covered_cells(board, heights)
    well    = well_depth(board, heights)
    tspin   = detect_tspin_slot(board, heights)

    # Line clear reward table
    lc_map = {0: 0, 1: WEIGHTS['lines_cleared_1'], 2: WEIGHTS['lines_cleared_2'],
               3: WEIGHTS['lines_cleared_3'], 4: WEIGHTS['lines_cleared_4']}
    lc_score = lc_map.get(lines_cleared, WEIGHTS['lines_cleared_4'])

    # Back-to-back bonus (B2B Tetris / T-spin)
    if b2b and lines_cleared >= 4:
        lc_score *= 1.5

    # Extra reward for I-piece Tetris
    if piece_type == 'I' and lines_cleared == 4:
        lc_score += WEIGHTS['i_piece_bonus']

    score = (
        lc_score
        + holes   * WEIGHTS['holes']
        + covered * WEIGHTS['blockades']
        + bumps   * WEIGHTS['bumpiness']
        + maxh    * WEIGHTS['max_height']
        + sumh    * WEIGHTS['sum_heights']
        + well    * WEIGHTS['well_depth']
        + tspin   * WEIGHTS['tspin_slot']
    )
    return score

# ---------------------------------------------------------------------------
# Main search – best placement for one piece (with 1-piece lookahead)
# ---------------------------------------------------------------------------

def best_move(board, piece_type, next_piece_type=None, b2b=False):
    """
    Returns (rotation_index, col, score).
    Searches every rotation x column for `piece_type`.
    If `next_piece_type` is given, adds a 1-piece lookahead.
    """
    rotations = PIECES.get(piece_type, [])
    if not rotations:
        return 0, BOARD_WIDTH // 2, -9999

    best_score = None
    best_rot   = 0
    best_col   = 0

    for rot_i, piece_matrix in enumerate(rotations):
        pw = len(piece_matrix[0])
        for x in range(BOARD_WIDTH - pw + 1):
            y = drop_y(board, piece_matrix, x)
            if y is None:
                continue
            placed = place_piece(board, piece_matrix, y, x)
            placed, cleared = clear_lines(placed)

            if next_piece_type and PIECES.get(next_piece_type):
                # 1-piece lookahead: pick best next placement
                next_best = None
                for nrot, npm in enumerate(PIECES[next_piece_type]):
                    npw = len(npm[0])
                    for nx in range(BOARD_WIDTH - npw + 1):
                        ny = drop_y(placed, npm, nx)
                        if ny is None:
                            continue
                        nb = place_piece(placed, npm, ny, nx)
                        nb, nc = clear_lines(nb)
                        ns = evaluate(nb, nc, next_piece_type, b2b)
                        if next_best is None or ns > next_best:
                            next_best = ns
                lookahead = next_best if next_best is not None else 0
            else:
                lookahead = 0

            base  = evaluate(placed, cleared, piece_type, b2b)
            total = base + 0.5 * lookahead   # weight lookahead lower

            if best_score is None or total > best_score:
                best_score = total
                best_rot   = rot_i
                best_col   = x

    if best_score is None:
        return 0, BOARD_WIDTH // 2, -9999
    return best_rot, best_col, best_score
