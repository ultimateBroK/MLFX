# MLFX - Bắt đầu nhanh

Tài liệu này là **điểm bắt đầu chuẩn** để chạy MLFX theo luồng ngắn nhất có thể.  
Nếu bạn chỉ muốn đi từ trạng thái **chưa có dữ liệu** đến **có kết quả backtest đầu tiên**, hãy làm theo file này.

## Khi nào nên đọc file này

Đọc `QUICKSTART.md` khi bạn muốn:

- Chạy thử kho mã nhanh
- Biết đúng thứ tự lệnh cần chạy
- Thấy mỗi bước tạo ra những gì
- Có một lộ trình bắt đầu ngắn gọn trước khi đọc tài liệu chi tiết hơn

Nếu bạn cần giải thích sâu hơn:

- Xem [NOOB_GUIDE.md](NOOB_GUIDE.md) để hiểu **vì sao** từng bước tồn tại
- Xem [../guides/USAGE_GUIDE.md](../guides/USAGE_GUIDE.md) để biết đầy đủ tham số dòng lệnh
- Xem [../guides/EVALUATION_GUIDE.md](../guides/EVALUATION_GUIDE.md) để hiểu cách đọc kết quả backtest
- Xem [../guides/TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md) khi gặp lỗi

---

## Điều kiện tối thiểu

- Đã cài `Pixi`
- Đang đứng tại thư mục gốc của kho mã `ML_FX`
- Chạy lệnh bằng `pixi run ...`

Cài môi trường:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

---

## Luồng chuẩn gồm 4 bước

Luồng tối thiểu:

```text
1. Tải dữ liệu     → download
2. Chuẩn bị dữ liệu → pipeline (OHLCV + đặc trưng + nhãn)
3. Huấn luyện       → train
4. Đánh giá         → evaluate (backtest + báo cáo)
```

---

## Bước 1 — Tải dữ liệu

Ví dụ tải dữ liệu cho `XAUUSD`:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
```

### Bước này làm gì

- Tải dữ liệu tick lịch sử từ nguồn dữ liệu
- Lưu dữ liệu thô dạng parquet vào `data/raw/{symbol}/`
- Lưu trạng thái tải để có thể tiếp tục nếu bị gián đoạn

### Kết quả mong đợi

Bạn sẽ thấy các tệp như:

- `data/raw/XAUUSD/YYYY-MM.parquet`
- `data/raw/XAUUSD/completed_months.json`

### Nếu muốn kiểm tra chất lượng dữ liệu thô

Bạn có thể chạy thêm bước kiểm tra:

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

Bước này không bắt buộc trong hướng dẫn bắt đầu nhanh, nhưng rất hữu ích nếu bạn nghi dữ liệu có khoảng trống hoặc tháng bị lỗi.

---

## Bước 2 — Chạy pipeline

Sau khi đã có dữ liệu thô, chạy pipeline để tạo OHLCV, đặc trưng và nhãn:

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
```

### Bước này làm gì

- Chuyển dữ liệu tick thành nến `OHLCV`
- Tạo các đặc trưng kỹ thuật và đặc trưng theo ngữ cảnh
- Tạo các nhãn như `label_5`, `label_10`, `label_20`

### Kết quả mong đợi

Bạn sẽ thấy dữ liệu trung gian ở:

- `data/ohlcv/XAUUSD/1H/`
- `data/features/XAUUSD/1H/`
- `data/labels/XAUUSD/1H/`

### Gợi ý

Nếu mới bắt đầu, hãy dùng khung thời gian `1H` vì:

- Nhẹ hơn các khung thời gian quá nhỏ
- Dễ đọc kết quả hơn
- Ít tốn tài nguyên hơn

---

## Bước 3 — Huấn luyện mô hình

