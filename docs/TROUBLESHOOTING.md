# Hướng dẫn Khắc phục Lỗi (Troubleshooting)

Đôi khi, bạn có thể gặp phải các sự cố do thiết lập môi trường hoặc giới hạn bộ nhớ. Nếu bạn thấy lỗi màu đỏ trong terminal, hãy kiểm tra hướng dẫn này để tìm cách khắc phục nhanh.

---

### 🚨 Lỗi 1: `pixi: command not found`
*   **Triệu chứng**: Terminal báo lỗi khi bạn cố gắng chạy bất kỳ lệnh `pixi` nào.
*   **Nguyên nhân**: Pixi chưa được cài đặt, hoặc bạn chưa khởi động lại terminal của mình sau khi cài đặt.
*   **Cách khắc phục**:
    1. Làm theo kỹ các bước cài đặt trong tài liệu [Hướng dẫn Sử dụng](USAGE_GUIDE.md).
    2. Đóng hoàn toàn Terminal hoặc VSCode của bạn và mở lại.

### 🚨 Lỗi 2: Thiếu Package (`ModuleNotFoundError`)
*   **Triệu chứng**: Bạn thấy lỗi dạng như `ModuleNotFoundError: No module named 'xgboost'`.
*   **Nguyên nhân**: Quá trình cài đặt môi trường của bạn chưa tải xuống đầy đủ các thư viện cần thiết cho dự án.
*   **Cách khắc phục**: Chạy lệnh này để đồng bộ hóa môi trường của bạn:
    ```bash
    pixi install
    ```

### 🚨 Lỗi 3: Lỗi Không tìm thấy Tệp (`SystemExit: No feature files found`)
*   **Triệu chứng**: Bạn kích hoạt script phân loại nhãn (labeling) hoặc huấn luyện (training), và nó phàn nàn về việc thiếu tệp hoặc DataFrames trống.
*   **Nguyên nhân**: Bạn đã bỏ lỡ một bước. Ví dụ: bạn đang cố gắng tạo nhãn trước khi làm bước trích xuất đặc trưng (Feature Engineering).
*   **Cách khắc phục**: Chuẩn theo từng bước của Pipeline với thứ tự nghiệm ngặt được định ra trong [Hướng dẫn Sử dụng](USAGE_GUIDE.md): Tải Dữ Liệu -> Resample -> Tạo Features -> Gán Nhãn.

### 🚨 Lỗi 4: Hết Bộ Nhớ / Crashes (Out Of Memory - OOM)
*   **Triệu chứng**: Máy tính của bạn hết RAM và tự động đóng/tắt script.
*   **Nguyên nhân**: Bạn đang cố gắng tải toàn bộ hơn 10 năm dữ liệu tick `.parquet` (hơn 20GB) vào RAM cùng một lúc.
*   **Cách khắc phục**: Trong code hãy luôn sử dụng hàm `scan_parquet()` (Thay vì `read_parquet()`) của thư viện Polars — đây là công nghệ Lazy Evaluation có thể xử lý dữ liệu qua từng phần nhỏ (chunk) mà không bị nghẽn tắc bộ nhớ máy tính.

### 🚨 Lỗi 5: Đang Tải bỗng Dừng Không Lý Do hoặc Mạng Gián Đoạn
*   **Triệu chứng**: `download_data.py` tự dưng tắc rị trong quá trình đang thực hiện Tải Dữ liệu lịch sử.
*   **Cách khắc phục**: Script đã được trang bị cơ chế tự bám sát theo tệp `completed_months.json`. Bạn CHỈ CẦN chạy lại lệnh `pixi run python pipeline/download_data.py`, và chương trình sẽ tự gánh vác phần tải của phần dở giang trước đó.

---

### 💡 Mẹo Nhanh: Làm Thế Nào Để Reload Lại Mọi Thứ Từ Số 0
Nếu chẳng may bạn chạy sai và làm hỏng mất một vài files dữ liệu (Candle / feature / label), bạn có hoàn thoàn quyền xóa các kho Cache rác này để tiếp tục thử nghiệm lại như mới mà **Không cần Mất Càng** load lại Data Ticks Thô từ ban đầu.

```bash
# Lệnh dưới giúp xóa mọi Candle, feature và label được gen ra bởi bộ quét.
# Đảm chứng dữ liệu Tick raw thô (File Gốc) đang được An Toàn cất giữ.
rm -rf data/ohlcv/* data/features/* data/labels/*

# Ngay sau đây, có thể hoàn toàn an trí chạy Script -> Resampling, Features, Gán Nhãn lại từ đầu.
```
