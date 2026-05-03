import time
import os
import sys
from engine_ai import best_move, matrix_to_board, PIECES, new_board
from vision import (
    extract_board_matrix,
    get_current_piece_smart,
    get_next_pieces,
    get_board_max_height,
    get_column_heights,
    CALIB_FILE,
)
from controller import exec_move, focus_game_window

SPAWN_COL   = 4    # spawn column centre for tetr.io
DELAY_MOVE  = 0.10 # seconds after executing a move
DELAY_WAIT  = 0.18 # seconds waiting for new piece to appear
DELAY_RETRY = 0.08 # seconds between retries detecting piece
MAX_RETRY   = 15   # retries before giving up on piece detection

def check_calibration():
    if not os.path.exists(CALIB_FILE):
        print('[MAIN] Calibration file not found. Run calibrate.py first!')
        sys.exit(1)

def board_from_vision():
    """Return a 20x10 binary board from screen, or None on failure."""
    matrix = extract_board_matrix()
    if matrix is None:
        return None
    return matrix_to_board(matrix)

def run_bot():
    check_calibration()
    print('[MAIN] Bot starting. Focus the tetr.io window...')
    time.sleep(2)
    focus_game_window()
    time.sleep(0.5)

    # Track back-to-back state
    b2b          = False
    last_cleared = 0
    no_move_cnt  = 0
    MAX_NO_MOVE  = 5

    while True:
        # --- 1. Detect board state ---
        board = board_from_vision()
        if board is None:
            print('[MAIN] Could not read board, retrying...')
            time.sleep(0.3)
            continue

        # --- 2. Detect current piece ---
        current_piece = None
        for _ in range(MAX_RETRY):
            current_piece = get_current_piece_smart()
            if current_piece:
                break
            time.sleep(DELAY_RETRY)

        if not current_piece:
            print('[MAIN] No current piece detected, skipping...')
            time.sleep(DELAY_WAIT)
            continue

        # --- 3. Detect next piece (for lookahead) ---
        next_pieces = get_next_pieces()
        next_piece  = next_pieces[0] if next_pieces else None

        # --- 4. Compute best move ---
        rot, col, score = best_move(board, current_piece, next_piece, b2b)

        if score < -5000:
            # No valid move found – board likely in bad state
            no_move_cnt += 1
            print(f'[MAIN] No valid move (score={score:.1f}), count={no_move_cnt}')
            if no_move_cnt >= MAX_NO_MOVE:
                print('[MAIN] Resetting board state detection...')
                no_move_cnt = 0
                time.sleep(0.5)
            time.sleep(DELAY_WAIT)
            continue

        no_move_cnt = 0
        print(f'[MAIN] Piece={current_piece} Next={next_piece} Rot={rot} Col={col} Score={score:.2f} B2B={b2b}')

        # --- 5. Execute move ---
        exec_move(rot, col, current_piece)
        time.sleep(DELAY_MOVE)

        # --- 6. Wait for piece to land and update B2B state ---
        time.sleep(DELAY_WAIT)
        new_board_state = board_from_vision()
        if new_board_state is not None:
            # Estimate lines cleared by counting full rows
            cleared = sum(1 for row in new_board_state if all(c for c in row))
            # Actually cleared = rows that disappeared; compare heights
            old_h = sum(1 for row in board if any(c for c in row))
            new_h = sum(1 for row in new_board_state if any(c for c in row))
            lines_cleared = max(0, (old_h + 1) - new_h)  # rough estimate

            # Update B2B: maintain if Tetris (4) or kept from before
            if lines_cleared == 4:
                b2b = True
            elif lines_cleared > 0:
                b2b = False  # single/double/triple breaks B2B

if __name__ == '__main__':
    run_bot()
