from vision import (
    extract_board_matrix,
    detect_current_piece,
    detect_next_queue,
    get_board_max_height,
)

def print_board(b):
    print("   0123456789")
    print("  +-----------+")
    for i, row in enumerate(b):
        print(f"{i:2d}|{''.join('#' if c else '.' for c in row)}|")
    print("  +-----------+")

print("Doc board tu man hinh (dam bao game dang mo)...")
board = extract_board_matrix()
print_board(board)
print(f"\nMax height : {get_board_max_height(board)}/20")
print(f"CURRENT    : {detect_current_piece()}")
print(f"NEXT queue : {detect_next_queue(5)}")
print("\nNeu board sai, hay chinh lai MONITOR_REGION trong vision.py")
