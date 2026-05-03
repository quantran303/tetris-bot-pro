"""
engine_ai.py - AI logic dua tren mikhail-vlasenko/Tetris-AI

Kien truc:
1. PIECES: mang numpy 4x4 cua 7 tetromino x 4 rotation (giong figures.py)
2. check_collision: kiem tra va cham
3. land: simulate piece roi xuong
4. all_landings: tra ve tat ca vi tri co the dat piece
5. get_score: ham diem so dua tren:
   - blank_cnt (lo rong bi che): phat nang nhat
   - max_height: phat khi cao
   - count_cleared: thuong manh khi >= 4 (Tetris)
   - almost_full_line: thuong khi gan day hang
   - find_hole: phat khi co gieng sau
6. best_move: depth-2 lookahead
"""
import copy
import numpy as np

BOARD_W = 10
BOARD_H = 20

# ---------------------------------------------------------------------------
# PIECES: 7 tetromino, moi cai co 4 rotations, mang 4x4
# Thu tu: I=0, O=1, T=2, S=3, Z=4, J=5, L=6
# Giong figures.py cua mikhail-vlasenko
# ---------------------------------------------------------------------------

PIECES = np.array([
    # I (idx=0) - 4x4
    [
        [[1,1,1,1],[0,0,0,0],[0,0,0,0],[0,0,1,0]],
        [[0,0,1,0],[0,0,1,0],[0,0,1,0],[0,0,1,0]],
        [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
        [[0,1,0,0],[0,1,0,0],[0,1,0,0],[0,1,0,0]],
    ],
    # O (idx=1)
    [
        [[0,1,1,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
        [[0,1,1,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
        [[0,1,1,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
        [[0,1,1,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
    ],
    # T (idx=2)
    [
        [[0,1,0,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
        [[0,1,0,0],[0,1,1,0],[0,1,0,0],[0,0,0,0]],
        [[0,0,0,0],[1,1,1,0],[0,1,0,0],[0,0,0,0]],
        [[0,1,0,0],[1,1,0,0],[0,1,0,0],[0,0,0,0]],
    ],
    # S (idx=3)
    [
        [[0,1,1,0],[1,1,0,0],[0,0,0,0],[0,0,0,0]],
        [[0,1,0,0],[0,1,1,0],[0,0,1,0],[0,0,0,0]],
        [[0,0,0,0],[0,1,1,0],[1,1,0,0],[0,0,0,0]],
        [[1,0,0,0],[1,1,0,0],[0,1,0,0],[0,0,0,0]],
    ],
    # Z (idx=4)
    [
        [[1,1,0,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
        [[0,0,1,0],[0,1,1,0],[0,1,0,0],[0,0,0,0]],
        [[0,0,0,0],[1,1,0,0],[0,1,1,0],[0,0,0,0]],
        [[0,1,0,0],[1,1,0,0],[1,0,0,0],[0,0,0,0]],
    ],
    # J (idx=5)
    [
        [[1,0,0,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
        [[0,1,1,0],[0,1,0,0],[0,1,0,0],[0,0,0,0]],
        [[0,0,0,0],[1,1,1,0],[0,0,1,0],[0,0,0,0]],
        [[0,1,0,0],[0,1,0,0],[1,1,0,0],[0,0,0,0]],
    ],
    # L (idx=6)
    [
        [[0,0,1,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
        [[0,1,0,0],[0,1,0,0],[0,1,1,0],[0,0,0,0]],
        [[0,0,0,0],[1,1,1,0],[1,0,0,0],[0,0,0,0]],
        [[1,1,0,0],[0,1,0,0],[0,1,0,0],[0,0,0,0]],
    ],
], dtype=np.int32)

PIECE_NAMES = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']
NAME_TO_IDX = {n: i for i, n in enumerate(PIECE_NAMES)}

def piece_name_to_idx(name: str) -> int:
    return NAME_TO_IDX.get(name, -1)

# ---------------------------------------------------------------------------
# Collision & Landing (dich tu find_landings.py)
# ---------------------------------------------------------------------------

def check_collision(field: np.ndarray, piece: np.ndarray, pos_row: int, pos_col: int, piece_idx: int) -> bool:
    """
    Kiem tra va cham piece tai vi tri (pos_row, pos_col).
    I-piece dung 4x4, con lai 3x3.
    """
    r = 4 if piece_idx == 0 else 3
    for i in range(r):
        for j in range(r):
            if piece[i][j]:
                ni, nj = i + pos_row, j + pos_col
                if ni < 0 or ni >= BOARD_H or nj < 0 or nj >= BOARD_W:
                    return True
                if field[ni][nj]:
                    return True
    return False

def land(field: np.ndarray, piece: np.ndarray, x_pos: int, piece_idx: int):
    """
    Simulate piece roi tu tren xuong tai cot x_pos.
    Tra ve board moi sau khi dat piece, hoac None neu khong hop le.
    (Dich tu find_landings.land())
    """
    f = field.copy()
    pos_row = 0
    while not check_collision(f, piece, pos_row, x_pos, piece_idx):
        pos_row += 1
    if pos_row == 0:
        return None  # Khong co cho cho piece
    pos_row -= 1
    # Dat piece vao board
    r = 4 if piece_idx == 0 else 4
    for i in range(4):
        for j in range(4):
            if piece[i][j]:
                ni, nj = i + pos_row, j + x_pos
                if 0 <= ni < BOARD_H and 0 <= nj < BOARD_W:
                    f[ni][nj] = 1
    return f

# ---------------------------------------------------------------------------
# All landings
# ---------------------------------------------------------------------------

def all_landings(field: np.ndarray, piece_idx: int):
    """
    Tinh tat ca vi tri co the dat piece_idx len board.
    Tra ve list cua (result_field, rotation, x_pos).
    (Dich tu find_landings.all_landings())
    """
    results = []
    for rotation in range(4):
        piece = PIECES[piece_idx][rotation]
        for x_pos in range(-1, BOARD_W):
            res = land(field, piece, x_pos, piece_idx)
            if res is not None:
                results.append((res, rotation, x_pos))
    return results

# ---------------------------------------------------------------------------
# Score function (dich tu AI_main.get_score())
# ---------------------------------------------------------------------------

def clear_lines(field: np.ndarray):
    """
    Xoa cac hang day va tra ve (field_moi, so_hang_da_xoa).
    (Dich tu AI_main.clear_line())
    """
    f = field.copy()
    full_cnt = 0
    i = 0
    while i < BOARD_H:
        if np.sum(f[i]) == BOARD_W:
            full_cnt += 1
            f = np.delete(f, i, axis=0)
            f = np.insert(f, 0, np.zeros(BOARD_W, dtype=np.int32), axis=0)
        else:
            i += 1
    return f, full_cnt

def find_roofs(field: np.ndarray):
    """
    Tim o rong bi che phia duoi cac khoi da dat va cac thong tin lien quan.
    Tra ve: (blank_cnt, max_height, column_heights, blank_cumulative_depth)
    (Dich tu AI_main.find_roofs())
    """
    tops = np.zeros((BOARD_W, 2), dtype=float)
    blank_cnt   = 0
    blank_depth = 0
    for i in range(BOARD_H):
        for j in range(BOARD_W):
            if field[i][j]:
                if tops[j][0] == 0:
                    tops[j][0] = BOARD_H - 1 - i  # chieu cao tinh tu duoi
                tops[j][1] += 1
            elif tops[j][0] != 0:
                blank_cnt   += 1
                blank_depth += tops[j][1] - 1
    max_height   = int(np.max(tops[:, 0]))
    col_heights  = tops[:, 0]
    return blank_cnt, max_height, col_heights, blank_depth

def almost_full_line(field: np.ndarray) -> float:
    """
    Thuong cho cac hang gan day (9/10 hoac 8/10 o da dien).
    (Dich tu AI_main.almost_full_line())
    """
    score = 0.0
    for i in range(BOARD_H):
        s = int(np.sum(field[i]))
        if s == BOARD_W - 1:
            score += 2.0
        elif s == BOARD_W - 2:
            score += 0.5
    return score

def find_hole(col_heights: np.ndarray) -> int:
    """
    Phat khi co cot qua thap so voi hang xom ("gieng").
    (Dich tu AI_main.find_hole())
    """
    cnt_hole = 0
    prev_h   = 20
    h        = col_heights.copy()
    h[-1]    = 20  # cot cuoi khong tinh
    for i in range(1, BOARD_W - 1):
        if prev_h - 2 > h[i] and h[i] < h[i+1] - 2:
            cnt_hole += 1
            if prev_h - 4 > h[i] and h[i] < h[i+1] - 4:
                cnt_hole += min(prev_h - 4 - h[i], h[i+1] - 4 - h[i])
        prev_h = h[i]
    return cnt_hole

def get_score(field: np.ndarray, scared: bool = False) -> (float, bool):
    """
    Tra ve (diem_so, expect_tetris).
    Logic hoan toan theo AI_main.get_score() cua mikhail-vlasenko.
    """
    expect_tetris = False
    score         = 0.0

    cleared_field, count_cleared = clear_lines(field)
    blank_cnt, max_height, col_heights, blank_depth = find_roofs(cleared_field)

    score += almost_full_line(cleared_field)

    # Tetris (4 hang) rat tot
    if count_cleared >= 4:
        score += 1000
        expect_tetris = True

    # Mode scared (board cao > 13): uu tien clear hang hon het
    if scared:
        score += 10 * count_cleared
        score -= max_height + max_height ** 1.4
        return score, expect_tetris

    # Mode binh thuong
    score -= blank_cnt   * 10     # lo rong bi che: phat nang
    score -= blank_depth * 2      # do sau lo: phat them

    if max_height > 7:
        score -= max_height ** 1.4

    score -= find_hole(col_heights) * 10

    if blank_cnt > 0:
        score += 5 * count_cleared

    # Khuyen khich xoa duoc hang
    score -= 3 * count_cleared  # phat nhe viec xoa < 4 hang khi khong co lo

    # Cot ngoai cung ben phai nen trong
    if col_heights[-1] != 0:
        score -= 10
        score -= col_heights[-1]

    return score, expect_tetris

# ---------------------------------------------------------------------------
# Best move: depth-1 va depth-2 (dich tu AI_main.calc_best/choose_action_depth2)
# ---------------------------------------------------------------------------

def best_move(board: np.ndarray, piece_name: str, next_piece_name: str = None,
              depth2_choices: int = 5, scared: bool = False):
    """
    Tim nuoc di tot nhat cho piece hien tai.
    Tra ve (rotation, x_pos, score) hoac None neu khong co nuoc.

    - depth2_choices: so luong ung vien hang dau de xet lookahead
    - scared: mode khi board qua cao
    """
    piece_idx = piece_name_to_idx(piece_name)
    if piece_idx < 0:
        return None

    landings = all_landings(board, piece_idx)
    if not landings:
        return None

    # Tinh score cho moi vi tri
    scored = []
    for (res_field, rot, x_pos) in landings:
        s, exp_tet = get_score(res_field, scared)
        scored.append((s, exp_tet, rot, x_pos, res_field))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not next_piece_name or depth2_choices <= 1:
        best = scored[0]
        return best[2], best[3], best[0]  # rotation, x_pos, score

    # Depth-2 lookahead
    next_idx  = piece_name_to_idx(next_piece_name)
    top_n     = scored[:depth2_choices]
    best_total = None
    best_rot   = 0
    best_x     = 0

    for (s, exp_tet, rot, x_pos, res_field) in top_n:
        # Clear lines truoc khi tinh next piece
        cleared, _ = clear_lines(res_field)

        if next_idx >= 0:
            next_landings = all_landings(cleared, next_idx)
            if next_landings:
                next_scores = [get_score(nf, scared)[0] for (nf, nr, nx) in next_landings]
                next_best   = max(next_scores)
            else:
                next_best = -9999
        else:
            next_best = 0

        # Tong diem: diem hien tai + diem tuong lai + bonus Tetris
        total = s + next_best + (1000 if exp_tet else 0)

        if best_total is None or total > best_total:
            best_total = total
            best_rot   = rot
            best_x     = x_pos

    return best_rot, best_x, best_total
