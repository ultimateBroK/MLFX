# MLFX - Hướng dẫn cấu hình và sử dụng

Tài liệu này là **manual vận hành CLI** cho MLFX.

Nó tập trung vào:

- cần chạy lệnh nào
- tham số nào quan trọng
- mỗi bước tạo ra artifact gì
- khi nào nên dùng từng command trong workflow chuẩn

Nếu bạn muốn đi theo lối bắt đầu nhanh nhất, hãy đọc:

- [Quickstart](../getting-started/QUICKSTART.md)

Nếu bạn là người mới và muốn hiểu **vì sao** workflow được tổ chức theo thứ tự hiện tại, hãy đọc:

- [Hướng dẫn cho người mới](../getting-started/NOOB_GUIDE.md)

## Tài liệu liên quan

- [Docs Hub tiếng Việt](../README.md)
- [Quickstart](../getting-started/QUICKSTART.md)
- [Hướng dẫn cho người mới](../getting-started/NOOB_GUIDE.md)
- [Hướng dẫn đánh giá](EVALUATION_GUIDE.md)
- [Khắc phục sự cố](TROUBLESHOOTING.md)
- [Tham chiếu cấu hình](../reference/CONFIG_REFERENCE.md)
- [Tham chiếu API](../reference/API_REFERENCE.md)
- [Tham chiếu Feature](../reference/FEATURE_REFERENCE.md)

---

## 1. Cài đặt môi trường

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

### Nguyên tắc vận hành

- Kuôn chạy lệnh qua `pixi run`
- Python và dependency được quản lý qua `pyproject.toml`
- Workflow chuẩn không yêu cầu tự dựng `uv` hoặc `venv` riêng

### Pixi tasks hữu ích

```bash
pixi run test
pixi run verify
pixi run clean-generated
```

---

## 2. Entrypoint chính

- `pixi run mlfx`: CLI hợp nhất

### Xem trợ giúp

```bash
pixi run mlfx --help
pixi run mlfx pipeline --help
```

---

## 3. `config.toml`

`config.toml` được đọc bởi CLI để nạp giá trị mặc định.

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
symbol          = "XAUUSD"
timeframe       = "1H"
label_col       = "label_10"
tp_r            = 1.5
sl_r            = 1.0
initial_capital = 10000.0
risk_pct        = 1.0
commission      = 0.1
```

### Các khóa cần nhớ

- `asset_class`: `fx`, `crypto`
- `timeframe`: `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`
- `pivot_type`: `traditional`, `fibonacci`, `woodie`, `classic`, `demark`, `camarilla`
- `pivot_anchor`: `daily`, `weekly`, `monthly`
- `label_col`: `label_5`, `label_10`, `label_20`
- `backend`: `mlf`, `lstm`, `bilstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`

Nếu bạn cần đầy đủ mapping giữa `config.toml` và CLI flags, hãy đọc:

- [Tham chiếu cấu hình](../reference/CONFIG_REFERENCE.md)

---

## 4. CLI theo từng bước

### 4.1. Download dữ liệu tick

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
```

#### Mục đích

- tải tick data về `data/raw/`
- lưu state để resume nếu download bị gián đoạn

#### Tham số chính

- `--symbol`
- `--asset-class`
- `--start-year`
- `--start-month`
- `--end-year` *(tùy chọn, mặc định: năm hiện tại)*
- `--end-month` *(tùy chọn, mặc định: tháng hiện tại)*
- `--concurrency`
- `--force`
- `--skip-current-month` — bỏ qua kiểm tra hoặc sửa chữa tháng hiện tại

#### Artifacts

- `data/raw/{symbol}/YYYY-MM.parquet`
- `data/raw/{symbol}/completed_months.json`

---

### 4.2. Audit dữ liệu raw

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

#### Mục đích

- Kiểm tra gap đáng kể
- Xuất báo cáo chất lượng dữ liệu

#### Artifact

- `data/raw/{symbol}/{symbol}_Data_Quality_Report.md`

---

### 4.3. Chạy pipeline

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
# Nhiều timeframe cùng lúc:
pixi run mlfx pipeline --symbol XAUUSD --tf 1H 4H 1D
```

#### Ví dụ bỏ qua từng stage

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-resample
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-features
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-labels
```

#### Tham số chính

