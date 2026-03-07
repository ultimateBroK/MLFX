# ML_FX - Hướng dẫn cấu hình và sử dụng

Tài liệu này mô tả cách chạy dự án bằng TUI và CLI theo trạng thái code hiện tại.

Tài liệu liên quan:
- [README.md](../README.md)
- [NOOB_GUIDE.md](NOOB_GUIDE.md)
- [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 1. Cài đặt môi trường

Repo nên được chạy bằng `Pixi`.

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

Lưu ý:
- [pyproject.toml](../pyproject.toml) khai báo `requires-python >= 3.11`
- môi trường Pixi hiện pin Python `3.13`
- cách đáng tin cậy nhất là luôn chạy lệnh qua `pixi run`

## 2. Chạy TUI

```bash
pixi run python main.py
```

TUI có 4 tab:
- `Download Data`
- `Pipeline`
- `Train Model`
- `Backtest`

Phím tắt:
- `q`: thoát
- `d`: đổi dark/light mode

[main.py](../main.py) sẽ đọc [config.toml](../config.toml) lúc khởi động để tự điền giá trị mặc định cho các form.

## 3. `config.toml`

Ví dụ cấu hình đang dùng:

```toml
[download]
symbol = "XAUUSD"
asset_class = "fx"
start_year = 2015
start_month = 1
concurrency = 20

[pipeline]
symbol = "XAUUSD"
timeframe = "1H"
pivot_type = "traditional"
pivot_anchor = "daily"

[train]
symbol = "XAUUSD"
timeframe = "1H"
backend = "mlf"
n_splits = 5

[backtest]
symbol = "XAUUSD"
timeframe = "1H"
label_col = "label_10"
```

Các giá trị chính:
- `asset_class`: `fx`, `crypto`
- `timeframe`: `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`
- `pivot_type`: `traditional`, `fibonacci`, `woodie`, `classic`, `demark`, `camarilla`
- `pivot_anchor`: `daily`, `weekly`, `monthly`
- `label_col`: `label_5`, `label_10`, `label_20`
- `backend` trong TUI:
  - `mlf`
  - `lstm`
  - `transformer`
  - `cnn_lstm`
  - `sgd`
  - `stats`
  - `neuralforecast`

## 4. Luồng chạy đầy đủ

Khối lệnh dưới đây là luồng chuẩn để tải dữ liệu, tạo feature, gắn nhãn, train, rồi backtest:

```bash
# 1) Tải dữ liệu tick
pixi run python pipeline/download_data.py --symbol XAUUSD --asset-class fx --start-year 2024

# 2) Kiểm tra chất lượng dữ liệu raw
pixi run python pipeline/qa_data.py --symbol XAUUSD --asset-class fx

# 3) Resample sang OHLCV
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H

# 4) Tạo feature
pixi run python pipeline/features.py --symbol XAUUSD --tf 1H --pivot traditional --anchor daily

# 5) Gắn nhãn
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H --horizons 5 10 20 --atr-mult 0.5

# 6) Train một backend mặc định
pixi run python models/ml_models.py --symbol XAUUSD --tf 1H --label label_10 --n-trials 15 --n-splits 5

# 7) Backtest trên một file label cụ thể
pixi run python eval/run_eval.py \
  --data data/labels/XAUUSD/1H/2024-01.parquet \
  --symbol XAUUSD \
  --tf 1H \
  --label label_10 \
  --tp 1.5 \
  --sl 1.0 \
  --outdir outputs/reports
```

## 5. CLI theo từng bước

### 5.1 Tải dữ liệu tick

```bash
pixi run python pipeline/download_data.py [OPTIONS]
```

Tham số:
- `--symbol`: mặc định `XAUUSD`
- `--start-year`: mặc định `2015`
- `--start-month`: mặc định `1`
- `--end-year`: mặc định năm hiện tại
- `--end-month`: mặc định tháng hiện tại
- `--asset-class`: `fx` hoặc `crypto`
- `--concurrency`: mặc định `20`
- `--force-repair`: ép kiểm tra lại các tháng đã xác nhận

Output:
- `data/raw/{symbol}/YYYY-MM.parquet`
- `data/raw/{symbol}/completed_months.json`

### 5.2 Kiểm tra chất lượng dữ liệu raw

```bash
pixi run python pipeline/qa_data.py --symbol XAUUSD --asset-class fx
```

Script này đọc `completed_months.json`, rà soát dữ liệu tick, và tạo báo cáo QA dạng Markdown trong thư mục dữ liệu raw.

### 5.3 Resample sang OHLCV

```bash
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H
pixi run python pipeline/resample.py --symbol XAUUSD
```

Tham số:
- `--symbol`
- `--tf`: bỏ trống để chạy toàn bộ timeframe
- `--force`

Output:
- `data/ohlcv/{symbol}/{tf}/YYYY-MM.parquet`

### 5.4 Tạo feature

```bash
pixi run python pipeline/features.py --symbol XAUUSD --tf 1H --pivot traditional --anchor daily
```

Tham số:
- `--symbol`
- `--tf`
- `--pivot`
- `--anchor`
- `--force`

Output:
- `data/features/{symbol}/{tf}/YYYY-MM.parquet`

### 5.5 Gắn nhãn

```bash
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H --horizons 5 10 20 --atr-mult 0.5
```

Tham số:
- `--symbol`
- `--tf`
- `--horizons`
- `--atr-mult`
- `--force`

Output:
- `data/labels/{symbol}/{tf}/YYYY-MM.parquet`

## 6. Train model

### 6.1 Backend `mlf`

```bash
pixi run python models/ml_models.py --symbol XAUUSD --tf 1H --label label_10 --n-trials 15 --n-splits 5
```

Phù hợp khi bạn muốn baseline chính dùng `MLForecast + LightGBM`.

### 6.2 Backend `lstm`

```bash
pixi run python models/lstm.py --symbol XAUUSD --tf 1H --label label_10
```

### 6.3 Backend `transformer`

```bash
pixi run python models/transformer.py --symbol XAUUSD --tf 1H --label label_10
```

### 6.4 Backend `cnn_lstm`

```bash
pixi run python models/cnn_lstm.py --symbol XAUUSD --tf 1H --label label_10
```

### 6.5 Backend `sgd`

```bash
pixi run python models/online_sgd.py --symbol XAUUSD --tf 1H --label label_10
```

### 6.6 Backend `stats`

```bash
pixi run python models/stats_baseline.py --symbol XAUUSD --tf 1H --label label_10 --n-splits 5
```

### 6.7 Backend `neuralforecast`

```bash
pixi run python models/neural_forecast.py --symbol XAUUSD --tf 1H --label label_10 --n-windows 5 --input-size 48 --max-steps 200
```

Các backend hiện lưu model và metrics trong:
- `outputs/models/{symbol}/{tf}/`

Ví dụ tên file:
- `ml_models_label_10.pkl`
- `lstm_label_10.pt`
- `transformer_label_10.pt`
- `cnn_lstm_label_10.pt`
- `online_sgd_label_10.pkl`
- `stats_baseline_label_10.pkl`
- `neural_forecast_label_10.pkl`

## 7. Backtest và đánh giá

```bash
pixi run python eval/run_eval.py \
  --data data/labels/XAUUSD/1H/2024-01.parquet \
  --symbol XAUUSD \
  --tf 1H \
  --label label_10 \
  --tp 1.5 \
  --sl 1.0 \
  --slippage 0.0 \
  --outdir outputs/reports
```

Tham số chính:
- `--data`: file parquet đã gắn nhãn
- `--symbol`
- `--tf`
- `--label`
- `--tp`
- `--sl`
- `--slippage`
- `--outdir`

Output mặc định:
- `outputs/reports/{prefix}_candlestick.html`
- `outputs/reports/{prefix}_equity.png`
- `outputs/reports/{prefix}_heatmap.png`

Giải thích ý nghĩa metric và cách đọc biểu đồ nằm trong [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md).

## 8. Lưu ý vận hành

- Chạy pipeline theo đúng thứ tự: raw -> ohlcv -> features -> labels -> train -> backtest
- Nếu training báo thiếu file, kiểm tra lại thư mục `data/features/` hoặc `data/labels/`
- Nếu download bị gián đoạn, có thể chạy lại [pipeline/download_data.py](../pipeline/download_data.py); script sẽ tiếp tục dựa trên `completed_months.json`
- Nếu cần làm sạch dữ liệu trung gian, xem [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
