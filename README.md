# toolFisch

toolFisch la mot tac vu tu dong cau ca ben ngoai (External Agent) danh cho tua game Fisch tren nen tang Roblox, su dung ky thuat thi giac may tinh (Computer Vision) de tuong tac voi giao dien game ma khong can can thiep vao bo nho hay tep tin cua game, dam bao tinh an toan va han che toi da kha nang bi phat hien.

## Tinh nang chinh

1. Kien truc State Machine tu dong hoa hoan toan cac buoc: Quang can -> Doi ca can -> Click bong bong Shake -> Giu/tha chuot mini-game (Reeling) -> Dem va ghi nhan ket qua.
2. Bo dieu khien Reeling thich ung (Edge-Aware Predictive Controller): Tu dong tinh toan van toc, huong di chuyen cua ca va ap dung thuat toan du doan vi tri de giu thanh bat ca luon nam trong vung an toan, ho tro cau ca hiem tu tier Common den Mythic.
3. Cong cu hieu chinh ROI truc quan (Visual Calibrator): Ho tro nguoi dung ve va luu vung quet truc tiep tren man hinh thong qua giao dien truc quan (F9), tu dong tuong thich voi moi do phan giai man hinh.
4. Chup man hinh da luong an toan: Su dung thu vien mss voi co che phan tach luong doc lap (thread-local contexts), giai quyet triet de loi truy cap bo nho tren he dieu hanh Windows.
5. Co che chong AFK va hanh vi nhan bang: Tich hop cac khoang tre ngau nhien, di chuyen nhan vat gia lap hanh vi nguoi that de di qua he thong quet AFK cua Roblox.

## Cong nghe su dung

* Python 3.11+
* OpenCV (Phan tich hinh anh va loc dai mau HSV)
* CustomTkinter / Tkinter (Giao dien dieu khien che do toi)
* MSS (Chup anh man hinh toc do cao tren 60 FPS)
* PyDirectInput (Gui tin hieu click, hold chuot o cap do phan cung DirectX)
* Loguru (Ghi log bat dong bo)

## Huong dan cai dat

### Yeu cau he thong
* He dieu hanh: Windows (do PyDirectInput can quyen dieu khien phan cung Windows).
* Python phien ban 3.11 tro len.

### Cac buoc cai dat
1. Tai ma nguon tu kho luu tru nay ve may.
2. Mo Command Prompt hoac PowerShell voi quyen Admin (Run as Administrator) va di chuyen den thu muc nguon cua du an.
3. Cai dat cac thu vien phu thuoc bang lenh sau:
   ```bash
   pip install opencv-python numpy mss pydirectinput loguru pillow
   ```

## Huong dan su dung

### Khoi dong tool
Moi thao tac gui tin hieu chuot vao Roblox yeu cau quyen quan tri, do do ban phai chay cong cu tu terminal co quyen Admin:
```bash
python main.py
```

### Cac phim tat trong tool
* F8: Bat dau hoac Tam dung (Toggle Start/Stop) chu ky tu dong cau ca.
* F9: Mo cua so hieu chinh vung quet man hinh (Calibrator).
* ESC: Dung chay tool ngay lap tuc.

### Huong dan can chinh toa do (Calibration)
1. Khi khoi chay tool lan dau, ban can dung visual calibrator de dinh hinh cac vung quet tren man hinh Roblox.
2. Nhan F9 de mo cua so Calibrator.
3. Chon vung can thiet lap (Bar Zone cho minigame hoac Shake Zone cho bong bong).
4. Nhap chuot va keo chon dung vi tri cua thanh minigame tren man hinh, sau do nhan ENTER de xac nhan luu.
5. Toa do moi se duoc cap nhat truc tiep vao tep tin config.json.

### Chuan doan loi (Diagnostic)
Neu tool bao loi khong tim thay thanh giu ca hoac ca chay tuot ra ngoai, hay mo game den phan minigame giu ca va chay:
```bash
python diagnostic.py
```
Sau 3 giay, tep tin hinh anh ket qua chup man hinh va mask loc mau HSV se duoc luu tai thu muc logs/. Dua vao cac anh do, ban co the dieu chinh lai toa do ROI hoac dai mau sac trong config.json cho phu hop voi cau hinh do hoa game cua ban.
