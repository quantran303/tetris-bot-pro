"""
vision.py - Doc man hinh Tetris theo logic mikhail-vlasenko/Tetris-AI

Cach hoat dong:
1. Chup vung board tu man hinh
2. Loc pixel: loai bo qua toi (nen) va qua sang (background)
3. Chia grid 20x10, moi cell vote 9 diem => mean > 0.75 = co khoi
4. Nhan dien mau piece bang colour distance
"""
import os
import json
import numpy as np
from mss import mss

BOARD_W = 10
BOARD_H = 20
CALIB_FILE = 'calibration.json'

# Tetr.io piece colours (RGB)
# Thu tu: I, O, T, S, Z, J, L
PIECE_COLORS_RGB = [
    [49,  206, 209],  # I  - cyan
    [218, 176,  26],  # O  - yellow
    [175,  41, 138],  # T  - purple
    [ 99, 178,  37],  # S  - green
    [215,  15,  55],  # Z  - red
    [ 24,  67, 212],  # J  - blue
    [225, 133,  25],  # L  - orange
]
PIECE_NAMES = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']

# Nguong loc pixel (BGR)
# Pixel qua toi hoac qua sang => khong phai piece
DARK_BOUNDARY = [90, 70, 60]   # BGR lower bound - qua toi => background
BRIGHT_BOUND  = 200             # Gia tri > nay o ca 3 kenh => qua sang

# Default region cho 1920x1080 Chrome fullscreen
_DEFAULT_CALIB = {
    'board': {'top': 135, 'left': 483, 'width': 316, 'height': 632},
    'next':  [{'top': 148, 'left': 810, 'width': 108, 'height': 80}],
    'hold':  {'top': 148, 'left': 340, 'width': 108, 'height': 80},
}

_screen = mss()
_calib  = None

def get_calib():
    global _calib
    if _calib is None:
        if os.path.exists(CALIB_FILE):
            with open(CALIB_FILE) as f:
                _calib = json.load(f)
        else:
            _calib = _DEFAULT_CALIB
    return _calib

def grab(region: dict) -> np.ndarray:
    """Chup man hinh va tra ve mang numpy HxWx3 (BGR)."""
    img = _screen.grab(region)
    arr = np.array(img)[:, :, :3]  # BGRA -> BGR
    return arr

# ---------------------------------------------------------------------------
# Buoc 1: Simplified pixels (logic tu scan_field.py)
# ---------------------------------------------------------------------------

def simplified(pixels: np.ndarray) -> np.ndarray:
    """
    Tao mang nhi phan HxW: 1=co piece, 0=rong.
    Loai bo pixel qua toi (nen den) va qua sang (vien grid).
    (Dich tu scan_field.simplified() cua mikhail-vlasenko)
    """
    b, g, r = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]

    # Too dark => background
    dark = ((b < DARK_BOUNDARY[0]) & (g < DARK_BOUNDARY[1]) & (r < DARK_BOUNDARY[2])).astype(int)

    # Too bright => grid line / UI
    white = ((b > BRIGHT_BOUND) & (g > BRIGHT_BOUND) & (r > BRIGHT_BOUND)).astype(int)

    excluded = dark + white
    field = 1 - np.clip(excluded, 0, 1)
    return field

# ---------------------------------------------------------------------------
# Buoc 2: Tao grid 20x10 bang vote 9 diem quanh tam cell
# ---------------------------------------------------------------------------

