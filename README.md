# tetris-bot-pro

Bot Tetris AI cho **tetr.io** chay tren Chrome. Phong cach choi pro-level: uu tien Tetris (xoa 4 hang), T-spin setup, tranh tao lo, giu board thap.

## Tinh nang moi (cap nhat pro-level)

- **1-piece lookahead**: tinh toan nuoc di tot nhat cho ca piece hien tai va piece tiep theo
- **Tetris reward x10**: uu tien manh me viec xoa 4 hang mot luc
- **Back-to-Back bonus**: thuong them 1.5x khi lien tuc Tetris
- **T-spin slot detection**: nhan dien va thuong cho cac vi tri co the T-spin
- **Well depth reward**: giu mot cot trong de don cho I-piece
- **Hole penalty -8**: phat nang neu tao lo (o trong bi che)
- **Height penalty**: khong xep chong qua cao
- **Piece detection fix**: nhan dien mau sac khoi chinh xac hon
- **Board height thuc te**: khong con mac dinh 20/20 tu dau game

## Cai dat

```bash
pip install pyautogui mss numpy
```

## Huong dan chay

1. **Calibrate (lan dau):**
   ```bash
   python calibrate.py
   ```
   Chay khi tetr.io dang mo tren Chrome, full screen, scale 100%.

2. **Chay bot:**
   ```bash
   python main.py
   ```
   Switch sang cua so Chrome trong 2 giay dau. Bot tu dong bat dau.

3. **Test vision (debug):**
   ```bash
   python test_vision.py
   ```

## Cau truc file

| File | Chuc nang |
|------|----------|
| `engine_ai.py` | AI logic: tinh toan nuoc di, scoring pro-level |
| `vision.py` | Doc man hinh: nhan biet board, khoi hien tai, next pieces |
| `controller.py` | Dieu khien ban phim: di chuyen, xoay, hard drop |
| `main.py` | Vong lap chinh: ket noi tat ca lai |
| `calibrate.py` | Chuan hoa vung man hinh cho may cua ban |

## Phim dieu khien (tetr.io mac dinh)

- **ArrowUp / X**: Xoay theo chieu kim dong ho
- **Z**: Xoay nguoc chieu kim dong ho  
- **ArrowLeft/Right**: Di chuyen ngang
- **Space**: Hard drop
- **C**: Hold piece

## Luu y

- Chay o che do Chrome fullscreen (F11), scale man hinh 100%
- Neu bot nhan dien sai vi tri, chay lai `calibrate.py`
- Tetr.io thay doi giao dien co the can chinh lai mau sac trong `vision.py`
