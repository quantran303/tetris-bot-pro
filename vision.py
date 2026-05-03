import mss
import numpy as np

BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# ============================================================
# TOA DO VUNG MAN HINH - Tetr.io Zen mode
# Neu bot khong nhan dien dung, chay test_color.py de lay so
# ============================================================
MONITOR_REGION = {
    "top":    230,
    "left":   548,
    "width":  252,
    "height": 443,
}

# Vung hien thi piece dang roi (hold/current piece preview area)
CURRENT_REGION = {
    "top":    188,
    "left":   548,
    "width":  252,
    "height": 50,
}

# Vung 3 next pieces ben phai
NEXT_REGIONS = [
    {"top": 250, "left": 818, "width": 85, "height": 55},
    {"top": 325, "left": 818, "width": 85, "height": 55},
    {"top": 400, "left": 818, "width": 85, "height": 55},
]

# ============================================================
# MAU RGB THUC TE CUA TETR.IO (lay bang test_color.py)
# Format: (R, G, B)  <-- chot la RGB de de doc
# ============================================================
PIECE_COLORS_RGB = {
    "I": (41,  204, 204),   # Cyan
    "O": (218, 170, 0),    # Yellow
    "T": (140, 40,  180),   # Purple
    "S": (50,  200, 50),    # Green
    "Z": (215, 40,  40),    # Red
    "J": (30,  80,  210),   # Blue
    "L": (220, 120, 20),    # Orange
}

# Nguong nhan dien block (do bao nhieu pixel sang/co mau)
BRIGHTNESS_MIN = 60    # Tong R+G+B / 3 phai >= nay
SATURATION_MIN = 45    # Max channel - Min channel phai >= nay
COLOR_MATCH_THRESH = 100  # Khoang cach mau toi da de xem la khop


def capture_region(region):
    """Chup vung man hinh, tra ve numpy array RGB"""
    with mss.mss() as sct:
        img = sct.grab(region)
        # mss tra ve BGRA, chuyen sang RGB
        arr = np.array(img)
        return arr[:, :, 2::-1]  # BGRA -> RGB


def average_color_rgb(img):
    """Tra ve mau trung binh (R, G, B) cua anh"""
    r = float(np.mean(img[:, :, 0]))
    g = float(np.mean(img[:, :, 1]))
    b = float(np.mean(img[:, :, 2]))
    return r, g, b


def is_colored_block(r, g, b):
    """
    Kiem tra mau co phai la block Tetris hay khong.
    Block Tetris luon co mau sac noi bat (cao saturation)
    va do sang trung binh tro len.
    """
    brightness = (r + g + b) / 3.0
    if brightness < BRIGHTNESS_MIN:
        return False
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    saturation = max_c - min_c
    return saturation >= SATURATION_MIN


def color_distance(r1, g1, b1, r2, g2, b2):
    """Khoang cach Euclidean giua 2 mau RGB"""
    return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5


def identify_piece_rgb(r, g, b):
    """
    Xac dinh loai piece tu mau RGB.
    Tra ve ten piece ('I','O','T','S','Z','J','L') hoac None.
    """
    if not is_colored_block(r, g, b):
        return None

    best_piece = None
    best_dist = float('inf')
    for piece, (pr, pg, pb) in PIECE_COLORS_RGB.items():
        dist = color_distance(r, g, b, pr, pg, pb)
        if dist < best_dist:
            best_dist = dist
            best_piece = piece

    if best_dist > COLOR_MATCH_THRESH:
        return None
    return best_piece


def get_current_piece():
    """Lay piece hien tai dang roi"""
    img = capture_region(CURRENT_REGION)
    # Lay vung trung tam tranh vien
    h, w = img.shape[:2]
    cy1, cy2 = int(h*0.2), int(h*0.8)
    cx1, cx2 = int(w*0.1), int(w*0.9)
    center = img[cy1:cy2, cx1:cx2]
    r, g, b = average_color_rgb(center)
    return identify_piece_rgb(r, g, b)


