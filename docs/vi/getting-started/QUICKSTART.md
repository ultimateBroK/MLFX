# MLFX - Quickstart

Tài liệu này là **điểm bắt đầu chuẩn** để chạy MLFX theo workflow ngắn nhất có thể.  
Nếu bạn chỉ muốn đi từ **không có dữ liệu** đến **có kết quả backtest đầu tiên**, hãy làm theo file này.

## Khi nào nên đọc file này

Đọc `QUICKSTART.md` khi bạn muốn:
- Chạy thử repo nhanh
- Biết đúng thứ tự lệnh cần chạy
- Thấy mỗi bước tạo ra gì
- Có một luồng bắt đầu ngắn gọn trước khi đọc tài liệu chi tiết hơn

Nếu bạn cần giải thích sâu hơn:
- Xem [NOOB_GUIDE.md](NOOB_GUIDE.md) để hiểu **vì sao** từng bước tồn tại
- Xem [../guides/USAGE_GUIDE.md](../guides/USAGE_GUIDE.md) để biết đầy đủ tham số CLI
- Xem [../guides/EVALUATION_GUIDE.md](../guides/EVALUATION_GUIDE.md) để đọc kết quả backtest
- Xem [../guides/TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md) khi gặp lỗi

---

## Điều kiện tối thiểu

- Đã cài `Pixi`
- Đang đứng tại thư mục gốc của repo `ML_FX`
- Chạy lệnh bằng `pixi run ...`

Cài environment:

```/dev/null/quickstart-install.sh#L1-2
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

---

## Workflow chuẩn 4 bước

Luồng tối thiểu:

```/dev/null/quickstart-flow.txt#L1-4
1. Download   → tải tick data
2. Pipeline   → tạo OHLCV + features + labels
3. Train      → huấn luyện model
4. Evaluate   → backtest và sinh report
```

---

## Bước 1 — Tải dữ liệu

Ví dụ tải dữ liệu cho `XAUUSD`:

```/dev/null/quickstart-download.sh#L1-1
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
```

### Bước này làm gì
- Tải historical tick data từ nguồn dữ liệu
- Lưu parquet raw vào `data/raw/{symbol}/`
- Lưu trạng thái download để có thể resume

### Kết quả mong đợi
Bạn sẽ thấy các file như:
- `data/raw/XAUUSD/YYYY-MM.parquet`
- `data/raw/XAUUSD/completed_months.json`

### Nếu muốn kiểm tra chất lượng raw data
Có thể chạy thêm bước QA:

```/dev/null/quickstart-qa.sh#L1-1
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

Bước này không bắt buộc cho quickstart, nhưng hữu ích nếu bạn nghi dữ liệu có gap.

---

## Bước 2 — Chạy pipeline

Sau khi có raw data, chạy pipeline để tạo OHLCV, feature và label:

```/dev/null/quickstart-pipeline.sh#L1-1
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
```

### Bước này làm gì
- Resample tick data thành nến `OHLCV`
- Tạo feature kỹ thuật và feature ngữ cảnh
- Tạo label như `label_5`, `label_10`, `label_20`

### Kết quả mong đợi
Bạn sẽ thấy dữ liệu trung gian ở:
- `data/ohlcv/XAUUSD/1H/`
- `data/features/XAUUSD/1H/`
- `data/labels/XAUUSD/1H/`

### Gợi ý
Nếu mới bắt đầu, hãy dùng timeframe `1H` vì:
- Nhẹ hơn timeframe nhỏ
- Dễ đọc kết quả hơn
- Ít tốn tài nguyên hơn

---

## Bước 3 — Train model

Ví dụ train backend mặc định dễ bắt đầu là `mlf`:

```/dev/null/quickstart-train.sh#L1-1
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
```

### Bước này làm gì
- Nạp dataset đã được gắn label
- Chọn backend train
- Train model
- Lưu artifact và metadata

### Kết quả mong đợi
Bạn sẽ thấy output trong:
- `outputs/models/XAUUSD/1H/`

### Lựa chọn mặc định nên dùng
- `--tf 1H`
- `--label label_10`
- `--backend mlf`

Đây là bộ thông số phù hợp để chạy thử lần đầu.

---

## Bước 4 — Evaluate / Backtest

Sau khi train xong, chạy evaluate:

```/dev/null/quickstart-evaluate.sh#L1-1
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

### Bước này làm gì
- Backtest model đã train
- Nếu chưa có model phù hợp, workflow có thể fallback sang labels
- Sinh báo cáo trực quan và metrics tổng hợp

### Kết quả mong đợi
Bạn sẽ thấy report ở:
- `outputs/reports/XAUUSD/1H/`

Thường có các file như:
- `*_candlestick.html`
- `*_equity.png`
- `*_heatmap.png`

CLI cũng sẽ in ra:
- Tổng số lệnh
- Win rate
- Profit factor
- Net profit
- Sharpe / Sortino / Calmar
- Final capital

---

## Toàn bộ lệnh quickstart

Nếu bạn muốn copy một lần toàn bộ luồng tối thiểu:

```/dev/null/quickstart-all.sh#L1-5
pixi install
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

Nếu muốn cẩn thận hơn với dữ liệu raw:

```/dev/null/quickstart-all-with-qa.sh#L1-6
pixi install
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx qa --symbol XAUUSD --asset-class fx
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

---

## Sau quickstart, nên đọc gì tiếp

### Nếu bạn là người mới hoàn toàn
Đọc tiếp:
- [NOOB_GUIDE.md](NOOB_GUIDE.md)

### Nếu bạn muốn biết từng command và flag
Đọc:
- [../guides/USAGE_GUIDE.md](../guides/USAGE_GUIDE.md)

### Nếu bạn muốn hiểu backtest đang đo cái gì
Đọc:
- [../guides/EVALUATION_GUIDE.md](../guides/EVALUATION_GUIDE.md)

### Nếu bạn muốn hiểu dữ liệu/feature/kiến trúc hệ thống
Đọc:
- [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
- [../reference/FEATURE_REFERENCE.md](../reference/FEATURE_REFERENCE.md)
- [../reference/GLOSSARY.md](../reference/GLOSSARY.md)

---

## Lỗi thường gặp khi chạy nhanh

### `pixi: command not found`
Bạn chưa cài `Pixi` hoặc shell chưa reload.

### Train lỗi vì thiếu file
Thường là bạn chưa chạy `download` hoặc `pipeline` trước.

### Evaluate không sinh report
Hãy kiểm tra:
- có parquet trong `data/labels/{symbol}/{tf}/` chưa
- model đã train chưa
- `label_col` có đúng không

### Muốn dọn output cũ
Chạy:

```/dev/null/quickstart-clean.sh#L1-1
pixi run clean-generated
```

Lệnh này dọn cache và output sinh ra, nhưng không đụng `data/raw/`.

---

## Canonical onboarding flow

File này là **quickstart canonical** của docs tiếng Việt.  
Các tài liệu khác nên:
- link về file này khi cần luồng bắt đầu nhanh
- không lặp lại toàn bộ chuỗi lệnh quickstart trừ khi thật sự cần thiết

---

## Tóm tắt 1 dòng

Nếu bạn chỉ cần chạy MLFX lần đầu, hãy chạy theo đúng thứ tự:

```/dev/null/quickstart-summary.txt#L1-1
download → pipeline → train → evaluate
```
