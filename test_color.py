from vision import capture_region, average_color, NEXT_REGIONS, CURRENT_REGION
import time

print("Chay khi Tetr.io dang mo. Ctrl+C de thoat.")
print("Dung gia tri BGR in ra de cap nhat PIECE_COLORS trong vision.py neu detect sai.")
print("=" * 55)

while True:
    img = capture_region(CURRENT_REGION)
    b, g, r = average_color(img)
    print(f"CURRENT   BGR = ({b:.0f}, {g:.0f}, {r:.0f})")

    for i, reg in enumerate(NEXT_REGIONS):
        img2 = capture_region(reg)
        b2, g2, r2 = average_color(img2)
        print(f"NEXT {i+1}    BGR = ({b2:.0f}, {g2:.0f}, {r2:.0f})")

    print("-" * 55)
    time.sleep(1.0)
