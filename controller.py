import pyautogui
import time
import random

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

# ============================================================
# PHIM DIEU KHIEN TETR.IO (mac dinh)
# Neu ban doi phim trong Settings -> Controls, chinh lai day
# ============================================================
KEY_ROTATE_CW  = 'up'       # Xoay xuoi (ArrowUp) - mac dinh Tetr.io
KEY_ROTATE_CCW = 'z'        # Xoay nguoc (Z)
KEY_LEFT       = 'left'     # Di trai
KEY_RIGHT      = 'right'    # Di phai  
KEY_SOFT_DROP  = 'down'     # Ha cham
KEY_HARD_DROP  = 'space'    # Ha nhanh
KEY_HOLD       = 'c'        # Giu

# Thoi gian delay (giay)
KEY_DELAY      = 0.030   # delay sau moi phim bam
ROTATE_DELAY   = 0.040   # delay sau khi xoay (de piece kip xoay)
MOVE_DELAY     = 0.040   # delay giua cac buoc di chuyen
DROP_DELAY     = 0.060   # delay sau hard drop


def focus_game_window(wait=2.5):
    """Cho nguoi dung chuyen sang cua so game"""
    print(f"[controller] Ban co {wait:.0f} giay de click vao cua so game...")
    time.sleep(wait)


def _press(key, delay=None):
    """Bam phim don voi delay"""
    if delay is None:
        delay = KEY_DELAY
    pyautogui.keyDown(key)
    time.sleep(0.018 + random.uniform(0, 0.010))
    pyautogui.keyUp(key)
    time.sleep(delay + random.uniform(0, 0.008))


def rotate_cw(n=1):
    """
    Xoay piece n lan theo chieu xuoi kim dong ho.
    Tetr.io: phim ArrowUp hoac X.
    """
    n = n % 4
    for _ in range(n):
        _press(KEY_ROTATE_CW, delay=ROTATE_DELAY)


def rotate_ccw(n=1):
    """
    Xoay piece n lan nguoc chieu kim dong ho.
    Tetr.io: phim Z.
    """
    n = n % 4
    for _ in range(n):
        _press(KEY_ROTATE_CCW, delay=ROTATE_DELAY)


def move_left(n):
    """Di chuyen trai n buoc"""
    for _ in range(int(n)):
        _press(KEY_LEFT, delay=MOVE_DELAY)


def move_right(n):
    """Di chuyen phai n buoc"""
    for _ in range(int(n)):
        _press(KEY_RIGHT, delay=MOVE_DELAY)


def hard_drop():
    """Hard drop - dat piece xuong ngay"""
    _press(KEY_HARD_DROP, delay=DROP_DELAY)


def hold_piece():
    """Giu piece hien tai"""
    _press(KEY_HOLD, delay=KEY_DELAY)


def exec_move(current_col, target_col, rotation=0):
    """
    Thuc hien toan bo 1 nuoc di:
      1. Xoay piece
      2. Di chuyen ngang den cot dich
      3. Hard drop

    Args:
      current_col (int): cot spawn hien tai (0-indexed, mac dinh 4 tren Tetr.io)
      target_col  (int): cot dich dat piece (0-indexed)
      rotation    (int): so lan xoay xuoi (0=khong xoay, 1=90, 2=180, 3=270)
    """
    # Buoc 1: Xoay truoc khi di chuyen
    # Dung xoay CW (ArrowUp) - nhanh nhat voi 1-2 lan xoay
    rot = rotation % 4
    if rot == 3:
        # 3 lan CW = 1 lan CCW, nhanh hon
        rotate_ccw(1)
    elif rot > 0:
        rotate_cw(rot)

    # Buoc 2: Di chuyen ngang
    # Tinh offset dua tren rotation (piece rong thay doi sau khi xoay)
    diff = target_col - current_col
    if diff < 0:
        move_left(abs(diff))
    elif diff > 0:
        move_right(diff)

    # Buoc 3: Hard drop
    hard_drop()
