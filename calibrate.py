"""
calibrate.py - Tu dong tim vung board Tetris tren man hinh

CAch dung:
  python calibrate.py

Sau khi chay, file calibration.json se duoc tao ra voi toa do chinh xac
cua board, next piece, va hold piece tren man hinh hien tai.

Yeu cau: tetr.io dang mo tren Chrome, o trang thai dang choi (co pieces).
"""
import json
import time
import sys
import numpy as np
from mss import mss

OUTPUT_FILE = 'calibration.json'

# ---------------------------------------------------------------------------
# Chup toan man hinh
# ---------------------------------------------------------------------------

def grab_screen():
    with mss() as sc:
        monitor = sc.monitors[1]  # man hinh chinh
        img = sc.grab(monitor)
        return np.array(img)[:, :, :3], monitor

# ---------------------------------------------------------------------------
# Phat hien board Tetris bang cach tim cac duong doc thang hang
# Board Tetris co ti le cao/rong ~ 2:1 va co khung vien
# ---------------------------------------------------------------------------

def simplified_full(pixels):
    """Loc pixel: loai bo qua toi va qua sang."""
    b, g, r = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]
    dark  = ((b < 90) & (g < 70) & (r < 60)).astype(np.uint8)
    white = ((b > 200) & (g > 200) & (r > 200)).astype(np.uint8)
    excluded = np.clip(dark.astype(int) + white.astype(int), 0, 1).astype(np.uint8)
    return (1 - excluded).astype(np.uint8)

