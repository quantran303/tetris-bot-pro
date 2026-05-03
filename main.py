import time
import os
import sys
from engine_ai import get_best_move, matrix_to_board, PIECES
from vision import (
    extract_board_matrix,
    get_current_piece_smart,
    get_next_pieces,
    get_board_max_height,
    get_column_heights,
    CALIB_FILE,
)
from controller import exec_move, focus_game_window

SPAWN_COL = 4   # cot spawn trung tam Tetr.io
DELAY_MOVE  = 0.10  # giay sau khi thuc hien move
DELAY_WAIT  = 0.18  # giay cho piece moi xuat hien
DELAY_RETRY = 0.08  # giay neu chua nhan dien duoc piece
MAX_RETRY   = 15    # thu toi da 15 lan moi piece


def check_calibration():
    if not os.path.exists(CALIB_FILE):
        print()
        print("!" * 55)
        print("  CHUA CALIBRATE!")
        print("  Chay lenh nay truoc:  python calibrate.py")
        print("  Sau do chay lai:       python main.py")
        print("!" * 55)
        print()
        sys.exit(1)


def wait_for_piece(max_retries=MAX_RETRY):
    """
    Cho den khi nhan dien duoc piece hien tai.
    Tra ve (piece_name, board_matrix) hoac (None, matrix).
    """
    for attempt in range(max_retries):
        matrix = extract_board_matrix()
        board  = matrix_to_board(matrix)
        piece  = get_current_piece_smart()
        if piece is not None:
            return piece, matrix, board
        time.sleep(DELAY_RETRY)
    # Tra ve matrix du khong co piece
    matrix = extract_board_matrix()
    board  = matrix_to_board(matrix)
    return None, matrix, board


def main():
    check_calibration()

    print("-" * 55)
    print("  Tetr.io Bot PRO - Zen mode auto-play")
    print("  Ctrl+C de dung bot")
    print("-" * 55)
    print()
    print("  Chuyen sang cua so Tetr.io...")
    focus_game_window(wait=2.5)
    print("  Bot dang chay!")
    print()

    step = 0
    miss = 0  # dem so lan bo qua lien tiep

    while True:
        step += 1

        # 1. Nhan dien piece hien tai (co retry)
        piece, matrix, board = wait_for_piece()

        # 2. Doc next piece
        nexts  = get_next_pieces()
        next_p = nexts[0] if nexts else None
        height = get_board_max_height(matrix)
        cols   = get_column_heights(matrix)

        # Log trang thai
        col_str = "".join(str(h) for h in cols)
        print(f"[{step:4d}] piece={piece or '?':2s}  next={next_p or '?':2s}  "
              f"height={height:2d}/20  cols={col_str}")

        # 3. Neu van khong nhan dien duoc piece -> cho va thu lai
        if piece is None:
            miss += 1
            if miss >= 5:
                print("       -> Qua nhieu lan bo qua, che do cho 1 giay...")
                time.sleep(1.0)
                miss = 0
            else:
                print("       -> Chua nhan dien piece, cho...")
                time.sleep(DELAY_WAIT)
            continue

        miss = 0

        # 4. Tim nuoc di tot nhat
        best = get_best_move(board, piece, next_p)

        if best is None:
            print("       -> Khong tim duoc nuoc di, bo qua")
            time.sleep(DELAY_WAIT)
            continue

        rotation, target_col, score = best
        print(f"       -> xoay={rotation}  cot={target_col}  score={score:.0f}")

        # 5. Thuc hien nuoc di
        exec_move(
            current_col=SPAWN_COL,
            target_col=target_col,
            rotation=rotation,
        )

        # 6. Cho piece tiep theo xuat hien
        time.sleep(DELAY_MOVE)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Bot da dung. Tam biet!")
