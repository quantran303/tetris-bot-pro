import mss
import numpy as np
import os
import json

BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# ===========================================================
# FILE LUU CAU HINH - tu dong luu sau khi calibrate
# ===========================================================
CALIB_FILE = "calibration.json"

# ===========================================================
# TOA DO MAC DINH - Tetr.io Zen mode 1920x1080, scale 100%
# Chay calibrate.py de tu dong tim toa do chinh xac
# ===========================================================
_DEFAULT_CONFIG = {
    "board": {"top": 130, "left": 483, "width": 318, "height": 634},
    "hold":  {"top": 155, "left": 335, "width": 110, "height": 100},
    "next": [
        {"top": 165, "left": 810, "width": 110, "height": 80},
        {"top": 260, "left": 810, "width": 110, "height": 80},
        {"top": 355, "left": 810, "width": 110, "height": 80},
    ]
}

def _load_config():
    if os.path.exists(CALIB_FILE):
        try:
            with open(CALIB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return _DEFAULT_CONFIG

_cfg = _load_config()
MONITOR_REGION = _cfg["board"]
HOLD_REGION    = _cfg["hold"]
NEXT_REGIONS   = _cfg["next"]
# alias cho compatibility
CURRENT_REGION = HOLD_REGION

# ===========================================================
# MAU HSV CUA 7 PIECES TETR.IO
# Dung HSV de khong bi anh huong boi do sang man hinh
# H: 0-179, S: 0-255, V: 0-255
# ===========================================================
PIECE_HSV = {
    #  name  H_min H_max  S_min  V_min
    "I":  (85,  105, 150, 100),   # Cyan
    "O":  (20,   35, 150, 150),   # Yellow
    "T":  (130, 155, 100,  80),   # Purple/Magenta
    "S":  (50,   80, 120, 100),   # Green
    "Z":  (0,    10, 150,  80),   # Red (low hue)
    "Z2": (170, 179, 150,  80),   # Red (high hue wrap)
    "J":  (105, 130, 150,  80),   # Blue
    "L":  (10,   20, 150, 100),   # Orange
}

# Nguong phat hien block tren board (saturation)
SATURATION_THRESHOLD = 60  # pixel voi S > nay la block
BLOCK_PIXEL_RATIO    = 0.25  # it nhat 25% pixel la block thi o do la block


def capture_region(region):
    """Chup vung man hinh, tra ve numpy array BGR"""
    with mss.mss() as sct:
        img = sct.grab(region)
        arr = np.array(img, dtype=np.uint8)
        return arr[:, :, :3]  # BGRA -> BGR (bo alpha)


def bgr_to_hsv_single(b, g, r):
    """Chuyen 1 pixel BGR sang HSV (H:0-179, S:0-255, V:0-255)"""
    b, g, r = b/255.0, g/255.0, r/255.0
    v = max(b, g, r)
    s_range = v - min(b, g, r)
    if v == 0:
        return 0, 0, 0
    s = s_range / v
    if s_range == 0:
        h = 0
    elif v == r:
        h = (60 * ((g - b) / s_range)) % 360
    elif v == g:
        h = 60 * ((b - r) / s_range) + 120
    else:
        h = 60 * ((r - g) / s_range) + 240
    if h < 0:
        h += 360
    return int(h / 2), int(s * 255), int(v * 255)  # scale H to 0-179


def img_to_hsv(bgr_img):
    """Chuyen anh BGR sang HSV bang numpy"""
    try:
        import cv2
        return cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
    except ImportError:
        pass
    # Fallback: chuyen tung pixel
    h_img = np.zeros_like(bgr_img)
    for y in range(bgr_img.shape[0]):
        for x in range(bgr_img.shape[1]):
            b, g, r = bgr_img[y, x]
            h_img[y, x] = bgr_to_hsv_single(int(b), int(g), int(r))
    return h_img


def classify_piece_from_hsv(hsv_img):
    """
    Xac dinh loai piece tu anh HSV.
    Tim mau chiem nhieu pixel nhat.
    """
    h = hsv_img[:, :, 0].astype(float)
    s = hsv_img[:, :, 1].astype(float)
    v = hsv_img[:, :, 2].astype(float)

    # Chi xet pixel co mau (S cao, V cao)
    mask_colored = (s > 80) & (v > 60)
    if np.sum(mask_colored) < 5:
        return None

    h_colored = h[mask_colored]

    best_piece = None
    best_count = 0

    for piece, params in PIECE_HSV.items():
        h_min, h_max, s_min, v_min = params
        name = piece.rstrip("2")
        mask_piece = (s > s_min) & (v > v_min)
        if h_min <= h_max:
            mask_piece &= (h >= h_min) & (h <= h_max)
        else:  # wrap-around (Red)
            mask_piece &= (h >= h_min) | (h <= h_max)
        count = int(np.sum(mask_piece))
        if count > best_count:
            best_count = count
            best_piece = name

    total_pixels = bgr_img_area(hsv_img)
    if best_count < max(3, total_pixels * 0.05):
        return None
    return best_piece


def bgr_img_area(img):
    return img.shape[0] * img.shape[1]


def get_piece_from_region(region):
    """Lay piece tu mot vung man hinh"""
    img = capture_region(region)
    # Cat vien ngoai 15%
    h, w = img.shape[:2]
    img = img[int(h*0.15):int(h*0.85), int(w*0.1):int(w*0.9)]
    if img.size == 0:
        return None
    hsv = img_to_hsv(img)
    return classify_piece_from_hsv(hsv)


def get_current_piece():
    """Lay piece hien tai tu HOLD_REGION"""
    # Thu HOLD truoc
    piece = get_piece_from_region(HOLD_REGION)
    if piece:
        return piece
    # Fallback: doc tu hang dau board (piece dang roi luon o hang 0-3)
    return get_piece_from_board_top()


def get_piece_from_board_top():
    """
    Fallback: xac dinh piece dang roi bang cach quet
    3 hang dau board va lay mau chiem nhieu nhat.
    """
    img = capture_region(MONITOR_REGION)
    h, w = img.shape[:2]
    # Lay 20% dau cua board (hang 0-3)
    top_region = img[0:int(h*0.2), :]
    if top_region.size == 0:
        return None
    hsv = img_to_hsv(top_region)
    return classify_piece_from_hsv(hsv)


def get_next_pieces():
    """Lay danh sach 3 next pieces"""
    return [get_piece_from_region(r) for r in NEXT_REGIONS]


def extract_board_matrix():
    """
    Quet board 10x20.
    Dung saturation: pixel S > threshold la block.
    Tra ve matrix[row][col]: True=block, False=trong.
    """
    img = capture_region(MONITOR_REGION)
    hsv = img_to_hsv(img)
    h_img, w_img = hsv.shape[:2]
    cell_h = h_img / BOARD_HEIGHT
    cell_w = w_img / BOARD_WIDTH

    matrix = []
    for row in range(BOARD_HEIGHT):
        row_data = []
        for col in range(BOARD_WIDTH):
            y1 = int(row * cell_h + cell_h * 0.2)
            y2 = int(row * cell_h + cell_h * 0.8)
            x1 = int(col * cell_w + cell_w * 0.2)
            x2 = int(col * cell_w + cell_w * 0.8)
            cell = hsv[y1:y2, x1:x2]
            if cell.size == 0:
                row_data.append(False)
                continue
            s_vals = cell[:, :, 1].astype(float)
            v_vals = cell[:, :, 2].astype(float)
            colored = np.sum((s_vals > SATURATION_THRESHOLD) & (v_vals > 50))
            total = cell.shape[0] * cell.shape[1]
            row_data.append(colored / max(total, 1) >= BLOCK_PIXEL_RATIO)
        matrix.append(row_data)
    return matrix


def get_board_max_height(matrix):
    """Tra ve chieu cao thuc te (0 neu trong)"""
    for row in range(BOARD_HEIGHT):
        if any(matrix[row]):
            return BOARD_HEIGHT - row
    return 0


def get_column_heights(matrix):
    """Tra ve chieu cao tung cot"""
    heights = []
    for col in range(BOARD_WIDTH):
        height = 0
        for row in range(BOARD_HEIGHT):
            if matrix[row][col]:
                height = BOARD_HEIGHT - row
                break
        heights.append(height)
    return heights


def average_color_rgb(img):
    """Compat: Tra ve (R,G,B) trung binh (BGR input)"""
    b = float(np.mean(img[:, :, 0]))
    g = float(np.mean(img[:, :, 1]))
    r = float(np.mean(img[:, :, 2]))
    return r, g, b


def is_colored_block(r, g, b):
    """Compat: kiem tra block theo RGB"""
    brightness = (r + g + b) / 3.0
    if brightness < 60:
        return False
    return (max(r, g, b) - min(r, g, b)) >= 45
