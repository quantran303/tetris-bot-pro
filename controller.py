import pyautogui
import time
import random

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

# ----------------------------------------------------------------
# PHIM DIEU KHIEN TETR.IO (mac dinh)
# Neu ban doi phim trong Settings -> Controls, chinh lai day
# ----------------------------------------------------------------
KEY_ROTATE_CW  = 'up'     # Xoay xuoi (ArrowUp) - mac dinh Tetr.io
KEY_ROTATE_CCW = 'z'      # Xoay nguoc (Z)
KEY_LEFT       = 'left'   # Di trai
KEY_RIGHT      = 'right'  # Di phai
KEY_SOFT_DROP  = 'down'   # Ha cham
KEY_HARD_DROP  = 'space'  # Ha nhanh
KEY_HOLD       = 'c'      # Giu

KEY_DELAY    = 0.050  # delay sau moi phim bam
ROTATE_DELAY = 0.040  # delay sau khi xoay (de piece kip xoay)
MOVE_DELAY   = 0.035  # delay giua cac lan di chuyen ngang
DROP_DELAY   = 0.050  # delay truoc hard drop

SPAWN_COL = 4  # cot spawn mac dinh cua Tetr.io (0-indexed)


def focus_game_window():
    """In ra thong bao de nguoi dung biet can click vao cua so game."""
    print('[controller] Ban co 2 giay de click vao cua so game...')
    time.sleep(2)


def _press(key, delay=None):
    """Bam phim don voi delay."""
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
    n = int(n) % 4
    for _ in range(n):
        _press(KEY_ROTATE_CW, delay=ROTATE_DELAY)


def rotate_ccw(n=1):
    """
    Xoay piece n lan nguoc chieu kim dong ho.
    Tetr.io: phim Z.
    """
    n = int(n) % 4
    for _ in range(n):
        _press(KEY_ROTATE_CCW, delay=ROTATE_DELAY)


def move_left(n):
    """Di chuyen trai n buoc."""
    for _ in range(int(n)):
        _press(KEY_LEFT, delay=MOVE_DELAY)


def move_right(n):
    """Di chuyen phai n buoc."""
    for _ in range(int(n)):
        _press(KEY_RIGHT, delay=MOVE_DELAY)


def hard_drop():
    """Hard drop - dat piece xuong ngay."""
    _press(KEY_HARD_DROP, delay=DROP_DELAY)


def hold_piece():
    """Giu piece hien tai."""
    _press(KEY_HOLD, delay=KEY_DELAY)


def exec_move(rotation, target_col, piece_type=None):
    """
    Thuc hien nuoc di: xoay piece roi di chuyen den cot dich, cuoi cung hard drop.

    Args:
        rotation   (int): rotation index tra ve boi engine_ai.best_move() (0, 1, 2, 3)
        target_col (int): cot dich (0-indexed) tra ve boi engine_ai.best_move()
        piece_type (str): loai piece (khong bat buoc, chi de debug)

    Cach hoat dong:
        - rotation=0: khong xoay
        - rotation=1: xoay CW 1 lan
        - rotation=2: xoay CW 2 lan (hoac CCW 2 lan)
        - rotation=3: xoay CCW 1 lan (nhanh hon CW 3 lan)
    """
    rotation   = int(rotation)   # dam bao la integer
    target_col = int(target_col) # dam bao la integer
    current_col = SPAWN_COL      # piece moi spawn o cot 4 (mac dinh tetr.io)

    # Buoc 1: Xoay truoc khi di chuyen
    rot = rotation % 4
    if rot == 3:
        # 3 lan CW = 1 lan CCW, nhanh hon
        rotate_ccw(1)
    elif rot > 0:
        rotate_cw(rot)

    # Buoc 2: Di chuyen ngang den cot dich
    # Tinh offset dua tren rotation (piece rong thay doi sau khi xoay)
    diff = target_col - current_col
    if diff < 0:
        move_left(abs(diff))
    elif diff > 0:
        move_right(diff)

    # Buoc 3: Hard drop
    hard_drop()
