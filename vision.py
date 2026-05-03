import mss
import numpy as np
import os
import json
import time

BOARD_WIDTH  = 10
BOARD_HEIGHT = 20
CALIB_FILE   = "calibration.json"

# Default screen regions for 1920x1080 fullscreen Chrome
# Run calibrate.py to auto-detect for your screen
_DEFAULT = {
    "board": {"top": 130, "left": 483, "width": 318, "height": 634},
    "hold":  {"top": 130, "left": 335, "width": 115, "height": 115},
    "next": [
        {"top": 145, "left": 810, "width": 115, "height": 90},
        {"top": 250, "left": 810, "width": 115, "height": 90},
        {"top": 355, "left": 810, "width": 115, "height": 90},
    ]
}

# ---------------------------------------------------------------------------
# Calibration helpers
# ---------------------------------------------------------------------------

def load_calib():
    if os.path.exists(CALIB_FILE):
        with open(CALIB_FILE) as f:
            return json.load(f)
    return _DEFAULT

_CALIB = None

def get_calib():
    global _CALIB
    if _CALIB is None:
        _CALIB = load_calib()
    return _CALIB

# ---------------------------------------------------------------------------
# Screenshot helpers
# ---------------------------------------------------------------------------

def grab_region(region):
    """Capture screen region and return as numpy array (H x W x 3 BGR)."""
    with mss.mss() as sct:
        img = sct.grab(region)
    return np.array(img)[:, :, :3]  # drop alpha

# ---------------------------------------------------------------------------
# Colour-based cell detection
# ---------------------------------------------------------------------------

# Tetr.io piece colours in BGR (approximate midpoints)
# Threshold: if ANY channel difference from background is > COLOUR_THRESH,
# the cell is considered filled.
BG_SAMPLE_ROWS = 2   # top rows of the board are usually empty at game start
COLOUR_THRESH  = 35  # minimum channel deviation from background

def is_block_pixel(pixel_bgr, bg_bgr):
    """Return True if pixel is significantly different from background."""
    return int(np.max(np.abs(pixel_bgr.astype(int) - bg_bgr.astype(int)))) > COLOUR_THRESH

def extract_board_matrix():
    """
    Capture the board region and return a 20x10 binary matrix.
    1 = filled cell, 0 = empty cell.
    """
    calib = get_calib()
    region = calib['board']
    img = grab_region(region)  # H x W x 3

    H, W = img.shape[:2]
    cell_h = H / BOARD_HEIGHT
    cell_w = W / BOARD_WIDTH

    # Estimate background colour from first empty rows
    bg_samples = []
    for r in range(BG_SAMPLE_ROWS):
        for c in range(BOARD_WIDTH):
            cy = int((r + 0.5) * cell_h)
            cx = int((c + 0.5) * cell_w)
            bg_samples.append(img[cy, cx, :3])
    bg_bgr = np.median(bg_samples, axis=0).astype(np.uint8)

    matrix = []
    for r in range(BOARD_HEIGHT):
        row = []
        for c in range(BOARD_WIDTH):
            cy = int((r + 0.5) * cell_h)
            cx = int((c + 0.5) * cell_w)
            pixel = img[cy, cx, :3]
            row.append(1 if is_block_pixel(pixel, bg_bgr) else 0)
        matrix.append(row)
    return matrix

def get_board_max_height(board):
    """Return the maximum filled height (rows from bottom) of the board."""
    for r in range(BOARD_HEIGHT):
        if any(board[r]):
            return BOARD_HEIGHT - r
    return 0

def get_column_heights(board):
    heights = []
    for c in range(BOARD_WIDTH):
        h = 0
        for r in range(BOARD_HEIGHT):
            if board[r][c]:
                h = BOARD_HEIGHT - r
                break
        heights.append(h)
    return heights

# ---------------------------------------------------------------------------
# Piece colour signatures (BGR, approximate)
# ---------------------------------------------------------------------------

PIECE_COLOURS = {
    'I': np.array([220, 220,  50]),  # cyan  (BGR)
    'O': np.array([ 50, 220, 220]),  # yellow
    'T': np.array([220,  50, 220]),  # purple
    'S': np.array([ 50, 220,  50]),  # green
    'Z': np.array([ 50,  50, 220]),  # red
    'J': np.array([220, 100,  50]),  # blue
    'L': np.array([ 50, 150, 220]),  # orange
}

def classify_colour(pixel_bgr):
    """Return the piece letter whose colour is closest to pixel_bgr."""
    pixel = pixel_bgr.astype(float)
    best_piece = None
    best_dist  = 1e9
    for piece, colour in PIECE_COLOURS.items():
        dist = float(np.linalg.norm(pixel - colour.astype(float)))
        if dist < best_dist:
            best_dist  = dist
            best_piece = piece
    return best_piece if best_dist < 120 else None

def _dominant_piece_in_region(img):
    """Return the piece type that appears most in a small preview image."""
    H, W = img.shape[:2]
    calib = get_calib()
    board_region = calib['board']
    # Sample background from board top-left corner
    bg_img = grab_region(board_region)
    bg_bgr = np.median(bg_img[:10, :10, :3].reshape(-1, 3), axis=0).astype(np.uint8)

    votes = {}
    for r in range(0, H, max(1, H // 6)):
        for c in range(0, W, max(1, W // 6)):
            px = img[r, c, :3]
            if not is_block_pixel(px, bg_bgr):
                continue
            piece = classify_colour(px)
            if piece:
                votes[piece] = votes.get(piece, 0) + 1
    if not votes:
        return None
    return max(votes, key=votes.get)

# ---------------------------------------------------------------------------
# Current piece detection (spawn zone = top 4 rows, columns 3-6)
# ---------------------------------------------------------------------------

def get_current_piece_smart():
    """
    Detect the active falling piece by sampling the spawn zone at the top
    of the board (rows 0-3, centre columns 3-6 in 0-indexed).
    Returns piece letter or None.
    """
    calib = get_calib()
    board_r = calib['board']
    img     = grab_region(board_r)
    H, W    = img.shape[:2]
    cell_h  = H / BOARD_HEIGHT
    cell_w  = W / BOARD_WIDTH

    # Sample top 4 rows, columns 2-7
    bg_img = img
    bg_bgr = np.median(img[int(0.5*cell_h): int(1.5*cell_h),
                            int(0.5*cell_w): int(2.5*cell_w), :3].reshape(-1, 3),
                        axis=0).astype(np.uint8)

    votes = {}
    for row in range(4):
        for col in range(2, 8):
            cy = int((row + 0.5) * cell_h)
            cx = int((col + 0.5) * cell_w)
            px = img[cy, cx, :3]
            if not is_block_pixel(px, bg_bgr):
                continue
            piece = classify_colour(px)
            if piece:
                votes[piece] = votes.get(piece, 0) + 1

    if not votes:
        return None
    best = max(votes, key=votes.get)
    return best if votes[best] >= 2 else None

# ---------------------------------------------------------------------------
# Next pieces detection
# ---------------------------------------------------------------------------

def get_next_pieces():
    """Return list of up to 3 next piece letters from the preview panel."""
    calib  = get_calib()
    pieces = []
    for region in calib.get('next', []):
        img = grab_region(region)
        p   = _dominant_piece_in_region(img)
        if p:
            pieces.append(p)
    return pieces

# ---------------------------------------------------------------------------
# Hold piece detection
# ---------------------------------------------------------------------------

def get_hold_piece():
    calib  = get_calib()
    region = calib.get('hold')
    if not region:
        return None
    img = grab_region(region)
    return _dominant_piece_in_region(img)
