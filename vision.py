import mss
import numpy as np
import os
import json
import time

BOARD_WIDTH = 10
BOARD_HEIGHT = 20
CALIB_FILE = "calibration.json"

# Toa do mac dinh (1920x1080, Chrome fullscreen, Windows scale 100%)
# Chay calibrate.py de chinh lai cho may cua ban
_DEFAULT = {
    "board": {"top": 130, "left": 483, "width": 318, "height": 634},
    "hold":  {"top": 130, "left": 335, "width": 115, "height": 115},
    "next":  [
        {"top": 145, "left": 810, "width": 115, "height": 90},
        {"top": 250, "left": 810, "width": 115, "height": 90},
        {"top": 355, "left": 810, "width": 115, "height": 90},
    ]
}

def _load():
    if os.path.exists(CALIB_FILE):
        try:
            with open(CALIB_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return _DEFAULT

_cfg = _load()
MONITOR_REGION = _cfg["board"]
HOLD_REGION    = _cfg["hold"]
NEXT_REGIONS   = _cfg["next"]
CURRENT_REGION = HOLD_REGION

# Nguong detect block (S channel HSV)
SAT_THRESH = 55
VAL_THRESH = 50
BLOCK_RATIO = 0.20  # >= 20% pixel co mau thi o do la block


def grab(region):
    """Chup vung man hinh -> numpy BGR uint8"""
    with mss.mss() as sct:
        raw = sct.grab(region)
        return np.array(raw, dtype=np.uint8)[:, :, :3]


def to_hsv(bgr):
    """BGR -> HSV nhanh bang numpy (khong can opencv)"""
    b = bgr[:,:,0].astype(np.float32) / 255.0
    g = bgr[:,:,1].astype(np.float32) / 255.0
    r = bgr[:,:,2].astype(np.float32) / 255.0
    v = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    s_range = v - minc
    # Saturation
    s = np.where(v > 0, s_range / (v + 1e-8), 0.0)
    # Hue
    h = np.zeros_like(v)
    mask_r = (v == r) & (s_range > 0)
    mask_g = (v == g) & (s_range > 0)
    mask_b = (v == b) & (s_range > 0)
    h[mask_r] = (60.0 * ((g[mask_r] - b[mask_r]) / (s_range[mask_r] + 1e-8))) % 360.0
    h[mask_g] = 60.0 * ((b[mask_g] - r[mask_g]) / (s_range[mask_g] + 1e-8)) + 120.0
    h[mask_b] = 60.0 * ((r[mask_b] - g[mask_b]) / (s_range[mask_b] + 1e-8)) + 240.0
    h = h % 360.0
    # Scale sang 0-255
    H = (h / 2.0).astype(np.uint8)
    S = (s * 255).astype(np.uint8)
    V = (v * 255).astype(np.uint8)
    return np.stack([H, S, V], axis=2)


def is_cell_block(hsv_cell):
    """True neu o nay co block (du nhieu pixel co mau)"""
    s = hsv_cell[:,:,1].astype(float)
    v = hsv_cell[:,:,2].astype(float)
    colored = np.sum((s > SAT_THRESH) & (v > VAL_THRESH))
    total = hsv_cell.shape[0] * hsv_cell.shape[1]
    if total == 0:
        return False
    return (colored / total) >= BLOCK_RATIO


def extract_board_matrix():
    """
    Quet board 10x20 -> matrix[row][col]: True=block, False=trong.
    Su dung HSV saturation de phan biet block vs nen toi.
    """
    img = grab(MONITOR_REGION)
    hsv = to_hsv(img)
    h_img, w_img = hsv.shape[:2]
    cell_h = h_img / BOARD_HEIGHT
    cell_w = w_img / BOARD_WIDTH
    matrix = []
    for row in range(BOARD_HEIGHT):
        row_data = []
        for col in range(BOARD_WIDTH):
            y1 = int(row * cell_h + cell_h * 0.15)
            y2 = int(row * cell_h + cell_h * 0.85)
            x1 = int(col * cell_w + cell_w * 0.15)
            x2 = int(col * cell_w + cell_w * 0.85)
            cell = hsv[y1:y2, x1:x2]
            row_data.append(is_cell_block(cell) if cell.size > 0 else False)
        matrix.append(row_data)
    return matrix


# ===========================================================
# NHAN DIEN PIECE TU MAU TROI NOI TRONG VUNG
# Dung H channel de phan loai mau
# ===========================================================
# Mau H (OpenCV scale 0-179) cua tung piece Tetr.io
# (khoang rong +/-15 de chiu duoc bien dong man hinh)
PIECE_HUE = {
    "I": (85,  105),   # Cyan ~90
    "O": (22,   35),   # Yellow ~28
    "T": (128, 155),   # Purple/Magenta ~145
    "S": (55,   85),   # Green ~65
    "Z": (0,    12),   # Red low
    "Z_": (168, 179),  # Red high
    "J": (105, 128),   # Blue ~115
    "L": (10,   22),   # Orange ~15
}


def classify_hue(hsv_img):
    """
    Lay mau H troi noi nhat trong anh HSV.
    Tra ve ten piece hoac None.
    """
    S = hsv_img[:,:,1].astype(float)
    V = hsv_img[:,:,2].astype(float)
    H = hsv_img[:,:,0].astype(float)

    # Chi xet pixel co mau ro net
    mask = (S > 80) & (V > 60)
    if np.sum(mask) < 8:
        return None

    best = None
    best_cnt = 0
    for piece, (h_lo, h_hi) in PIECE_HUE.items():
        if h_lo <= h_hi:
            m = mask & (H >= h_lo) & (H <= h_hi)
        else:
            m = mask & ((H >= h_lo) | (H <= h_hi))
        cnt = int(np.sum(m))
        if cnt > best_cnt:
            best_cnt = cnt
            best = piece

    if best_cnt < 6:
        return None
    # Xoa suffix phan biet Z/Z_
    return best.rstrip("_")


def get_piece_from_region(region):
    img = grab(region)
    # Cat bot vien 12%
    h, w = img.shape[:2]
    crop = img[int(h*0.12):int(h*0.88), int(w*0.12):int(w*0.88)]
    if crop.size == 0:
        return None
    hsv = to_hsv(crop)
    return classify_hue(hsv)


def get_current_piece():
    """
    Lay piece hien tai.
    Thu tu: hold region -> 3 hang dau board.
    """
    p = get_piece_from_region(HOLD_REGION)
    if p:
        return p
    # Fallback: quet 3 hang dau cua board
    img = grab(MONITOR_REGION)
    h, w = img.shape[:2]
    top_strip = img[0:int(h * 0.18), :]
    if top_strip.size == 0:
        return None
    return classify_hue(to_hsv(top_strip))


def get_next_pieces():
    return [get_piece_from_region(r) for r in NEXT_REGIONS]


def get_board_max_height(matrix):
    for row in range(BOARD_HEIGHT):
        if any(matrix[row]):
            return BOARD_HEIGHT - row
    return 0


def get_column_heights(matrix):
    heights = []
    for col in range(BOARD_WIDTH):
        h = 0
        for row in range(BOARD_HEIGHT):
            if matrix[row][col]:
                h = BOARD_HEIGHT - row
                break
        heights.append(h)
    return heights


def detect_piece_by_diff(prev_matrix, curr_matrix):
    """
    NHAN DIEN PIECE BANG BOARD DIFF.
    So sanh board cu va moi:
    - Cac o moi xuat hien o hang 0-3 la cells cua piece moi.
    - Dem cac o moi va suy ra hinh dang piece.
    Tra ve ten piece hoac None.
    """
    if prev_matrix is None:
        return None
    new_cells = []
    for row in range(4):  # Chi xet 4 hang dau
        for col in range(BOARD_WIDTH):
            if curr_matrix[row][col] and not prev_matrix[row][col]:
                new_cells.append((row, col))
    if len(new_cells) < 2:
        return None
    return guess_piece_from_cells(new_cells)


def guess_piece_from_cells(cells):
    """
    Doan ten piece dua tren cac o vua xuat hien.
    """
    if not cells:
        return None
    rows = [c[0] for c in cells]
    cols = [c[1] for c in cells]
    n = len(cells)
    row_span = max(rows) - min(rows) + 1
    col_span = max(cols) - min(cols) + 1
    # I: 4 o tren 1 hang hoac 1 cot
    if n == 4:
        if row_span == 1 and col_span == 4:
            return "I"
        if row_span == 4 and col_span == 1:
            return "I"
        # O: 2x2
        if row_span == 2 and col_span == 2:
            return "O"
        # Cac piece 3 o rong/cao
        if col_span == 3:
            # T, S, Z, J, L
            sorted_cells = sorted(cells)
            if sorted_cells[0][0] == sorted_cells[1][0] == sorted_cells[2][0]:
                # 3 o hang dau, 1 o hang 2
                mid_col = sorted(cols)[1]
                extra_col = sorted_cells[3][1]
                if extra_col == mid_col:
                    return "T"
                if extra_col < mid_col:
                    return "J"
                return "L"
            if sorted_cells[0][0] == sorted_cells[1][0]:
                # 2 o hang dau va 2 o hang 2
                return "S"  # hoac Z
    return None  # Khong xac dinh duoc


# Bo nho board truoc de dung diff
_prev_board = None


def get_current_piece_smart():
    """
    Phuong phap ket hop:
    1. Thu nhan dien qua mau (nhanh)
    2. Neu khong duoc, dung board diff
    """
    global _prev_board
    # Thu nhan dien bang mau truoc
    piece = get_current_piece()
    if piece:
        return piece
    # Neu khong co mau, dung diff
    curr = extract_board_matrix()
    p = detect_piece_by_diff(_prev_board, curr)
    _prev_board = curr
    return p