- `--symbol`
- `--tf` *(chấp nhận nhiều giá trị, ví dụ `1H 4H 1D`)*
- `--pivot`
- `--anchor`
- `--atr-period`
- `--atr-mult`
- `--force`
- `--skip-resample`
- `--skip-features`
- `--skip-labels`

#### Artifacts

- `data/ohlcv/{symbol}/{tf}/`
- `data/features/{symbol}/{tf}/`
- `data/labels/{symbol}/{tf}/`

---

### 4.4. Train model

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf --n-trials 15 --n-splits 5
```

#### Backend hiện hỗ trợ qua CLI

- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

#### Tham số chính

- `--symbol`
- `--tf`
- `--label`
- `--backend`
- `--n-trials`
- `--n-splits`
- `--force`

#### Artifacts

- `outputs/models/{symbol}/{tf}/`

#### Lưu ý

- `n_trials` hiện có ý nghĩa nhất với backend `mlf`
- `n_splits` được map khác nhau tùy backend trong code
- Để chọn backend phù hợp, đọc:
  - [So sánh backend](../architecture/BACKEND_COMPARISON.md)

---

### 4.5. Evaluate và sinh report

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

#### Mặc định hoạt động như thế nào

- Nếu đã có model phù hợp: backtest **model**
- Nếu chưa có model: fallback sang **labels**
- Nếu muốn chỉ backtest labels: thêm `--use-labels`

#### Tham số chính

- `--symbol`
- `--tf`
- `--label`
- `--capital`
- `--risk`
- `--commission`
- `--tp`
- `--sl`
- `--slippage`
- `--use-labels`

#### Artifacts mặc định

- `outputs/reports/{symbol}/{tf}/{symbol}_{tf}_{label}_R{tp*10}_candlestick.html`
- `outputs/reports/{symbol}/{tf}/{symbol}_{tf}_{label}_R{tp*10}_equity.png`
- `outputs/reports/{symbol}/{tf}/{symbol}_{tf}_{label}_R{tp*10}_heatmap.png`

#### Đọc tiếp

- [Hướng dẫn đánh giá](EVALUATION_GUIDE.md)

---

### 4.6. Serving thời gian thực (FastAPI)

```bash
# Khởi động inference server
pixi run mlfx serve --port 8000

# Hoặc qua Docker
docker-compose up api

# Health check
curl http://localhost:8000/health

# List registered models
curl http://localhost:8000/models

# Predict
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "XAUUSD",
    "tf": "1H",
    "label_col": "label_10",
    "features": {"rsi_14": 65.2, "atr_14": 0.003, "...": "..."}
  }'
```

#### Đọc tiếp

- [Tham chiếu API](../reference/API_REFERENCE.md)

---

### 4.7. Batch inference

Dùng khi cần export predictions parquet để deploy hoặc tích hợp hệ thống khác.

> **Không dùng để xem kết quả backtest** — hãy dùng `evaluate` cho việc đó.

```bash
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H --label label_10
# → outputs/predictions/XAUUSD/1H/label_10_predictions.parquet
```

---

### 4.8. Drift detection

#### Bước 1 — Lưu reference sau khi train

```bash
# Tự động sau run_training(), hoặc thủ công:
python -c "
from mlfx.monitoring.drift import save_reference
import polars as pl
df = pl.read_parquet('data/labels/XAUUSD/1H/*.parquet')
feature_cols = [c for c in df.columns if c not in ['datetime','label_5','label_10','label_20']]
save_reference(df, feature_cols, 'XAUUSD', '1H')
"
```

#### Bước 2 — Kiểm tra drift định kỳ

```bash
pixi run mlfx drift --symbol XAUUSD --tf 1H
# In JSON report và exit code 1 nếu phát hiện drift nghiêm trọng

# Tùy chỉnh ngưỡng:
pixi run mlfx drift --symbol XAUUSD --tf 1H --threshold-ks 0.1 --threshold-psi 0.2
```

#### Tham số tùy chọn

- `--threshold-ks` — ngưỡng KS test (mặc định: `0.1`)
- `--threshold-psi` — ngưỡng PSI (mặc định: `0.2`)

---

### 4.9. Model registry

```bash
# Liệt kê tất cả versions
pixi run mlfx models

