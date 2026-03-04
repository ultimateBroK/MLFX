# Sổ Tay Cấp Cứu (Troubleshooting)

Hệ thống thi thoảng sẽ có những trục trặc nho nhỏ do môi trường hoặc dữ liệu. Nếu bạn gõ lệnh mà bị lỗi màu đỏ đỏ, hãy bình tĩnh tìm cách giải quyết ở đây.

---

### 🚨 Lỗi 1: `pixi: command not found`
*   **Hiện tượng**: Gõ bất kì lệnh `pixi ...` nào máy cũng báo lỗi không hiểu.
*   **Nguyên nhân**: Do bạn chưa cài Pixi, hoặc cài rồi nhưng chưa reset lại Terminal.
*   **Cách sửa**: 
    1. Làm theo bước cài đặt ở phần 1 trong [USAGE_GUIDE](USAGE_GUIDE.md).
    2. Đóng hẳn phần mềm Terminal/VSCode lại và mở lên lại.

### 🚨 Lỗi 2: Báo thiếu Package (Ví dụ: `ModuleNotFoundError: No module named 'xgboost'`)
*   **Nguyên nhân**: Môi trường dự án chưa cài đủ thư viện. Có thể ai đó vừa thêm thu viện mới mà bạn quên update.
*   **Cách sửa**: Chạy đúng 1 lệnh để đồng bộ lại:
    ```bash
    pixi install
    ```

### 🚨 Lỗi 3: `SystemExit: No feature files found for XAUUSD` (Lỗi Không Tìm Thấy File)
*   **Hiện tượng**: Khi bạn chạy lệnh Label (Bước 4) hoặc lệnh Train AI nhưng lại bị văng lỗi không tìm thấy File hoặc `DataFrame is empty`.
*   **Nguyên nhân**: Bạn nhảy cóc! Bạn chạy Bước 4 trong khi chưa chạy Bước 2 (Resample) hoặc Bước 3 (Tạo Features).
*   **Cách sửa**: Làm từ tốn theo thứ tự ở [USAGE_GUIDE](USAGE_GUIDE.md). Phải tạo data thô -> tạo Nến -> tạo Feature -> rồi mới Label.

### 🚨 Lỗi 4: Máy tính hết RAM, đứng máy (Out Of Memory / Killed)
*   **Nguyên nhân**: Bạn đang làm sai thao tác khi đọc dữ liệu Vàng 10 năm. Đừng bao giờ gom 135 file `.parquet` thành 1 cục duy nhất để Load vô RAM. Nó nặng tới 20GB.
*   **Cách sửa**: Luôn sử dụng lệnh `scan_parquet` của Polars để xử lý dữ liệu cuộn (Lazy Evaluation) thay vì `read_parquet` thông thường. Xem cách đọc chuẩn ở `EVALUATION_GUIDE.md`.

### 🚨 Lỗi 5: Đang Download từ Dukascopy thì bị đứng im, rớt mạng
*   **Hiện tượng**: Đang chạy `download_gold.py` tới năm 2018 thì rớt mạng tắt ngang.
*   **Cách sửa**: Yên tâm, hệ thống có lưu tiến trình tải ở log (file `completed_months.json`). Cứ bật lại lệnh `pixi run python pipeline/download_gold.py`, nó sẽ tự nhận diện các tháng đã tải và tiếp tục ở đoạn bị đứt.

---

### 💡 Bí kíp Reset lại từ đầu: Dọn dẹp Dữ Lệu "Cứng"
Nếu bạn lỡ tay xóa bậy, chỉnh sửa bậy làm data hỏng, hãy dọn sạch các file do code sinh ra và làm lại pipeline từ đầu. Gõ lệnh:

```bash
# Lệnh này sẽ XÓA TOÀN BỘ dữ liệu nến, feature, nhãn đã làm. (Giữ lại data TICK gốc để khỏi mất công download).
rm -rf data/ohlcv/* data/features/* data/labels/*
# Sau đó làm lại Bước 2, Bước 3, Bước 4.
```
