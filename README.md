# tetris-bot-pro

Bot Tetris AI choi tu dong tren **tetr.io** (Chrome). Dua tren logic cua [mikhail-vlasenko/Tetris-AI](https://github.com/mikhail-vlasenko/Tetris-AI).

---

## Cai dat nhanh

```bash
pip install pyautogui mss numpy
```

---

## Huong dan chay (doc ky tung buoc)

### Buoc 1: Calibrate (CHI CHAY LAN DAU)

```bash
python calibrate.py
```

- Mo tetr.io tren Chrome, nhan **F11** (fullscreen), scale man hinh 100%
- Bat dau 1 game cho den khi co pieces xuat hien
- Switch sang terminal, nhan **Enter**
- Bot se tu dong chup man hinh va tao file `calibration.json`

### Buoc 2: Kiem tra vision (QUAN TRONG - lam truoc khi chay bot)

```bash
python debug_vision.py
```

- Switch sang tetr.io ngay lap tuc
- Nhin vao terminal sau 3 giay
- **Board phai hien thi dung** (# = co khoi, . = rong)
- **Current piece phai duoc nhan dien** (I/O/T/S/Z/J/L)
- Neu board sai hoac piece = None => xem phan **Xu ly loi** ben duoi

### Buoc 3: Chay bot

```bash
python main.py
```

- Switch sang Chrome trong vong 2 giay
- Bot se tu dong choi
- Nhin terminal de xem bot dang lam gi

---

## Xu ly loi thuong gap

### Loi: Board hien thi toan `..........` (tat ca rong)

Nguyen nhan: Vung calibration sai, bot dang chup vung khong phai board.

Cach sua:
1. Dong game, chay lai `python calibrate.py`
2. Hoac sua tay `calibration.json`:
```json
{
  "board": {"top": 135, "left": 483, "width": 316, "height": 632}
}
```
Cong thuc tinh theo do phan giai man hinh cua ban:
- `left` = (man_hinh_rong - 316) / 2 - 158
- `top` = khoang 135 (phan tren cua board)

### Loi: Current piece = None

Nguyen nhan: Mau sac piece khac voi bang mau trong `vision.py`.

Cach sua: Chay `python debug_vision.py`, nhin phan `[DIAG] Mau pixel`, sau do sua `PIECE_COLORS_RGB` trong `vision.py` cho khop voi mau thuc te tren man hinh ban.

### Loi: Bot bam phim nhung piece bay sang trai/phai sai

Nguyen nhan: `SPAWN_COL` sai trong `controller.py`.

Tetr.io mac dinh spawn tai cot 4 (0-indexed). Neu piece xuat hien tai vi tri khac, doi `SPAWN_COL = 4` trong `controller.py`.

### Loi: Bot chay nhanh qua, piece chua ha xuong kip

Sua trong `main.py`:
```python
DELAY_AFTER_MOVE = 0.20   # tang len (mac dinh 0.12)
DELAY_WAIT_PIECE = 0.25   # tang len (mac dinh 0.15)
```

---

## Cau truc file

| File | Chuc nang |
|------|----------|
| `calibrate.py` | Tu dong tim vung board tren man hinh, tao `calibration.json` |
| `debug_vision.py` | Kiem tra board/piece co duoc nhan dien dung khong |
| `vision.py` | Doc man hinh: board 20x10, mau piece, spawn detection |
| `engine_ai.py` | AI: simulation, scoring, depth-2 lookahead |
| `controller.py` | Dieu khien ban phim (xoay, di chuyen, hard drop) |
| `main.py` | Vong lap chinh |

---

## Yeu cau

- Python 3.8+
- Windows (dung pyautogui)
- Chrome mo tetr.io, F11 fullscreen, zoom 100%
- **Khong** co phan mem zoom man hinh (scale phai la 100%)
