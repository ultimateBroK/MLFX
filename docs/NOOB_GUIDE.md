# ML_FX - Hướng dẫn cho người mới

Nếu bạn mới vào repo, hãy đọc tài liệu này trước khi chạy lệnh. Mục tiêu là hiểu dự án đang làm gì, dữ liệu đi qua những bước nào, và vì sao phải chạy pipeline đúng thứ tự.

## 1. Dự án này làm gì

ML_FX là một pipeline nghiên cứu cho dữ liệu giá:
- lấy dữ liệu tick lịch sử
- gom dữ liệu thành nến OHLCV
- tạo feature kỹ thuật
- gắn nhãn hướng giá trong tương lai
- huấn luyện mô hình
- backtest trên dữ liệu đã gắn nhãn

Nó không phải là một bot giao dịch tự động hoàn chỉnh đang sẵn sàng chạy live.

## 2. Pipeline tổng quát

```text
Tick data
  -> OHLCV
  -> Features
  -> Labels
  -> Train
  -> Backtest
```

Mỗi bước tương ứng với một nhóm file:
- `pipeline/download_data.py`
- `pipeline/resample.py`
- `pipeline/features.py`
- `pipeline/labels.py`
- `models/*.py`
- `eval/run_eval.py`

## 3. Vì sao phải đi theo đúng thứ tự

### 3.1 Tick -> OHLCV

Dữ liệu tick rất dày và nhiều nhiễu. `resample.py` chuyển tick thành nến như `1m`, `5m`, `1H` để các bước sau dễ xử lý hơn.

### 3.2 OHLCV -> Features

`features.py` gắn thêm ngữ cảnh vào mỗi cây nến, ví dụ:
- trạng thái session theo `ICT Killzone`
- mức `Support/Resistance`
- `Pivot Points`
- indicator phổ biến như RSI, MACD, ATR, EMA

Không có feature thì model chỉ thấy giá thô và rất khó học được cấu trúc thị trường.

### 3.3 Features -> Labels

`labels.py` sinh nhãn như `label_5`, `label_10`, `label_20`. Mỗi nhãn mô tả hướng giá sau một số lượng nến nhìn trước.

Đây là bước tạo mục tiêu để bài toán trở thành supervised learning.

### 3.4 Labels -> Train

Các file trong `models/` đọc dữ liệu đã gắn nhãn và huấn luyện backend tương ứng. Repo hiện có nhiều backend khác nhau như:
- `ml_models.py`
- `lstm.py`
- `transformer.py`
- `cnn_lstm.py`
- `online_sgd.py`
- `stats_baseline.py`
- `neural_forecast.py`

### 3.5 Train -> Backtest

`eval/run_eval.py` và `eval/backtest.py` dùng cột tín hiệu để mô phỏng giao dịch, rồi `viz/charts.py` tạo báo cáo:
- candlestick HTML
- equity curve PNG
- heatmap PNG

## 4. Cách bắt đầu nhanh

Nếu bạn chỉ muốn chạy thử repo:

```bash
pixi install
pixi run python main.py
```

Trong TUI, bạn có thể đi theo thứ tự:
1. `Download Data`
2. `Pipeline`
3. `Train Model`
4. `Backtest`

Nếu bạn thích CLI, xem `USAGE_GUIDE.md`.

## 5. Những điều nên nhớ

- Nếu thiếu file ở bước train, nguyên nhân thường là chưa chạy `features.py` hoặc `labels.py`
- `outputs/models/` là nơi lưu model và metrics
- `outputs/reports/` là nơi lưu báo cáo backtest
- `agent/` hiện chưa phải phần hoàn chỉnh để sử dụng như tính năng chính

## 6. Nên đọc tiếp gì

- `USAGE_GUIDE.md`: cách chạy từng lệnh
- `EVALUATION_GUIDE.md`: cách đọc kết quả backtest
- `TROUBLESHOOTING.md`: xử lý lỗi môi trường và dữ liệu
- `GLOSSARY.md`: thuật ngữ thường gặp