def get_next_pieces():
    """Lay danh sach next pieces (3 pieces)"""
    pieces = []
    for region in NEXT_REGIONS:
        img = capture_region(region)
        h, w = img.shape[:2]
        cy1, cy2 = int(h*0.15), int(h*0.85)
        cx1, cx2 = int(w*0.1), int(w*0.9)
        center = img[cy1:cy2, cx1:cx2]
        r, g, b = average_color_rgb(center)
        piece = identify_piece_rgb(r, g, b)
        pieces.append(piece)
    return pieces


def extract_board_matrix():
    """
    Chup board va chia thanh luoi 10x20.
    Tra ve matrix 20x10: True = o co block, False = o trong.
    Dung phuong phap phan tich saturation tung o.
    """
    img = capture_region(MONITOR_REGION)
    h, w = img.shape[:2]
    cell_h = h / BOARD_HEIGHT
    cell_w = w / BOARD_WIDTH

    matrix = []
    for row in range(BOARD_HEIGHT):
        row_data = []
        for col in range(BOARD_WIDTH):
            # Lay vung 60% trung tam cua o (tranh vien luoi)
            y1 = int(row * cell_h + cell_h * 0.2)
            y2 = int(row * cell_h + cell_h * 0.8)
            x1 = int(col * cell_w + cell_w * 0.2)
            x2 = int(col * cell_w + cell_w * 0.8)
            cell = img[y1:y2, x1:x2]
            if cell.size == 0:
                row_data.append(False)
                continue
            r, g, b = average_color_rgb(cell)
            row_data.append(is_colored_block(r, g, b))
        matrix.append(row_data)
    return matrix


def get_board_max_height(matrix):
    """
    Tinh chieu cao thuc te cua board.
    Tra ve so hang co block tinh tu duoi len.
    Neu board trong hoan toan, tra ve 0.
    """
    for row in range(BOARD_HEIGHT):
        if any(matrix[row]):
            return BOARD_HEIGHT - row
    return 0


def get_column_heights(matrix):
    """Tra ve chieu cao tung cot (list 10 phan tu)"""
    heights = []
    for col in range(BOARD_WIDTH):
        height = 0
        for row in range(BOARD_HEIGHT):
            if matrix[row][col]:
                height = BOARD_HEIGHT - row
                break
        heights.append(height)
    return heights


def debug_colors():
    """
    Ham debug: in mau RGB thuc te cua CURRENT_REGION va NEXT_REGIONS.
    Chay ham nay khi dang co piece de xem mau thuc te.
    """
    print("=" * 50)
    print("DEBUG MAU SAC THUC TE TREN MAN HINH")
    print("=" * 50)

    img = capture_region(CURRENT_REGION)
    h, w = img.shape[:2]
    center = img[int(h*0.2):int(h*0.8), int(w*0.1):int(w*0.9)]
    r, g, b = average_color_rgb(center)
    piece = identify_piece_rgb(r, g, b)
    print(f"CURRENT: R={r:.0f}, G={g:.0f}, B={b:.0f}  -> {piece}")

    for i, region in enumerate(NEXT_REGIONS):
        img = capture_region(region)
        h, w = img.shape[:2]
        center = img[int(h*0.15):int(h*0.85), int(w*0.1):int(w*0.9)]
        r, g, b = average_color_rgb(center)
        piece = identify_piece_rgb(r, g, b)
        print(f"NEXT {i+1}: R={r:.0f}, G={g:.0f}, B={b:.0f}  -> {piece}")

    print("=" * 50)
    print("MAU THAM CHIEU (PIECE_COLORS_RGB):")
    for name, (pr, pg, pb) in PIECE_COLORS_RGB.items():
        print(f"  {name}: R={pr}, G={pg}, B={pb}")
    print("=" * 50)
