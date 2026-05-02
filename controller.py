import pyautogui
import time
import random

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

def focus_game_window(wait=2.0):
    print(f"[controller] Ban co {wait} giay de click vao cua so game...")
    time.sleep(wait)

def _press(key, delay_after=0.025):
    pyautogui.keyDown(key)
    time.sleep(0.015 + random.uniform(0, 0.010))
    pyautogui.keyUp(key)
    time.sleep(delay_after + random.uniform(0, 0.010))

def exec_move(current_col, target_col, rotation_count):
    # Buoc 1: Xoay piece
    for _ in range(rotation_count % 4):
        _press('up', delay_after=0.03)

    # Buoc 2: Di chuyen ngang
    dx = target_col - current_col
    if dx > 0:
        for _ in range(dx):
            _press('right', delay_after=0.022)
    elif dx < 0:
        for _ in range(-dx):
            _press('left', delay_after=0.022)

    # Buoc 3: Hard drop
    time.sleep(0.02)
    _press('space', delay_after=0.05)
