# toolFisch

toolFisch là một tác vụ tự động câu cá bên ngoài (External Agent) dành cho tựa game Fisch trên nền tảng Roblox, sử dụng kỹ thuật thị giác máy tính (Computer Vision) để tương tác với giao diện game mà không cần can thiệp vào bộ nhớ hay tệp tin của game, đảm bảo tính an toàn và hạn chế tối đa khả năng bị phát hiện.

## Tính năng chính

1. Kiến trúc State Machine tự động hóa hoàn toàn các bước: Quăng cần -> Đợi cá cắn -> Click bong bóng Shake -> Giữ/thả chuột mini-game (Reeling) -> Đếm và ghi nhận kết quả.
2. Bộ điều khiển Reeling thích ứng (Edge-Aware Predictive Controller): Tự động tính toán vận tốc, hướng di chuyển của cá và áp dụng thuật toán dự đoán vị trí để giữ thanh bắt cá luôn nằm trong vung an toàn, hỗ trợ câu cá hiếm từ hạng Common đến Mythic.
3. Công cụ hiệu chỉnh ROI trực quan (Visual Calibrator): Hỗ trợ người dùng vẽ và lưu vùng quét trực tiếp trên màn hình thông qua giao diện trực quan (F9), tự động tương thích với mọi độ phân giải màn hình.
4. Chụp màn hình đa luồng an toàn: Sử dụng thư viện mss với cơ chế phân tách luồng độc lập (thread-local contexts), giải quyết triệt để lỗi truy cập bộ nhớ trên hệ điều hành Windows.
5. Cơ chế chống AFK và hành vi nhân bản: Tích hợp các khoảng trễ ngẫu nhiên, di chuyển nhân vật giả lập hành vi người thật để đi qua hệ thống quét AFK của Roblox.

## Công nghệ sử dụng

* Python 3.11+
* OpenCV (Phân tích hình ảnh và lọc dải màu HSV)
* CustomTkinter / Tkinter (Giao diện điều khiển chế độ tối)
* MSS (Chụp ảnh màn hình tốc độ cao trên 60 FPS)
* PyDirectInput (Gửi tín hiệu click, hold chuột ở cấp độ phần cứng DirectX)
* Loguru (Ghi log bất đồng bộ)

## Hướng dẫn cài đặt

### Yêu cầu hệ thống
* Hệ điều hành: Windows (do PyDirectInput cần quyền điều khiển phần cứng Windows).
* Python phiên bản 3.11 trở lên.

### Các bước cài đặt
1. Tải mã nguồn từ kho lưu trữ này về máy.
2. Mở Command Prompt hoặc PowerShell với quyền Admin (Run as Administrator) và di chuyển đến thư mục nguồn của dự án.
3. Cài đặt các thư viện phụ thuộc bằng lệnh sau:
   ```bash
   pip install opencv-python numpy mss pydirectinput loguru pillow
   ```

## Hướng dẫn sử dụng

### Khởi động công cụ
Mọi thao tác gửi tín hiệu chuột vào Roblox yêu cầu quyền quản trị, do đó bạn phải chạy công cụ từ terminal có quyền Admin:
```bash
python main.py
```

### Các phím tắt trong công cụ
* F8: Bắt đầu hoặc Tạm dừng (Toggle Start/Stop) chu kỳ tự động câu cá.
* F9: Mở cửa sổ hiệu chỉnh vùng quét màn hình (Calibrator).
* ESC: Dừng chạy công cụ ngay lập tức.

### Hướng dẫn căn chỉnh tọa độ (Calibration)
1. Khi khởi chạy công cụ lần đầu, bạn cần dùng visual calibrator để định hình các vùng quét trên màn hình Roblox.
2. Nhấn F9 để mở cửa sổ Calibrator.
3. Chọn vùng cần thiết lập (Bar Zone cho minigame hoặc Shake Zone cho bong bóng).
4. Nhấp chuột và kéo chọn đúng vị trí của thanh minigame trên màn hình, sau đó nhấn ENTER để xác nhận lưu.
5. Tọa độ mới sẽ được cập nhật trực tiếp vào tệp tin config.json.

### Chẩn đoán lỗi (Diagnostic)
Nếu công cụ báo lỗi không tìm thấy thanh giữ cá hoặc cá chạy tuột ra ngoài, hãy mở game đến phần minigame giữ cá và chạy:
```bash
python diagnostic.py
```
Sau 3 giây, tệp tin hình ảnh kết quả chụp màn hình và mask lọc màu HSV sẽ được lưu tại thư mục logs/. Dựa vào các ảnh đó, bạn có thể điều chỉnh lại tọa độ ROI hoặc dải màu sắc trong config.json cho phù hợp với cấu hình đồ họa game của bạn.