# Lọc theo symbol/tf
pixi run mlfx models --symbol XAUUSD --tf 1H
```

---

### 4.10. MLflow tracking (tùy chọn)

Khởi động MLflow server qua Docker:

```bash
docker-compose --profile tracking up mlflow
# UI tại http://localhost:5000
```

Khi server đang chạy, tracking sẽ tự động dùng MLflow thay cho file fallback.

---

## 5. Luồng chạy đầy đủ

### 5.1. Luồng tối thiểu

Đủ để xem kết quả backtest:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

### 5.2. Luồng nâng cao

```bash
# Audit dữ liệu raw
pixi run mlfx qa --symbol XAUUSD --asset-class fx

# Xem model registry
pixi run mlfx models --symbol XAUUSD --tf 1H

# Batch predict
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H --label label_10

# Serve API real-time
pixi run mlfx serve --port 8000

# Drift detection
pixi run mlfx drift --symbol XAUUSD --tf 1H
```

---

## 6. Artifacts và tracking

Mỗi lần train thường sinh ra:

- **Model artifact** — lưu trong `outputs/models/{symbol}/{tf}/`
- **Registry entry** — cập nhật vào `outputs/models/registry.json`
- **Metrics log** — thường nằm trong `outputs/runs/{symbol}/{tf}/`
- **Run files** — lưu chi tiết run khi dùng file-based tracking

### Experiment tracking

MLflow sẽ được dùng tự động nếu đã cài. Nếu chưa cài, hệ thống dùng fallback tracker dạng file.

Ví dụ:

```bash
# Khi có MLflow
pixi run mlfx train ...

# Khi không có MLflow
pixi run mlfx train ...
```

Nếu cần cài MLflow:

```bash
pip install mlflow
```

---

## 7. Checklist xác minh nhanh

Sau mỗi bước, nên kiểm tra:

- Sau `download`: có file parquet trong `data/raw/{symbol}/`
- Sau `qa`: có file báo cáo chất lượng dữ liệu
- Sau `pipeline`: có parquet trong `data/ohlcv/`, `data/features/`, `data/labels/`
- Sau `train`: có artifact mới trong `outputs/models/{symbol}/{tf}/`
- Sau `evaluate`: có HTML/PNG mới trong `outputs/reports/{symbol}/{tf}/`
- Sau `batch-predict`: có parquet trong `outputs/predictions/{symbol}/{tf}/`
- Sau `drift`: không có cảnh báo drift nghiêm trọng hoặc đã hiểu rõ cảnh báo đó

---

## 8. Cleanup an toàn

Dọn cache và generated artifacts phổ biến:

```bash
pixi run clean-generated
```

### Khi nào nên dùng

- Trước khi chạy lại benchmark hoặc smoke test
- Sau các lần train dài tạo nhiều `lightning_logs`
- Khi workspace có quá nhiều output hoặc report cũ gây khó kiểm tra

Nếu cần xử lý sự cố, đọc:

- [Khắc phục sự cố](TROUBLESHOOTING.md)

Nếu cần lối chạy nhanh nhất, đọc:

- [Quickstart](../getting-started/QUICKSTART.md)

---

## 9. Lưu ý về phong cách sử dụng tài liệu này

- `QUICKSTART.md` là lối đi nhanh nhất
- `NOOB_GUIDE.md` dành cho người mới cần hiểu tư duy và workflow
- file này là manual vận hành chính cho CLI
- `CONFIG_REFERENCE.md` là nguồn canonical khi cần tra cứu config hoặc CLI mapping chi tiết
- `API_REFERENCE.md` là nguồn canonical cho serving endpoints

---

## 10. Xem thêm

- [Quickstart](../getting-started/QUICKSTART.md)
- [Hướng dẫn cho người mới](../getting-started/NOOB_GUIDE.md)
- [Hướng dẫn đánh giá](EVALUATION_GUIDE.md)
- [Khắc phục sự cố](TROUBLESHOOTING.md)
- [Tham chiếu cấu hình](../reference/CONFIG_REFERENCE.md)
- [Tham chiếu API](../reference/API_REFERENCE.md)
- [Tham chiếu Feature](../reference/FEATURE_REFERENCE.md)
- [So sánh backend](../architecture/BACKEND_COMPARISON.md)
- [Docs Hub tiếng Việt](../README.md)
