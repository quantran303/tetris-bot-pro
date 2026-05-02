import copy

BOARD_WIDTH = 10
BOARD_HEIGHT = 20
MAX_SAFE_HEIGHT = 16
MAX_HARD_HEIGHT = 18

PIECES = {
    'I': [[[1,1,1,1]],[[1],[1],[1],[1]]],
    'O': [[[1,1],[1,1]]],
    'T': [[[0,1,0],[1,1,1]],[[1,0],[1,1],[1,0]],[[1,1,1],[0,1,0]],[[0,1],[1,1],[0,1]]],
    'S': [[[0,1,1],[1,1,0]],[[1,0],[1,1],[0,1]]],
    'Z': [[[1,1,0],[0,1,1]],[[0,1],[1,1],[1,0]]],
    'J': [[[1,0,0],[1,1,1]],[[1,1],[1,0],[1,0]],[[1,1,1],[0,0,1]],[[0,1],[0,1],[1,1]]],
    'L': [[[0,0,1],[1,1,1]],[[1,0],[1,0],[1,1]],[[1,1,1],[1,0,0]],[[1,1],[0,1],[0,1]]],
}

def new_board():
    return [[0]*BOARD_WIDTH for _ in range(BOARD_HEIGHT)]

def drop_piece(board, shape, x):
    h_shape = len(shape)
    w_shape = len(shape[0])
    best_y = None
    for y in range(BOARD_HEIGHT - h_shape + 1):
        collision = False
        for sy in range(h_shape):
            for sx in range(w_shape):
                if not shape[sy][sx]:
                    continue
                bx, by = x + sx, y + sy
                if bx < 0 or bx >= BOARD_WIDTH or by >= BOARD_HEIGHT:
                    collision = True
                    break
                if board[by][bx]:
                    collision = True
                    break
            if collision:
                break
        if collision:
            break
        best_y = y
    if best_y is None:
        return None, 0
    newb = copy.deepcopy(board)
    for sy in range(h_shape):
        for sx in range(w_shape):
            if shape[sy][sx]:
                newb[best_y + sy][x + sx] = 1
    cleared = 0
    rows_to_keep = []
    for row in newb:
        if all(row):
            cleared += 1
        else:
            rows_to_keep.append(row)
    while len(rows_to_keep) < BOARD_HEIGHT:
        rows_to_keep.insert(0, [0]*BOARD_WIDTH)
    return rows_to_keep, cleared

def column_heights(board):
    heights = []
    for x in range(BOARD_WIDTH):
        h = 0
        for y in range(BOARD_HEIGHT):
            if board[y][x]:
                h = BOARD_HEIGHT - y
                break
        heights.append(h)
    return heights

def max_height(heights):
    return max(heights) if heights else 0

def count_holes(board):
    holes = 0
    for x in range(BOARD_WIDTH):
        found = False
        for y in range(BOARD_HEIGHT):
            if board[y][x]:
                found = True
            elif found:
                holes += 1
    return holes

def bumpiness(heights):
    return sum(abs(heights[i]-heights[i+1]) for i in range(len(heights)-1))

def row_transitions(board):
    total = 0
    for row in board:
        for i in range(len(row)-1):
            if row[i] != row[i+1]:
                total += 1
    return total

def col_transitions(board):
    total = 0
    for x in range(BOARD_WIDTH):
        for y in range(BOARD_HEIGHT-1):
            if board[y][x] != board[y+1][x]:
                total += 1
    return total

def near_full_row_bonus(board):
    bonus = 0
    for row in board:
        filled = sum(row)
        if filled >= 9:
            bonus += 15
        elif filled >= 8:
            bonus += 8
        elif filled >= 7:
            bonus += 3
    return bonus

def evaluate_board_pro(board, cleared):
    heights = column_heights(board)
    agg_h = sum(heights)
    mh = max_height(heights)
    holes = count_holes(board)
    bump = bumpiness(heights)
    rt = row_transitions(board)
    ct = col_transitions(board)
    clear_bonus = [0, 5, 18, 35, 60][min(cleared, 4)]
    nf_bonus = near_full_row_bonus(board)
    score = clear_bonus + nf_bonus
    avg_h = agg_h / BOARD_WIDTH
    height_dev = sum(abs(h - avg_h) for h in heights)
    if mh <= 10:
        score -= agg_h * 0.20
        score -= height_dev * 0.70
        score -= holes * 6.0
        score -= bump * 0.30
        score -= rt * 0.15
        score -= ct * 0.15
    else:
        score -= agg_h * 1.0
        score -= height_dev * 1.0
        score -= holes * 12.0
        score -= bump * 0.5
        score -= rt * 0.3
        score -= ct * 0.3
    if mh >= MAX_HARD_HEIGHT:
        score -= 2000
    elif mh >= MAX_SAFE_HEIGHT:
        score -= 600
    return score

def best_move_one(board, piece_type):
    best_score, best = None, None
    for r, shape in enumerate(PIECES.get(piece_type, [])):
        w = len(shape[0])
        for x in range(BOARD_WIDTH - w + 1):
            newb, cleared = drop_piece(board, shape, x)
            if newb is None:
                continue
            score = evaluate_board_pro(newb, cleared)
            if best_score is None or score > best_score:
                best_score = score
                best = (r, x, newb, cleared, score)
    return best

def best_move_lookahead(board, current_piece, next_pieces=None, depth=2):
    if not next_pieces or depth <= 1:
        return best_move_one(board, current_piece)
    best_first, best_total = None, None
    for r, shape in enumerate(PIECES.get(current_piece, [])):
        w = len(shape[0])
        for x in range(BOARD_WIDTH - w + 1):
            newb, cleared = drop_piece(board, shape, x)
            if newb is None:
                continue
            score = evaluate_board_pro(newb, cleared)
            total = score
            b2 = newb
            for i, p in enumerate(next_pieces[:depth-1]):
                mv = best_move_one(b2, p)
                if mv is None:
                    break
                _, _, newb2, _, sc2 = mv
                total += sc2 * (0.75 ** (i+1))
                b2 = newb2
            if best_total is None or total > best_total:
                best_total = total
                best_first = (r, x, newb, cleared, total)
    return best_first
