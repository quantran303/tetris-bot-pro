import pyautogui
import time
import random

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

# Thoi gian giua cac phim (giay)
KEY_DELAY  = 0.025   # delay sau moi phim
MOVE_DELAY = 0.04    # delay giua cac lan di chuyen ngang


def focus_game_window(wait=2.5):
    """Cho nguoi dung chuyen sang cua so game"""
    print(f"[controller] Ban co {wait} giay de click vao cua so game...")
    time.sleep(wait)


def _press(key, delay=KEY_DELAY):
    """Bam phim don, co delay"""
    pyautogui.keyDown(key)
    time.sleep(0.015 + random.uniform(0, 0.008))
    pyautogui.keyUp(key)
    time.sleep(delay + random.uniform(0, 0.008))


def rotate(n):
    """Xoay piece n lan (phim Z tren Tetr.io = xoay nguoc, X = xoay xuoi)"""
    for _ in range(n % 4):
        _press('x')  # xoay xuoi kim dong ho


def move_left(n):
    """Di chuyen trai n buoc"""
    for _ in range(n):
        _press('left', delay=MOVE_DELAY)


def move_right(n):
    """Di chuyen phai n buoc"""
    for _ in range(n):
        _press('right', delay=MOVE_DELAY)


def hard_drop():
    """Hard drop (phim Space tren Tetr.io)"""
    _press('space', delay=0.05)


def exec_move(current_col, target_col, rotation=0):
    """
    Thuc hien nuoc di:
      1. Xoay piece 'rotation' lan
      2. Di chuyen ngang tu current_col den target_col
      3. Hard drop

    Args:
      current_col: cot spawn hien tai (mac dinh 4)
      target_col:  cot dich muon dat piece
      rotation:    so lan xoay (0-3)
    """
    # Buoc 1: Xoay
    rotate(rotation)

    # Buoc 2: Di chuyen ngang
    diff = target_col - current_col
    if diff < 0:
        move_left(abs(diff))
    elif diff > 0:
        move_right(diff)

    # Buoc 3: Hard drop
    hard_drop()