def pixels_to_grid(field_pixels: np.ndarray) -> np.ndarray:
    """
    Chia anh da loc thanh grid 20x10.
    Moi cell vote 9 diem (3x3 offset quanh tam cell).
    mean > 0.75 => co piece.
    (Logic tu get_field() cua mikhail-vlasenko)
    Returns: numpy array shape (20, 10) voi 0/1
    """
    H, W = field_pixels.shape
    cell_size = W // BOARD_W

    v_centers = np.array(
        np.linspace(cell_size // 2, H + cell_size // 2, BOARD_H + 1)[:-1], int)
    h_centers = np.array(
        np.linspace(cell_size // 2, W + cell_size // 2, BOARD_W + 1)[:-1], int)

    # 3x3 offset quanh tam cell
    step = max(1, cell_size // 3)
    offsets = [(-step, -step), (-step, 0), (-step, step),
               (0,    -step), (0,    0), (0,    step),
               (step,  -step), (step,  0), (step,  step)]

    grid = np.zeros((BOARD_H, BOARD_W), dtype=np.float32)
    for i, v in enumerate(v_centers):
        for j, h in enumerate(h_centers):
            votes = []
            for dv, dh in offsets:
                rv = np.clip(v + dv, 0, H - 1)
                rh = np.clip(h + dh, 0, W - 1)
                votes.append(field_pixels[rv, rh])
            grid[i, j] = 1 if np.mean(votes) > 0.75 else 0
    return grid.astype(int)

# ---------------------------------------------------------------------------
# Buoc 3: Doc board chinh
# ---------------------------------------------------------------------------

def get_board() -> np.ndarray:
    """
    Chup board va tra ve grid 20x10 (numpy int array).
    Row 0 = tren cung, Row 19 = duoi cung.
    """
    calib  = get_calib()
    pixels = grab(calib['board'])
    simple = simplified(pixels)
    grid   = pixels_to_grid(simple)
    return grid

# ---------------------------------------------------------------------------
# Buoc 4: Nhan dien mau piece
# ---------------------------------------------------------------------------

def cmp_pixel(pixel_bgr, color_rgb):
    """Tinh khoang cach mau giua pixel BGR va color RGB."""
    return (abs(int(pixel_bgr[2]) - color_rgb[0]) +
            abs(int(pixel_bgr[1]) - color_rgb[1]) +
            abs(int(pixel_bgr[0]) - color_rgb[2]))

def get_piece_from_region(region: dict):
    """
    Nhan dien piece trong vung anh (next/hold panel).
    Lay mau pixel noi bat nhat, so sanh voi bang mau.
    Returns: chu cai piece ('I','O','T','S','Z','J','L') hoac None
    """
    pixels = grab(region)
    H, W   = pixels.shape[:2]
    simple = simplified(pixels)

    # Lay tat ca pixel duoc danh la piece
    mask = simple > 0
    if not np.any(mask):
        return None

    piece_pixels = pixels[mask]  # Mx3 BGR
    if len(piece_pixels) == 0:
        return None

    # Lay mau trung binh cua tat ca pixel piece
    avg_bgr = piece_pixels.mean(axis=0)

    # Tim piece co mau gan nhat
    best_idx  = -1
    best_dist = 9999
    for idx, color_rgb in enumerate(PIECE_COLORS_RGB):
        d = cmp_pixel(avg_bgr, color_rgb)
        if d < best_dist:
            best_dist = d
            best_idx  = idx

    if best_dist > 100:
        return None
    return PIECE_NAMES[best_idx]

def get_next_piece():
    """Tra ve ten piece tiep theo (str) hoac None."""
    calib = get_calib()
    nexts = calib.get('next', [])
    if not nexts:
        return None
    return get_piece_from_region(nexts[0])

def get_hold_piece():
    """Tra ve ten piece dang giu (str) hoac None."""
    calib = get_calib()
    hold  = calib.get('hold')
    if not hold:
        return None
    return get_piece_from_region(hold)

# ---------------------------------------------------------------------------
# Buoc 5: Nhan dien piece hien tai dang roi (spawn zone)
# Logic: scan 4 hang dau cua board, vote piece noi bat nhat
# ---------------------------------------------------------------------------

def get_current_piece(board: np.ndarray = None):
    """
    Nhan dien piece hien tai bang cach lay anh vung spawn (4 hang dau, cot 2-7)
    tu board thuc te tren man hinh, roi phan tich mau.
    """
    calib   = get_calib()
    pixels  = grab(calib['board'])   # anh day du cua board
    H, W    = pixels.shape[:2]
    cell_h  = H // BOARD_H
    cell_w  = W // BOARD_W

    # Vung spawn: 4 hang dau, cot 2->7 (0-indexed)
    top    = 0
    bottom = 4 * cell_h
    left   = 2 * cell_w
    right  = 8 * cell_w
    spawn_img = pixels[top:bottom, left:right]

    return get_piece_from_region_img(spawn_img)

def get_piece_from_region_img(img: np.ndarray):
    """Nhan dien piece tu anh numpy (HxWx3 BGR)."""
    simple = simplified(img)
    mask   = simple > 0
    if not np.any(mask):
        return None
    piece_pixels = img[mask]
    if len(piece_pixels) < 4:
        return None
    avg_bgr = piece_pixels.mean(axis=0)
    best_idx  = -1
    best_dist = 9999
    for idx, color_rgb in enumerate(PIECE_COLORS_RGB):
        d = cmp_pixel(avg_bgr, color_rgb)
        if d < best_dist:
            best_dist = d
            best_idx  = idx
    if best_dist > 100:
        return None
    return PIECE_NAMES[best_idx]

# ---------------------------------------------------------------------------
# Utility: in board ra terminal (de debug)
# ---------------------------------------------------------------------------

def print_board(board: np.ndarray):
    for row in board:
        print(''.join(['#' if c else '.' for c in row]))
