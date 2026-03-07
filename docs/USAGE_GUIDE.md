# ML_FX - Hướng dẫn cấu hình và sử dụng

Tài liệu này mô tả cách vận hành dự án theo workflow chuẩn dùng `Pixi`.

Tài liệu liên quan:
- [README.md](../README.md)
- [NOOB_GUIDE.md](NOOB_GUIDE.md)
- [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 1. Cài đặt môi trường

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

Nguyên tắc vận hành:
- luôn chạy lệnh qua `pixi run`
- Python và dependency được quản lý qua `pyproject.toml`
- không cần `uv` hoặc `venv` riêng cho workflow chuẩn

Pixi tasks hữu ích:

```bash
pixi run test
pixi run verify
pixi run clean-generated
```

## 2. Entrypoint chính

- `pixi run mlfx`: CLI hợp nhất
- `pixi run mlfx-tui`: TUI

Xem help:

```bash
pixi run mlfx --help
pixi run mlfx pipeline --help
```

## 3. `config.toml`

`config.toml` được đọc bởi CLI và TUI để nạp giá trị mặc định.

Ví dụ:

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

Các khóa cần nhớ:
- `asset_class`: `fx`, `crypto`
- `timeframe`: `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`
- `pivot_type`: `traditional`, `fibonacci`, `woodie`, `classic`, `demark`, `camarilla`
- `pivot_anchor`: `daily`, `weekly`, `monthly`
- `label_col`: `label_5`, `label_10`, `label_20`
- `backend`: `mlf`, `lstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`

## 4. TUI

Khởi chạy:

```bash
pixi run mlfx-tui
```

TUI hiện có 4 tab:
- `Download Data`
- `Pipeline`
- `Train Model`
- `Backtest`

Phím tắt:
- `q`: thoát
- `d`: đổi dark/light mode

## 5. CLI theo từng bước

### 5.1 Download dữ liệu tick

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
```

Mục đích:
- tải tick data về `data/raw/`
- lưu state để resume nếu download bị gián đoạn

Tham số chính:
- `--symbol`
- `--asset-class`
- `--start-year`
- `--start-month`
- `--concurrency`
- `--force`

Artifacts:
- `data/raw/{symbol}/YYYY-MM.parquet`
- `data/raw/{symbol}/completed_months.json`

### 5.2 Audit dữ liệu raw

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

Mục đích:
- kiểm tra gap đáng kể
- xuất báo cáo chất lượng dữ liệu

Artifact:
- `data/raw/{symbol}/{symbol}_Data_Quality_Report.md`

### 5.3 Chạy pipeline

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
```

Ví dụ bỏ qua từng stage:

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-resample
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-features
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-labels
```

Tham số chính:
- `--symbol`
- `--tf`
- `--pivot`
- `--anchor`
- `--atr-period`
- `--atr-mult`
- `--force`
- `--skip-resample`
- `--skip-features`
- `--skip-labels`

Artifacts:
- `data/ohlcv/{symbol}/{tf}/`
- `data/features/{symbol}/{tf}/`
- `data/labels/{symbol}/{tf}/`

### 5.4 Train model

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf --n-trials 15 --n-splits 5
```

Backend hiện hỗ trợ qua CLI/TUI:
- `mlf`
- `lstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

Tham số chính:
- `--symbol`
- `--tf`
- `--label`
- `--backend`
- `--n-trials`
- `--n-splits`
- `--force`

Artifacts:
- `outputs/models/{symbol}/{tf}/`

Lưu ý:
- `n_trials` hiện có ý nghĩa nhất với backend `mlf`
- `n_splits` được map khác nhau tùy backend trong code

### 5.5 Evaluate và sinh báo cáo

```bash
pixi run mlfx evaluate \
  --symbol XAUUSD \
  --tf 1H \
  --label label_10 \
  --capital 10000 \
  --risk 1.0 \
  --commission 0.1 \
  --tp 1.5 \
  --sl 1.0 \
  --slippage 0.0
```

Tham số chính:
- `--symbol`
- `--tf`
- `--label`
- `--capital`
- `--risk`
- `--commission`
- `--tp`
- `--sl`
- `--slippage`

Artifacts mặc định:
- `outputs/reports/{symbol}_{tf}_{label}_R{tp*10}_candlestick.html`
- `outputs/reports/{symbol}_{tf}_{label}_R{tp*10}_equity.png`
- `outputs/reports/{symbol}_{tf}_{label}_R{tp*10}_heatmap.png`

## 6. Luồng chạy đầy đủ

```bash
# 1) Tải dữ liệu tick
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024

# 2) Audit dữ liệu raw
pixi run mlfx qa --symbol XAUUSD --asset-class fx

# 3) OHLCV + features + labels
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --pivot traditional --anchor daily --atr-mult 0.5

# 4) Train
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf --n-trials 15 --n-splits 5

# 5) Evaluate
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

## 7. Checklist xác minh nhanh

Sau mỗi bước, nên kiểm tra:
- sau `download`: có file parquet trong `data/raw/{symbol}/`
- sau `qa`: có file báo cáo chất lượng dữ liệu
- sau `pipeline`: có parquet trong `data/ohlcv/`, `data/features/`, `data/labels/`
- sau `train`: có artifact mới trong `outputs/models/{symbol}/{tf}/`
- sau `evaluate`: có HTML/PNG mới trong `outputs/reports/`

## 8. Cleanup an toàn

Dọn cache và generated artifacts phổ biến:

```bash
pixi run clean-generated
```

Khi nào nên dùng:
- trước khi chạy lại benchmark hoặc test clean-room
- sau các lần train dài tạo nhiều `lightning_logs`
- khi workspace có quá nhiều output/report cũ gây khó kiểm tra

Nếu cần xử lý sự cố, xem [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
