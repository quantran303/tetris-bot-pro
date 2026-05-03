import copy

BOARD_WIDTH  = 10
BOARD_HEIGHT = 20

# Hinh dang 7 pieces, moi piece co cac goc xoay
# Moi goc xoay la list cac hang, moi hang la list 0/1
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


def matrix_to_board(matrix):
    """Chuyen matrix True/False sang board 1/0"""
    return [[1 if c else 0 for c in row] for row in matrix]


def new_board():
    return [[0]*BOARD_WIDTH for _ in range(BOARD_HEIGHT)]


def can_place(board, shape, x, y):
    """Kiem tra co the dat piece tai (x, y) khong"""
    for r, row in enumerate(shape):
        for c, val in enumerate(row):
            if not val:
                continue
            ny, nx = y + r, x + c
            if ny < 0 or ny >= BOARD_HEIGHT:
                return False
            if nx < 0 or nx >= BOARD_WIDTH:
                return False
            if board[ny][nx]:
                return False
    return True


def drop_y(board, shape, x):
    """Tim vi tri y thap nhat co the dat piece tai cot x"""
    y = 0
    while can_place(board, shape, x, y + 1):
        y += 1
    if not can_place(board, shape, x, y):
        return -1
    return y


def place_piece(board, shape, x, y):
    """Dat piece vao board, tra ve board moi"""
    b = copy.deepcopy(board)
    for r, row in enumerate(shape):
        for c, val in enumerate(row):
            if val:
                b[y+r][x+c] = 1
    return b


def clear_lines(board):
    """Xoa hang day, tra ve (board_moi, so_hang_da_xoa)"""
    kept = [row for row in board if not all(row)]
    cleared = BOARD_HEIGHT - len(kept)
    return [[0]*BOARD_WIDTH]*cleared + kept, cleared


def col_heights(board):
    """Tra ve chieu cao tung cot"""
    h = []
    for c in range(BOARD_WIDTH):
        height = 0
        for r in range(BOARD_HEIGHT):
            if board[r][c]:
                height = BOARD_HEIGHT - r
                break
        h.append(height)
    return h


def get_max_height(board):
    """Chieu cao lon nhat tren board"""
    for r in range(BOARD_HEIGHT):
        if any(board[r]):
            return BOARD_HEIGHT - r
    return 0


def count_holes(board):
    """Dem lo hong (o trong co block phia tren)"""
    holes = 0
    for c in range(BOARD_WIDTH):
        found = False
        for r in range(BOARD_HEIGHT):
            if board[r][c]:
                found = True
            elif found:
                holes += 1
    return holes


def count_wells(heights):
    """Dem do sau gieng (cot thap hon ca 2 ben)"""
    wells = 0
    for i in range(BOARD_WIDTH):
        left  = heights[i-1] if i > 0 else 99
        right = heights[i+1] if i < BOARD_WIDTH-1 else 99
        depth = min(left, right) - heights[i]
        if depth > 0:
            wells += depth
    return wells


# ============================================================
# TRONG SO DANH GIA BOARD
# Tang WEIGHT_LINES de bot tap trung clear line hon
# ============================================================
WEIGHT_LINES    =  800.0   # thuong cho moi hang cleared
WEIGHT_TETRIS   = 1200.0   # thuong them cho Tetris (4 hang)
WEIGHT_HOLES    = -350.0   # phat lo hong
WEIGHT_BUMP     =  -25.0   # phat do loi lom
WEIGHT_HEIGHT   =  -18.0   # phat chieu cao trung binh
WEIGHT_MAX_H    = -120.0   # phat chieu cao max
WEIGHT_WELLS    =  -20.0   # phat gieng sau
DANGER_HEIGHT   =   15     # nguong nguy hiem
DANGER_PENALTY  = -600.0   # phat them neu cao qua


def evaluate(board, lines_cleared):
    """
    Danh gia board sau khi dat piece.
    Diem cao = tot.
    Tap trung: clear nhieu hang, it lo hong, board phang.
    """
    heights = col_heights(board)
    max_h   = get_max_height(board)
    holes   = count_holes(board)
    avg_h   = sum(heights) / BOARD_WIDTH
    bump    = sum(abs(heights[i]-heights[i+1]) for i in range(BOARD_WIDTH-1))
    wells   = count_wells(heights)

    score = 0.0

    # Thuong clear line (luy tien manh)
    if lines_cleared == 4:
        score += WEIGHT_LINES * 4 + WEIGHT_TETRIS
    else:
        score += WEIGHT_LINES * lines_cleared

    # Cac penalty
    score += WEIGHT_HOLES  * holes
    score += WEIGHT_BUMP   * bump
    score += WEIGHT_HEIGHT * avg_h
    score += WEIGHT_MAX_H  * max_h
    score += WEIGHT_WELLS  * wells

    # Penalty nguy hiem
    if max_h >= DANGER_HEIGHT:
        score += DANGER_PENALTY * (max_h - DANGER_HEIGHT + 1)

    return score


def get_best_move(board, piece_type, next_piece=None):
    """
    Tim nuoc di tot nhat cho piece hien tai.
    Duyet toan bo rotation x col, co look-ahead 1 buoc.
    Tra ve (rotation_idx, col, score) hoac None.
    """
    if piece_type is None or piece_type not in PIECES:
        return None

    shapes = PIECES[piece_type]
    best   = None
    best_s = float('-inf')

    for rot_i, shape in enumerate(shapes):
        w = len(shape[0])
        for x in range(BOARD_WIDTH - w + 1):
            y = drop_y(board, shape, x)
            if y < 0:
                continue
            b1 = place_piece(board, shape, x, y)
            b1, cl1 = clear_lines(b1)

            # Look-ahead: thu next piece
            if next_piece and next_piece in PIECES:
                next_shapes = PIECES[next_piece]
                best_next = float('-inf')
                for ns in next_shapes:
                    nw = len(ns[0])
                    for nx2 in range(BOARD_WIDTH - nw + 1):
                        ny2 = drop_y(b1, ns, nx2)
                        if ny2 < 0:
                            continue
                        b2, cl2 = clear_lines(place_piece(b1, ns, nx2, ny2))
                        s2 = evaluate(b2, cl2)
                        if s2 > best_next:
                            best_next = s2
                score = evaluate(b1, cl1) + 0.4 * best_next
            else:
                score = evaluate(b1, cl1)

            if score > best_s:
                best_s = score
                best   = (rot_i, x, score)

    return best
