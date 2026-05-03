"""
main.py - Vong lap chinh cua Tetris Bot

Thuat toan hoat dong:
1. Chup board => nhan dien cau truc hien tai (20x10 numpy array)
2. Nhan dien piece dang roi (spawn zone)
3. Nhan dien next piece
4. Goi engine_ai.best_move() => (rotation, x_pos)
5. Thuc hien lenh: xoay + di chuyen + hard drop
6. Lap lai

Mo phong y tuong cua mikhail-vlasenko/Tetris-AI nhung chay tren tetr.io
"""
import time
import sys
import os
import numpy as np

from vision import (
    get_board, get_current_piece, get_next_piece,
    print_board, CALIB_FILE, get_calib
)
from engine_ai import best_move, find_roofs
from controller import exec_move, focus_game_window

# Cau hinh vong lap
DELAY_AFTER_MOVE   = 0.12   # giay, cho piece ha xuong sau hard drop
DELAY_WAIT_PIECE   = 0.15   # giay, cho piece moi xuat hien
DELAY_RETRY        = 0.06   # giay, thu lai khi khong nhan dien duoc piece
MAX_RETRY_PIECE    = 20     # so lan thu lai toi da
SCARED_HEIGHT      = 13     # khi max_height > nay => 'scared mode'
DEPTH2_CHOICES     = 5      # so vi tri hang dau xet lookahead

def check_calibration():
    """Kiem tra file calibration ton tai."""
    if not os.path.exists(CALIB_FILE):
        print('[MAIN] CANH BAO: Khong tim thay calibration.json!')
        print('[MAIN] Chay: python calibrate.py truoc khi chay bot.')
        sys.exit(1)

def is_scared(board: np.ndarray) -> bool:
    """Kiem tra xem board co qua cao khong."""
    _, max_h, _, _ = find_roofs(board)
    return max_h >= SCARED_HEIGHT

def wait_for_piece(max_retries=MAX_RETRY_PIECE) -> str:
    """
    Doi cho den khi nhan dien duoc piece dang roi.
    Tra ve ten piece hoac None.
    """
    for i in range(max_retries):
        piece = get_current_piece()
        if piece:
            return piece
        time.sleep(DELAY_RETRY)
    return None

def run_bot():
    print('[MAIN] =====================================')
    print('[MAIN] Tetris Bot Pro - tetr.io')
    print('[MAIN] Dua tren logic mikhail-vlasenko/Tetris-AI')
    print('[MAIN] =====================================')

    check_calibration()

    focus_game_window()
    time.sleep(0.3)

    fail_count = 0
    move_count = 0

    while True:
        # ------- 1. Doc board tu man hinh -------
        board = get_board()
        if board is None:
            print('[MAIN] Khong doc duoc board, thu lai...')
            time.sleep(0.3)
            continue

        scared = is_scared(board)
        if scared:
            print('[MAIN] [SCARED MODE] Board cao > 13!')

        # ------- 2. Nhan dien piece dang roi -------
        current_piece = wait_for_piece()
        if not current_piece:
            print('[MAIN] Khong nhan dien duoc piece, bo qua...')
            fail_count += 1
            if fail_count >= 10:
                print('[MAIN] Qua nhieu lan that bai, kiem tra calibration!')
                print_board(board)
                fail_count = 0
            time.sleep(DELAY_WAIT_PIECE)
            continue

        fail_count = 0

        # ------- 3. Nhan dien next piece -------
        next_piece = get_next_piece()

        # ------- 4. Tinh nuoc di tot nhat -------
        result = best_move(
            board, current_piece, next_piece,
            depth2_choices=DEPTH2_CHOICES,
            scared=scared
        )

        if result is None:
            print(f'[MAIN] Piece={current_piece}: Khong tim duoc nuoc di hop le!')
            time.sleep(DELAY_WAIT_PIECE)
            continue

        rotation, x_pos, score = result
        move_count += 1

        print(f'[MAIN] #{move_count} Piece={current_piece} Next={next_piece} '
              f'Rot={rotation} Col={x_pos} Score={score:.1f} Scared={scared}')

        # ------- 5. Thuc hien nuoc di -------
        exec_move(rotation, x_pos, current_piece)

        # ------- 6. Cho piece ha xuong va piece moi xuat hien -------
        time.sleep(DELAY_AFTER_MOVE)
        time.sleep(DELAY_WAIT_PIECE)

if __name__ == '__main__':
    run_bot()
