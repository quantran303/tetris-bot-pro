"""
calibrate.py - Tu dong tim toa do board Tetr.io tren man hinh cua ban

CAH DUNG (QUAN TRONG - Chay truoc khi dung bot):
  1. Mo Tetr.io trong Chrome, vao Zen mode
  2. Dat cua so Chrome chiem toan man hinh (Maximize)
  3. Mo terminal, cd den thu muc bot
  4. Chay: python calibrate.py
  5. Lam theo huong dan hien ra
  6. File calibration.json se duoc tao ra
  7. Sau do chay: python main.py

YEU CAU: pip install mss numpy pyautogui
"""
import mss
import numpy as np
import json
import time
import sys

CALIB_FILE = "calibration.json"


def capture_full_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # man hinh chinh
        img = sct.grab(monitor)
        arr = np.array(img, dtype=np.uint8)
        return arr[:, :, :3], monitor  # BGR


def find_board_by_color(img):
    """
    Tim board Tetr.io bang cach:
    - Board co vien mau xanh lam nhat hoac dam
    - Khu vuc board phai co nen toi
    - Ty le khung board la ~1:2 (rong:cao)
    """
    # Chuyen sang HSV de tim vung co mau
    h_all, w_all = img.shape[:2]

    # Tim cot va hang co nhieu bien doi mau (vien board)
    # Scan theo hang de tim vung toi (nen board)
    gray = (img[:,:,0].astype(int) + img[:,:,1].astype(int) + img[:,:,2].astype(int)) // 3

    # Board Tetr.io co nen tuong doi toi (< 50 per channel average)
    dark_mask = gray < 40

    # Tim khoi lon nhat cua vung toi
    # Dung sliding window theo chieu doc
    best_col_start = 0
    best_col_end = w_all
    best_row_start = 0
    best_row_end = h_all

    # Thong ke vung toi theo cot
    col_dark = np.sum(dark_mask, axis=0)  # tong pixel toi theo cot
    row_dark = np.sum(dark_mask, axis=1)  # tong pixel toi theo hang

    # Tim cot trung tam (cot co nhieu vung toi nhat)
    center_col = int(np.argmax(
        np.convolve(col_dark, np.ones(50, dtype=int), 'valid')
    )) + 25

    # Scan tu center ra ngoai de tim vien board
    # Tim cot trai
    left = center_col
    while left > 0 and col_dark[left] > h_all * 0.3:
        left -= 1
    # Tim cot phai
    right = center_col
    while right < w_all - 1 and col_dark[right] > h_all * 0.3:
        right += 1

    # Tim hang tren
    top = 0
    while top < h_all - 1 and row_dark[top] < (right - left) * 0.3:
        top += 1
    # Tim hang duoi
    bottom = h_all - 1
    while bottom > 0 and row_dark[bottom] < (right - left) * 0.3:
        bottom -= 1

    # Kiem tra ti le hop le (board Tetris ~1:2)
    bw = right - left
    bh = bottom - top
    if bw <= 0 or bh <= 0:
        return None

    ratio = bh / bw
    if not (1.5 <= ratio <= 2.5):
        # Adjust: dat ty le chuan 2:1
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        bw = min(bw, w_all // 4)
        bh = int(bw * 2.0)
        left = center_x - bw // 2
        right = center_x + bw // 2
        top = center_y - bh // 2
        bottom = center_y + bh // 2

    return {
        "left": int(left),
        "top": int(top),
        "width": int(right - left),
        "height": int(bottom - top),
    }


def manual_calibrate():
    """
    Calibrate thu cong bang cach click vao 2 goc board.
    Su dung pyautogui de bat vi tri chuot.
    """
    try:
        import pyautogui
    except ImportError:
        print("Loi: can pip install pyautogui")
        return None

    print()
    print("=" * 55)
    print("  CALIBRATE THU CONG")
    print("=" * 55)
    print()
    print("Huong dan:")
    print("  1. De cua so Tetr.io hien ra (KHONG minimize)")
    print("  2. Di chuot den goc TREN-TRAI cua board (o dau tien)")
    print("  3. Bam ENTER")
    print()
    input("  >>> Bam ENTER sau khi dat chuot vao goc TREN-TRAI board...")
    x1, y1 = pyautogui.position()
    print(f"  Goc tren-trai: ({x1}, {y1})")
    print()
    print("  4. Di chuot den goc DUOI-PHAI cua board (o cuoi cung)")
    print("  5. Bam ENTER")
    print()
    input("  >>> Bam ENTER sau khi dat chuot vao goc DUOI-PHAI board...")
    x2, y2 = pyautogui.position()
    print(f"  Goc duoi-phai: ({x2}, {y2})")
    print()

    board_w = abs(x2 - x1)
    board_h = abs(y2 - y1)
    board_left = min(x1, x2)
    board_top = min(y1, y2)

    board = {
        "left": int(board_left),
        "top": int(board_top),
        "width": int(board_w),
        "height": int(board_h),
    }

    # Tinh toan cac vung khac dua tren board
    cell_w = board_w / 10
    cell_h = board_h / 20

    # Hold piece: nam ben trai board, cach ~3 cell
    hold = {
        "left": max(0, int(board_left - cell_w * 4)),
        "top": int(board_top),
        "width": int(cell_w * 3.5),
        "height": int(cell_h * 3),
    }

    # Next pieces: nam ben phai board
    next_regions = []
    for i in range(3):
        next_regions.append({
            "left": int(board_left + board_w + cell_w * 0.5),
            "top": int(board_top + i * cell_h * 3.5),
            "width": int(cell_w * 3.5),
            "height": int(cell_h * 3),
        })

    config = {
        "board": board,
        "hold": hold,
        "next": next_regions,
    }

    return config


def save_config(config):
    with open(CALIB_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print(f"  Luu cau hinh vao {CALIB_FILE} thanh cong!")


def print_config(config):
    print()
    print("CAU HINH DA LUU:")
    b = config["board"]
    print(f"  Board: top={b['top']}, left={b['left']}, w={b['width']}, h={b['height']}")
    h = config["hold"]
    print(f"  Hold:  top={h['top']}, left={h['left']}, w={h['width']}, h={h['height']}")
    for i, n in enumerate(config["next"]):
        print(f"  Next{i+1}: top={n['top']}, left={n['left']}, w={n['width']}, h={n['height']}")
    print()


def main():
    print()
    print("=" * 55)
    print("  TETR.IO BOT - CALIBRATION TOOL")
    print("=" * 55)
    print()
    print("Chon phuong phap calibrate:")
    print("  1. Thu cong (KHUYEN DUNG - chinh xac nhat)")
    print("  2. Tu dong (thu tim board tren man hinh)")
    print()

    choice = input("Nhap 1 hoac 2: ").strip()

    if choice == "2":
        print()
        print("Dang chup man hinh va tim board...")
        print("Hay chac rang Tetr.io dang hien thi toan man hinh!")
        time.sleep(2)
        img, monitor = capture_full_screen()
        config_board = find_board_by_color(img)

        if config_board is None:
            print("Khong tim thay board tu dong. Chuyen sang thu cong...")
            config = manual_calibrate()
        else:
            bw = config_board["width"]
            bh = config_board["height"]
            cell_w = bw / 10
            cell_h = bh / 20
            bl = config_board["left"]
            bt = config_board["top"]

            hold = {
                "left": max(0, int(bl - cell_w * 4)),
                "top": int(bt),
                "width": int(cell_w * 3.5),
                "height": int(cell_h * 3),
            }
            next_regions = []
            for i in range(3):
                next_regions.append({
                    "left": int(bl + bw + cell_w * 0.5),
                    "top": int(bt + i * cell_h * 3.5),
                    "width": int(cell_w * 3.5),
                    "height": int(cell_h * 3),
                })
            config = {"board": config_board, "hold": hold, "next": next_regions}
            print("Tim thay board tu dong!")
    else:
        config = manual_calibrate()

    if config is None:
        print("Calibrate that bai!")
        return

    print_config(config)
    save_config(config)

    print("Calibrate xong! Bay gio chay: python main.py")
    print()


if __name__ == "__main__":
    main()
