import mss
import numpy as np

BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# Toa do do tu Tetr.io Zen mode (1328x864)
# Neu man hinh khac, chay test_color.py de chinh lai
MONITOR_REGION = {
    "top":    230,
    "left":   548,
    "width":  252,
    "height": 443,
}

CURRENT_REGION = {
    "top":    188,
    "left":   548,
    "width":  252,
    "height": 60,
}

NEXT_REGIONS = [
    {"top": 210, "left": 812, "width": 108, "height": 72},
    {"top": 285, "left": 812, "width": 108, "height": 72},
    {"top": 360, "left": 812, "width": 108, "height": 72},
    {"top": 435, "left": 812, "width": 108, "height": 72},
    {"top": 510, "left": 812, "width": 108, "height": 72},
]

# Mau BGR thuc te tu Tetr.io
# Neu detect sai, chay test_color.py de lay gia tri thuc roi cap nhat vao day
PIECE_COLORS = {
    'I': (80,  220, 220),
    'J': (210,  80,  60),
    'L': (50,  150, 230),
    'O': (50,  210, 220),
    'S': (80,  210,  80),
    'T': (190,  80, 200),
    'Z': (70,   70, 210),
}

def capture_region(region):
    with mss.mss() as sct:
        frame = np.array(sct.grab(region))
    return frame[:, :, :3]

def is_block(pixel):
    b, g, r = int(pixel[0]), int(pixel[1]), int(pixel[2])
    return (b + g + r) / 3 > 45

def average_color(img):
    h, w, _ = img.shape
    mh = max(1, h // 4)
    mw = max(1, w // 4)
    center = img[mh:h-mh, mw:w-mw]
    if center.size == 0:
        return 0.0, 0.0, 0.0
    return (
        float(center[:, :, 0].mean()),
        float(center[:, :, 1].mean()),
        float(center[:, :, 2].mean()),
    )

def nearest_piece(b, g, r):
    best, best_dist = None, None
    for name, (cb, cg, cr) in PIECE_COLORS.items():
        d = (b - cb)**2 + (g - cg)**2 + (r - cr)**2
        if best_dist is None or d < best_dist:
            best_dist, best = d, name
    return best

def extract_board_matrix():
    img = capture_region(MONITOR_REGION)
    h, w, _ = img.shape
    cell_h = h / BOARD_HEIGHT
    cell_w = w / BOARD_WIDTH
    board = [[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            cy = min(int((y + 0.5) * cell_h), h - 1)
            cx = min(int((x + 0.5) * cell_w), w - 1)
            board[y][x] = 1 if is_block(img[cy, cx]) else 0
    return board

def detect_current_piece():
    img = capture_region(CURRENT_REGION)
    b, g, r = average_color(img)
    if (b + g + r) / 3 < 35:
        return None
    return nearest_piece(b, g, r)

def detect_next_piece(index=0):
    if index >= len(NEXT_REGIONS):
        return None
    img = capture_region(NEXT_REGIONS[index])
    b, g, r = average_color(img)
    if (b + g + r) / 3 < 35:
        return None
    return nearest_piece(b, g, r)

def detect_next_queue(count=5):
    return [detect_next_piece(i) for i in range(count)]

def get_board_max_height(board):
    for row_idx in range(BOARD_HEIGHT):
        if any(board[row_idx]):
            return BOARD_HEIGHT - row_idx
    return 0