def find_board_auto(screen_img, monitor):
    """
    Tu dong tim board Tetris:
    1. Tim vung co mat do piece cao nhat
    2. Board phai co ti le ~1:2 (rong:cao)
    Tra ve dict {top, left, width, height} hoac None
    """
    H, W = screen_img.shape[:2]
    field = simplified_full(screen_img)

    # Chia man hinh thanh cac block 40x40, dem so pixel piece
    block = 40
    rows = H // block
    cols = W // block
    density = np.zeros((rows, cols))
    for r in range(rows):
        for c in range(cols):
            density[r, c] = field[r*block:(r+1)*block, c*block:(c+1)*block].mean()

    # Tim vung co density cao: board thuc su
    threshold = 0.08
    active = density > threshold

    # Tim bounding box cua vung active
    rows_with_piece = np.where(active.any(axis=1))[0]
    cols_with_piece = np.where(active.any(axis=0))[0]

    if len(rows_with_piece) < 5 or len(cols_with_piece) < 3:
        return None

    # Lay phan chinh giua (loai bo panel next/hold)
    # Board namnchinhla o trung tam man hinh
    mid_col = cols // 2
    # Loc chi lay cac cot gan trung tam
    center_cols = cols_with_piece[
        (cols_with_piece >= mid_col - cols//4) &
        (cols_with_piece <= mid_col + cols//4)
    ]
    if len(center_cols) < 3:
        center_cols = cols_with_piece

    r_min = int(rows_with_piece[0])
    r_max = int(rows_with_piece[-1])
    c_min = int(center_cols[0])
    c_max = int(center_cols[-1])

    # Convert sang pixel
    px_top    = r_min * block
    px_left   = c_min * block
    px_height = (r_max - r_min + 1) * block
    px_width  = (c_max - c_min + 1) * block

    # Board Tetris phai co ti le ~1:2 (rong:cao)
    ratio = px_height / px_width if px_width > 0 else 0
    if ratio < 1.5 or ratio > 2.8:
        # Thu dieu chinh width de co ti le dung
        px_height_target = int(px_width * 2)
        if px_height_target > px_height:
            px_height = px_height_target

    # Dam bao khong vuot qua man hinh
    px_height = min(px_height, H - px_top)
    px_width  = min(px_width, W - px_left)

    # Offset cua monitor
    board = {
        'top':    px_top    + monitor['top'],
        'left':   px_left   + monitor['left'],
        'width':  px_width,
        'height': px_height
    }
    return board

def board_from_known_resolution(monitor, screen_w, screen_h):
    """
    Fallback: tinh toa do dua tren do phan giai man hinh.
    Tetr.io chrome fullscreen co board o giua man hinh.
    """
    # Dua tren 1920x1080 fullscreen
    # Board ~316x632 tai vi tri ~(483, 135)
    scale_x = screen_w / 1920
    scale_y = screen_h / 1080

    board_w = int(316 * scale_x)
    board_h = int(632 * scale_y)
    board_l = int(483 * scale_x) + monitor['left']
    board_t = int(135 * scale_y) + monitor['top']

    return {
        'top': board_t, 'left': board_l,
        'width': board_w, 'height': board_h
    }

def derive_panels(board, monitor, screen_w, screen_h):
    """
    Tu board, suy ra vi tri cac panel next va hold.
    Next o ben phai board, hold o ben trai.
    """
    scale_x = screen_w / 1920
    scale_y = screen_h / 1080

    panel_w = int(108 * scale_x)
    panel_h = int(80  * scale_y)

    # Hold: ben trai board
    hold_left = board['left'] - int(130 * scale_x)
    hold_left = max(0, hold_left)
    hold = {
        'top':   board['top'],
        'left':  hold_left,
        'width': panel_w,
        'height': panel_h
    }

    # Next: ben phai board
    next_left = board['left'] + board['width'] + int(10 * scale_x)
    nexts = []
    for i in range(3):
        nexts.append({
            'top':    board['top'] + i * int(90 * scale_y),
            'left':   next_left,
            'width':  panel_w,
            'height': panel_h
        })

    return hold, nexts

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print('=' * 50)
    print('Tetris Bot - Calibration Tool')
    print('=' * 50)
    print()
    print('Huong dan:')
    print('1. Mo tetr.io tren Chrome, F11 full screen')
    print('2. Bat dau 1 game (can co pieces hien thi tren board)')
    print('3. Nhan Enter khi san sang...')
    input()

    print('[CAL] Chup man hinh sau 3 giay...')
    time.sleep(3)

    screen_img, monitor = grab_screen()
    H, W = screen_img.shape[:2]
    print(f'[CAL] Man hinh: {W}x{H}')

    # Thu tu dong phat hien board
    print('[CAL] Dang tim board tu dong...')
    board = find_board_auto(screen_img, monitor)

    if board:
        ratio = board['height'] / board['width'] if board['width'] else 0
        print(f'[CAL] Tim thay board: {board} (ratio={ratio:.2f})')
        if ratio < 1.5 or ratio > 2.8:
            print('[CAL] Canh bao: Ti le board khong hop le, dung gia tri mac dinh')
            board = None

    if not board:
        print('[CAL] Dung gia tri mac dinh theo do phan giai man hinh...')
        board = board_from_known_resolution(monitor, W, H)
        print(f'[CAL] Board mac dinh: {board}')

    hold, nexts = derive_panels(board, monitor, W, H)

    calib = {
        'board': board,
        'hold':  hold,
        'next':  nexts,
        'screen_size': [W, H]
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(calib, f, indent=2)

    print()
    print(f'[CAL] Da luu calibration vao: {OUTPUT_FILE}')
    print(f'[CAL] Board  : top={board["top"]} left={board["left"]} w={board["width"]} h={board["height"]}')
    print(f'[CAL] Hold   : top={hold["top"]}  left={hold["left"]}  w={hold["width"]} h={hold["height"]}')
    print(f'[CAL] Next[0]: top={nexts[0]["top"]} left={nexts[0]["left"]}')
    print()
    print('[CAL] Kiem tra: chay python debug_vision.py de xem board co duoc nhan dien dung khong')
    print('[CAL] Neu sai, sua tay file calibration.json')

if __name__ == '__main__':
    main()
