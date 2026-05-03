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
    "height": 50,
}

NEXT_REGIONS = [
    {"top": 245, "left": 820, "width": 80, "height": 60},
    {"top": 320, "left": 820, "width": 80, "height": 60},
    {"top": 395, "left": 820, "width": 80, "height": 60},
]

# Mau BGR cua 7 khoi Tetris tren Tetr.io
PIECE_COLORS = {
    "I": (200, 200, 20),   # Cyan
    "O": (20, 200, 200),   # Yellow
    "T": (150, 20, 150),   # Purple
    "S": (20, 180, 20),    # Green
    "Z": (20, 20, 200),    # Red
    "J": (200, 100, 20),   # Blue
    "L": (20, 100, 200),   # Orange
}

COLOR_THRESHOLD = 60   # nguong phan biet block vs nen
BRIGHTNESS_THRESHOLD = 80  # min do sang de tinh la block


def capture_region(region):
    with mss.mss() as sct:
        img = sct.grab(region)
        return np.array(img)[:, :, :3]  # BGR, bo alpha


def average_color(img):
    """Tra ve mau trung binh (B, G, R) cua anh"""
    b = float(np.mean(img[:, :, 0]))
    g = float(np.mean(img[:, :, 1]))
    r = float(np.mean(img[:, :, 2]))
    return b, g, r


def is_block(b, g, r):
    """
    Kiem tra xem mau co phai la block hay khong.
    - Do sang phai > BRIGHTNESS_THRESHOLD
    - It nhat 1 kenh mau phai vuot troi (color saturation)
    """
    brightness = (b + g + r) / 3.0
    if brightness < BRIGHTNESS_THRESHOLD:
        return False
    max_ch = max(b, g, r)
    min_ch = min(b, g, r)
    saturation = max_ch - min_ch
    return saturation > COLOR_THRESHOLD


def extract_board_matrix():
    """
    Chup board va chia thanh luoi 10x20.
    Tra ve matrix 20x10 voi True = o trong, False = o co block.
    Chi dem la block neu ca 2 dieu kien (brightness + saturation) deu dat.
    """
    img = capture_region(MONITOR_REGION)
    h, w = img.shape[:2]
    cell_h = h / BOARD_HEIGHT
    cell_w = w / BOARD_WIDTH

    matrix = []
    for row in range(BOARD_HEIGHT):
        row_data = []
        for col in range(BOARD_WIDTH):
            # Lay vung trung tam cua o (tranh vien)
            y1 = int(row * cell_h + cell_h * 0.2)
            y2 = int(row * cell_h + cell_h * 0.8)
            x1 = int(col * cell_w + cell_w * 0.2)
            x2 = int(col * cell_w + cell_w * 0.8)
            cell = img[y1:y2, x1:x2]
            if cell.size == 0:
                row_data.append(False)
                continue
            b, g, r = average_color(cell)
            row_data.append(is_block(b, g, r))
        matrix.append(row_data)
    return matrix


def identify_piece_from_color(b, g, r):
    """Xac dinh loai piece tu mau BGR"""
    if not is_block(b, g, r):
        return None
    best_piece = None
    best_dist = float('inf')
    for piece, (pb, pg, pr) in PIECE_COLORS.items():
        dist = ((b - pb)**2 + (g - pg)**2 + (r - pr)**2) ** 0.5
        if dist < best_dist:
            best_dist = dist
            best_piece = piece
    if best_dist > 120:
        return None
    return best_piece


def get_current_piece():
    """Lay piece hien tai tu vung CURRENT_REGION"""
    img = capture_region(CURRENT_REGION)
    b, g, r = average_color(img)
    return identify_piece_from_color(b, g, r)


def get_next_pieces():
    """Lay danh sach next pieces"""
    pieces = []
    for region in NEXT_REGIONS:
        img = capture_region(region)
        b, g, r = average_color(img)
        piece = identify_piece_from_color(b, g, r)
        pieces.append(piece)
    return pieces


def get_board_max_height(matrix):
    """
    Tinh chieu cao thuc te cua board dua tren matrix.
    Tra ve so hang tinh tu duoi len co chua block.
    Neu board trong hoan toan, tra ve 0.
    """
    for row in range(BOARD_HEIGHT):
        if any(matrix[row]):
            return BOARD_HEIGHT - row
    return 0


def get_column_heights(matrix):
    """Tra ve chieu cao cua tung cot (10 cot)"""
    heights = []
    for col in range(BOARD_WIDTH):
        height = 0
        for row in range(BOARD_HEIGHT):
            if matrix[row][col]:
                height = BOARD_HEIGHT - row
                break
        heights.append(height)
    return heights
