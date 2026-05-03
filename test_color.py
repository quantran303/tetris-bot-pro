"""
test_color.py - Cong cu debug mau sac Tetr.io

CAH DUNG:
1. Mo Tetr.io trong Chrome, vao Zen mode
2. Chay: python test_color.py
3. Xem gia tri R, G, B in ra
4. Cap nhat PIECE_COLORS_RGB trong vision.py theo gia tri thuc te

LUU Y: Moi man hinh/do phan giai/Windows scaling co the cho mau khac nhau!
"""
from vision import (
    capture_region,
    average_color_rgb,
    identify_piece_rgb,
    CURRENT_REGION,
    NEXT_REGIONS,
    MONITOR_REGION,
    PIECE_COLORS_RGB,
    is_colored_block,
)
import time
import numpy as np


def print_separator(char="-", n=55):
    print(char * n)


def scan_colors_once():
    """Doc mau 1 lan va in ket qua chi tiet"""
    print_separator("=")
    print("  MAU SAC THUC TE TREN MAN HINH HIEN TAI")
    print_separator("=")

    # Current piece
    img = capture_region(CURRENT_REGION)
    h, w = img.shape[:2]
    center = img[int(h*0.2):int(h*0.8), int(w*0.1):int(w*0.9)]
    r, g, b = average_color_rgb(center)
    piece = identify_piece_rgb(r, g, b)
    is_block = is_colored_block(r, g, b)
    print(f"CURRENT PIECE:")
    print(f"  RGB = ({r:.0f}, {g:.0f}, {b:.0f})")
    print(f"  La block? {is_block}  |  Nhan dien: {piece}")
    print()

    # Next pieces
    for i, region in enumerate(NEXT_REGIONS):
        img = capture_region(region)
        h, w = img.shape[:2]
        center = img[int(h*0.15):int(h*0.85), int(w*0.1):int(w*0.9)]
        r, g, b = average_color_rgb(center)
        piece = identify_piece_rgb(r, g, b)
        is_block = is_colored_block(r, g, b)
        print(f"NEXT {i+1}:")
        print(f"  RGB = ({r:.0f}, {g:.0f}, {b:.0f})")
        print(f"  La block? {is_block}  |  Nhan dien: {piece}")
        print()

    print_separator()
    print("MAU THAM CHIEU HIEN TAI (PIECE_COLORS_RGB):")
    for name, (pr, pg, pb) in PIECE_COLORS_RGB.items():
        print(f"  {name}: R={pr:3d}, G={pg:3d}, B={pb:3d}")
    print_separator()


def scan_board_once():
    """Quet board va hien thi trang thai"""
    img = capture_region(MONITOR_REGION)
    h, w = img.shape[:2]
    cell_h = h / 20
    cell_w = w / 10

    print("BOARD STATE (# = block, . = trong):")
    board_str = ""
    for row in range(20):
        line = "  |"
        for col in range(10):
            y1 = int(row * cell_h + cell_h * 0.2)
            y2 = int(row * cell_h + cell_h * 0.8)
            x1 = int(col * cell_w + cell_w * 0.2)
            x2 = int(col * cell_w + cell_w * 0.8)
            cell = img[y1:y2, x1:x2]
            r2, g2, b2 = average_color_rgb(cell)
            line += "#" if is_colored_block(r2, g2, b2) else "."
        line += "|"
        board_str += line + "\n"
    print(board_str)


def main():
    print()
    print("  TEST COLOR TOOL - Tetr.io Bot PRO")
    print("  Dang theo doi mau sac... Ctrl+C de thoat")
    print()
    print("  -> Mo tetr.io Zen mode truoc khi chay!")
    print("  -> Sau 3 giay se bat dau doc mau...")
    print()
    time.sleep(3.0)

    step = 0
    while True:
        step += 1
        print(f"\n[Quet lan {step}]")
        try:
            scan_colors_once()
            if step % 5 == 0:  # Moi 5 lan quet 1 lan hien thi board
                scan_board_once()
        except Exception as e:
            print(f"Loi: {e}")
        time.sleep(1.5)


if __name__ == "__main__":
    main()
