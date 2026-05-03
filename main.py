import time
from engine_ai import get_best_move, matrix_to_board
from vision import (
    extract_board_matrix,
    get_current_piece,
    get_next_pieces,
    get_board_max_height,
)
from controller import exec_move, focus_game_window

# Cot spawn trung tam cua Tetr.io (0-indexed, dem tu trai)
SPAWN_COLUMN = 4


def main():
    print("-" * 55)
    print("  Tetr.io Bot PRO  |  tetr.io  |  Zen mode")
    print("  Cai dat: pip install pyautogui mss numpy")
    print("-" * 55)
    focus_game_window(wait=2.0)

    step = 0
    prev_piece = None
    while True:
        step += 1

        # 1. Doc trang thai board tu man hinh
        matrix = extract_board_matrix()
        board = matrix_to_board(matrix)

        # 2. Lay piece hien tai va next
        current_piece = get_current_piece()
        next_pieces = get_next_pieces()
        next_piece = next_pieces[0] if next_pieces else None

        # 3. Tinh chieu cao thuc te (0 neu board trong)
        board_height = get_board_max_height(matrix)

        print(f"Step {step:4d} | Piece: {current_piece} | Next: {next_piece} | Height: {board_height}/20")

        # 4. Bo qua neu khong nhan dien duoc piece
        if current_piece is None:
            print("  -> Khong nhan dien duoc piece, cho...")
            time.sleep(0.3)
            continue

        # 5. Neu piece giong buoc truoc, co the piece chua thay doi
        if current_piece == prev_piece:
            time.sleep(0.1)
            continue

        # 6. Tim nuoc di tot nhat
        best = get_best_move(board, current_piece, next_piece)

        if best is None:
            print("  -> Khong tim duoc nuoc di, bo qua")
            time.sleep(0.3)
            continue

        rotation, target_col, score = best
        print(f"  -> Xoay {rotation} lan, dat cot {target_col}, diem: {score:.1f}")

        # 7. Thuc hien nuoc di
        exec_move(
            current_col=SPAWN_COLUMN,
            target_col=target_col,
            rotation=rotation,
        )

        prev_piece = current_piece
        time.sleep(0.15)


if __name__ == "__main__":
    main()
