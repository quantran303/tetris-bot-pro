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
    y = 0
    while y + h_shape <= BOARD_HEIGHT:
        for row in range(h_shape):
            for col in range(w_shape):
                if shape[row][col] and board[y + row][x + col]:
                    return y - 1
        y += 1
    return y - 1


def place_piece(board, shape, x, y):
    """Dat piece vao board, tra ve board moi"""
    new_b = copy.deepcopy(board)
    for row in range(len(shape)):
        for col in range(len(shape[0])):
            if shape[row][col]:
                if 0 <= y + row < BOARD_HEIGHT and 0 <= x + col < BOARD_WIDTH:
                    new_b[y + row][x + col] = 1
    return new_b


def clear_lines(board):
    """Xoa cac hang day, tra ve (board_moi, so_hang_xoa)"""
    new_b = [row for row in board if not all(row)]
    cleared = BOARD_HEIGHT - len(new_b)
    new_b = [[0]*BOARD_WIDTH for _ in range(cleared)] + new_b
    return new_b, cleared


def get_column_heights(board):
    heights = []
    for col in range(BOARD_WIDTH):
        h = 0
        for row in range(BOARD_HEIGHT):
            if board[row][col]:
                h = BOARD_HEIGHT - row
                break
        heights.append(h)
    return heights


def get_max_height(board):
    """Tinh chieu cao thuc te: dem tu hang co block dau tien tu duoi len"""
    for row in range(BOARD_HEIGHT):
        if any(board[row]):
            return BOARD_HEIGHT - row
    return 0  # Board trong = chieu cao 0


def count_holes(board):
    holes = 0
    for col in range(BOARD_WIDTH):
        block_found = False
        for row in range(BOARD_HEIGHT):
            if board[row][col]:
                block_found = True
            elif block_found:
                holes += 1
    return holes


def count_bumpiness(heights):
    return sum(abs(heights[i] - heights[i+1]) for i in range(len(heights)-1))


def count_complete_lines(board):
    return sum(1 for row in board if all(row))


def evaluate_board(board, lines_cleared):
    """
    Ham danh gia board sau khi dat piece.
    Diem cao = tot, diem thap = xau.
    """
    heights = get_column_heights(board)
    max_h = get_max_height(board)
    holes = count_holes(board)
    bumpiness = count_bumpiness(heights)
    avg_height = sum(heights) / BOARD_WIDTH

    score = 0

    # Thuong cho moi hang cleared
    line_rewards = [0, 100, 300, 700, 1500]
    score += line_rewards[min(lines_cleared, 4)]

    # Phat neu board cao
    if max_h > MAX_HARD_HEIGHT:
        score -= (max_h - MAX_HARD_HEIGHT) * 500
    elif max_h > MAX_SAFE_HEIGHT:
        score -= (max_h - MAX_SAFE_HEIGHT) * 100

    # Phat lo hong
    score -= holes * 150

    # Phat do gon song
    score -= bumpiness * 30

    # Phat chieu cao trung binh
    score -= avg_height * 10

    return score


def get_best_move(board, piece_type, next_piece=None):
    """
    Tim nuoc di tot nhat cho piece hien tai.
    Tra ve (rotation, x, score) hoac None neu khong tim duoc.
    """
    if piece_type is None or piece_type not in PIECES:
        return None

    shapes = PIECES[piece_type]
    best_score = float('-inf')
    best_move = None

    for rot_idx, shape in enumerate(shapes):
        w = len(shape[0])
        for x in range(BOARD_WIDTH - w + 1):
            y = drop_piece(board, shape, x)
            if y < 0:
                continue
            new_b = place_piece(board, shape, x, y)
            new_b, cleared = clear_lines(new_b)

            # Look-ahead: neu co next piece, tinh them 1 buoc
            if next_piece and next_piece in PIECES:
                next_shapes = PIECES[next_piece]
                best_next = float('-inf')
                for ns in next_shapes:
                    nw = len(ns[0])
                    for nx in range(BOARD_WIDTH - nw + 1):
                        ny = drop_piece(new_b, ns, nx)
                        if ny < 0:
                            continue
                        nb2 = place_piece(new_b, ns, nx, ny)
                        nb2, c2 = clear_lines(nb2)
                        s2 = evaluate_board(nb2, c2)
                        if s2 > best_next:
                            best_next = s2
                score = evaluate_board(new_b, cleared) + 0.3 * best_next
            else:
                score = evaluate_board(new_b, cleared)

            if score > best_score:
                best_score = score
                best_move = (rot_idx, x, score)

    return best_move


def matrix_to_board(matrix):
    """
    Chuyen matrix tu vision.py (True/False) sang board noi bo (1/0).
    matrix[row][col] = True neu o do co block.
    """
    board = []
    for row in matrix:
        board.append([1 if cell else 0 for cell in row])
    return board
