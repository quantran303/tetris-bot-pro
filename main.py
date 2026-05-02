import time
from engine_ai import best_move_lookahead
from vision import (
    extract_board_matrix,
    detect_current_piece,
    detect_next_queue,
    get_board_max_height,
)
from controller import exec_move, focus_game_window

# Cot spawn trung tam cua Tetr.io (0-indexed, dem tu trai)
SPAWN_COLUMN = 4

def main():
    print("=" * 55)
    print("  Tetr.io Bot PRO  |  tetr.io  |  Zen mode")
    print("  Cai dat: pip install pyautogui mss numpy")
    print("=" * 55)
    focus_game_window(wait=2.0)

    step = 0
    while True:
        step += 1

        board   = extract_board_matrix()
        current = detect_current_piece()
        nexts   = detect_next_queue(count=2)
        mh      = get_board_max_height(board)

        if current is None:
            print(f"[{step}] Khong detect duoc quan, thu lai...")
            time.sleep(0.06)
            continue

        print(f"Step {step:4d} | piece={current} | next={nexts} | height={mh}/20")

        move = best_move_lookahead(board, current, nexts, depth=2)
        if move is None:
            print("Khong tim duoc nuoc di - game over?")
            break

        r, x, _, cleared, score = move
        print(f"           rot={r}  x={x}  cleared={cleared}  score={score:.1f}")

        exec_move(SPAWN_COLUMN, x, r)
        time.sleep(0.18)

if __name__ == "__main__":
    main()
