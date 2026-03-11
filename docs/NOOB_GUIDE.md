# MLFX - Hướng dẫn cho người mới

Nếu bạn mới vào repo, hãy đọc tài liệu này trước. Mục tiêu là hiểu dữ liệu đi đâu, vì sao phải chạy đúng thứ tự, và cách bắt đầu an toàn bằng `Pixi`.

## 1. Dự án này làm gì

MLFX là một pipeline nghiên cứu cho dữ liệu giá:
- tải tick data lịch sử
- gom thành OHLCV
- tạo feature kỹ thuật và feature theo bối cảnh ICT
- gắn nhãn hướng giá tương lai
- train model
- backtest và xuất báo cáo

Nó là môi trường nghiên cứu và đánh giá, không phải bot giao dịch live hoàn chỉnh.

## 2. Pipeline tổng quát (4 bước chính)

```text
1. Tải dữ liệu   → download
2. Chuẩn bị      → pipeline (OHLCV + features + labels)
3. Train model   → train
4. Xem kết quả   → evaluate (backtest)
```

Sau `evaluate`, CLI in bảng metrics và đường dẫn biểu đồ. Mặc định backtest **model** nếu đã train; nếu chưa train thì backtest **labels** (baseline).

Trong code, các bước này nằm trong:
- `mlfx.ingestion`
- `mlfx.pipeline`
- `mlfx.training`
- `mlfx.evaluation`

## 3. Vì sao phải chạy đúng thứ tự

### Tick -> QA

Sau khi download, nên audit raw data để phát hiện gap, tháng lỗi, hoặc dữ liệu bất thường trước khi đi tiếp.

### Tick -> OHLCV

Tick data rất dày. Resampling biến chúng thành nến như `1m`, `5m`, `1H` để các bước sau dễ xử lý hơn.

### OHLCV -> Features

Feature engineering thêm ngữ cảnh như:
- session theo `ICT Killzone`
- support/resistance
- pivot points
- RSI, MACD, ATR, EMA

### Features -> Labels

Các cột như `label_5`, `label_10`, `label_20` biến dữ liệu thành bài toán supervised learning.

### Labels -> Train

CLI hiện hỗ trợ các backend:
- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

### Train -> Xem kết quả (evaluate)

`evaluate` = backtest và sinh báo cáo. Mặc định backtest **model** đã train; nếu chưa train thì backtest **labels** (baseline). Kết quả:
- bảng metrics in ra console
- candlestick HTML, equity PNG, heatmap PNG trong `outputs/reports/`
- khi backtest model: so sánh với labels (model tốt hơn / kém hơn bao nhiêu R)

## 4. Cách bắt đầu nhanh

Nếu chỉ muốn chạy thử:

```bash
pixi install
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

(Bỏ qua `qa` khi mới bắt đầu; dùng khi cần audit dữ liệu.)

## 5. Kết quả nên thấy sau mỗi bước

- sau `download`: có parquet trong `data/raw/{symbol}/`
- sau `qa`: có báo cáo markdown trong `data/raw/{symbol}/`
- sau `pipeline`: có parquet trong `data/ohlcv/`, `data/features/`, `data/labels/`
- sau `train`: có artifact trong `outputs/models/{symbol}/{tf}/`
- sau `evaluate`: có HTML/PNG trong `outputs/reports/{symbol}/{tf}/`

## 6. Điều nên nhớ

- nếu train lỗi vì thiếu file, thường là bạn chưa chạy `mlfx pipeline`
- `outputs/models/{symbol}/{tf}/` lưu model và metrics
- `outputs/reports/{symbol}/{tf}/` lưu báo cáo backtest
- `pixi run clean-generated` dọn cache và output cũ mà không đụng `data/raw/`

## 7. Đọc tiếp gì

- [USAGE_GUIDE.md](USAGE_GUIDE.md): cách chạy từng lệnh
- [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md): cách đọc kết quả backtest
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md): xử lý lỗi môi trường và dữ liệu
- [GLOSSARY.md](GLOSSARY.md): thuật ngữ thường gặp
