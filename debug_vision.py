"""
debug_vision.py - Cong cu debug de kiem tra vision co hoat dong dung khong

Chay: python debug_vision.py

Se in ra board, current piece, next piece moi 2 giay.
Nhin vao terminal de kiem tra:
- Board co dung cau truc khong (# = co khoi, . = rong)
- Piece co duoc nhan dien dung khong
"""
import time
import os
import json
import numpy as np
from mss import mss

from vision import get_board, get_current_piece, get_next_piece, print_board, get_calib, simplified, grab

def test_once():
    print('\n' + '='*40)
    print(f'Time: {time.strftime("%H:%M:%S")}')
    print('='*40)

    # --- Doc board ---
    board = get_board()
    if board is None:
        print('[DEBUG] FAIL: get_board() tra ve None')
        print('[DEBUG] Kiem tra: tetr.io co dang mo khong? calibration.json co dung khong?')
        return

    # In board ra
    filled = int(board.sum())
    print(f'[DEBUG] Board ({filled} cells filled):')
    print_board(board)

    # In chieu cao tung cot
    heights = []
    for c in range(10):
        h = 0
        for r in range(20):
            if board[r][c]:
                h = 20 - r
                break
        heights.append(h)
    print(f'[DEBUG] Col heights: {heights}')
    print(f'[DEBUG] Max height: {max(heights)}')

    # --- Nhan dien current piece ---
    piece = get_current_piece()
    print(f'[DEBUG] Current piece: {piece}')

    # --- Nhan dien next piece ---
    nxt = get_next_piece()
    print(f'[DEBUG] Next piece: {nxt}')

    if piece is None:
        print('[DEBUG] CANH BAO: Khong nhan dien duoc current piece!')
        print('[DEBUG] Nguyen nhan co the:')
        print('  1. Spawn zone sai - kiem tra calib board region')
        print('  2. Nguong mau sai - piece co mau khac voi PIECE_COLORS_RGB')
        print('  3. Piece chua xuat hien (dang trong animation)')

def diagnose_color():
    """
    In mau trung binh cua vung spawn de so sanh voi PIECE_COLORS_RGB.
    Dung khi piece khong duoc nhan dien.
    """
    calib   = get_calib()
    pixels  = grab(calib['board'])
    H, W    = pixels.shape[:2]
    cell_h  = H // 20
    cell_w  = W // 10

    print('\n[DIAG] Mau pixel o vung spawn (4 hang dau, cot 3-7):')
    for row in range(4):
        for col in range(3, 7):
            cy = int((row + 0.5) * cell_h)
            cx = int((col + 0.5) * cell_w)
            px = pixels[cy, cx, :3]
            print(f'  Cell({row},{col}): BGR=({px[0]},{px[1]},{px[2]})  RGB=({px[2]},{px[1]},{px[0]})')

def main():
    print('Tetris Bot - Debug Vision Tool')
    print('Nhan Ctrl+C de dung\n')

    # Kiem tra calibration
    if not os.path.exists('calibration.json'):
        print('[DEBUG] CANH BAO: Khong co calibration.json!')
        print('[DEBUG] Chay python calibrate.py truoc!')
        print('[DEBUG] Dang dung gia tri mac dinh...')
    else:
        with open('calibration.json') as f:
            calib = json.load(f)
        b = calib['board']
        print(f'[DEBUG] Board region: top={b["top"]} left={b["left"]} w={b["width"]} h={b["height"]}')

    print('\nBat dau doc board... (switch sang tetr.io ngay bay gio)')
    time.sleep(3)

    try:
        i = 0
        while True:
            test_once()
            if i == 0:
                diagnose_color()  # chi chay lan dau de debug mau
            i += 1
            print('\n[DEBUG] Doi 2 giay...')
            time.sleep(2)
    except KeyboardInterrupt:
        print('\n[DEBUG] Da dung.')

if __name__ == '__main__':
    main()