Ví dụ huấn luyện bộ máy mặc định, dễ bắt đầu là `mlf`:

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
```

### Bước này làm gì

- Nạp tập dữ liệu đã gắn nhãn
- Chọn bộ máy huấn luyện
- Huấn luyện mô hình
- Lưu tệp đầu ra và siêu dữ liệu

### Kết quả mong đợi

Bạn sẽ thấy đầu ra trong:

- `outputs/models/XAUUSD/1H/label_10/`

### Bộ tham số mặc định nên dùng

- `--tf 1H`
- `--label label_10`
- `--backend mlf`

Đây là bộ tham số phù hợp để chạy thử lần đầu.

---

## Bước 4 — Đánh giá / Backtest

Sau khi huấn luyện xong, chạy bước đánh giá:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

### Bước này làm gì

- Backtest mô hình đã huấn luyện
- Nếu chưa có mô hình phù hợp, quy trình có thể quay về dùng nhãn làm mốc cơ sở
- Tạo báo cáo trực quan và các chỉ số tổng hợp

### Kết quả mong đợi

Bạn sẽ thấy báo cáo ở:

- `outputs/reports/XAUUSD/1H/label_10/model/R15/`

Thường có các tệp như:

- `*_candlestick.html`
- `*_equity.png`
- `*_heatmap.png`
- `*_trades.parquet`

Giao diện dòng lệnh cũng sẽ in ra:

- Tổng số lệnh
- Tỷ lệ thắng
- Hệ số lợi nhuận
- Lợi nhuận ròng
- Chỉ số Sharpe / Sortino / Calmar
- Vốn cuối kỳ

---

## Toàn bộ lệnh bắt đầu nhanh

Nếu bạn muốn sao chép một lần toàn bộ luồng tối thiểu:

```bash
pixi install
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

Nếu muốn cẩn thận hơn với dữ liệu thô:

```bash
pixi install
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx qa --symbol XAUUSD --asset-class fx
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

---

## Sau bước bắt đầu nhanh, nên đọc gì tiếp

### Nếu bạn là người mới hoàn toàn

Đọc tiếp:

- [NOOB_GUIDE.md](NOOB_GUIDE.md)

### Nếu bạn muốn biết từng lệnh và từng cờ

Đọc:

- [../guides/USAGE_GUIDE.md](../guides/USAGE_GUIDE.md)

### Nếu bạn muốn hiểu backtest đang đo điều gì

Đọc:

- [../guides/EVALUATION_GUIDE.md](../guides/EVALUATION_GUIDE.md)

### Nếu bạn muốn hiểu dữ liệu, đặc trưng và kiến trúc hệ thống

Đọc:

- [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
- [../reference/FEATURE_REFERENCE.md](../reference/FEATURE_REFERENCE.md)
- [../reference/GLOSSARY.md](../reference/GLOSSARY.md)

---

## Lỗi thường gặp khi chạy nhanh

### `pixi: command not found`

Bạn chưa cài `Pixi` hoặc shell chưa được nạp lại.

### Huấn luyện lỗi vì thiếu tệp

Thông thường là do bạn chưa chạy `download` hoặc `pipeline` trước đó.

### Đánh giá không sinh báo cáo

Hãy kiểm tra:

- Đã có parquet trong `data/labels/{symbol}/{tf}/` chưa
- Mô hình đã được huấn luyện chưa
- `label_col` có đúng không

### Muốn dọn đầu ra cũ

Chạy:

```bash
pixi run clean-generated
```

Lệnh này dọn vùng nhớ đệm và các đầu ra được tạo ra, nhưng không đụng đến `data/raw/`.

---

## Luồng nhập môn chuẩn

File này là **hướng dẫn bắt đầu nhanh chuẩn** của tài liệu tiếng Việt.  
Các tài liệu khác nên:

- Dẫn liên kết về file này khi cần luồng bắt đầu nhanh
- Không lặp lại toàn bộ chuỗi lệnh ở đây trừ khi thật sự cần thiết

---

## Tóm tắt một dòng

Nếu bạn chỉ cần chạy MLFX lần đầu, hãy đi đúng thứ tự:

```text
download → pipeline → train → evaluate
```
