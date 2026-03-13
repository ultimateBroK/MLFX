# Kiến trúc MLFX

Tài liệu này mô tả kiến trúc MLOps tổng thể của dự án MLFX, bao gồm các mô-đun, luồng dữ liệu và các quyết định thiết kế quan trọng.

---

## Tổng quan (C4 Context)

```text
[Người dùng / Nhà nghiên cứu]
        │
        ▼
┌─────────────────────────────────┐
│          Hệ thống MLFX          │
│   (nạp dữ liệu → xử lý →        │
│    huấn luyện → đánh giá →      │
│    phục vụ → giám sát)          │
└─────────────────────────────────┘
        │
        ├── API Dukascopy        (nguồn dữ liệu tick)
        ├── Hệ thống tệp cục bộ  (data/*, outputs/*)
        └── MLflow Server        (theo dõi thí nghiệm, tùy chọn)
```

---

## Tầng dữ liệu

### Luồng dữ liệu

```text
Dukascopy API
    │  (HTTP bất đồng bộ, giải nén bi5)
    ▼
data/raw/{symbol}/
    YYYY-MM.parquet          ← dữ liệu tick (timestamp, bid, ask, volumes)
    completed_months.json    ← trạng thái tải dữ liệu

    │  resample_symbol_tf()
    ▼
data/ohlcv/{symbol}/{tf}/
    YYYY-MM.parquet          ← OHLCV + tick_count

    │  run_feature_pipeline()
    ▼
data/features/{symbol}/{tf}/
    YYYY-MM.parquet          ← OHLCV + toàn bộ chỉ báo kỹ thuật

    │  run_label_pipeline()
    ▼
data/labels/{symbol}/{tf}/
    YYYY-MM.parquet          ← đặc trưng + label_5, label_10, label_20
```

### Chính sách quản lý đường dẫn

Tất cả đường dẫn được quản lý qua `mlfx.config.paths.ProjectPaths` (`dataclass` bất biến). Không có đường dẫn nào bị ghi cứng bên ngoài mô-đun này.

```python
from mlfx.config.paths import DEFAULT_PATHS

paths = DEFAULT_PATHS                         # hoặc ProjectPaths(project_root=...)
in_dir = paths.features_dir("XAUUSD", "1H")  # data/features/XAUUSD/1H/
```

---

## Tầng xây dựng đặc trưng

Điểm vào duy nhất: `mlfx.pipeline.features.run_feature_pipeline()`.

Các nhóm đặc trưng được bổ sung:

| Nhóm | Hàm | Cột đầu ra |
|---|---|---|
| Chỉ báo kỹ thuật | `add_ta_features()` | `rsi_14`, `macd`, `macd_signal`, `atr_14`, `ema_*` |
| Phiên khung giờ trọng điểm | `add_killzone_features()` | `is_london`, `is_ny`, `is_asian` |
| Hỗ trợ / kháng cự và các mức điểm xoay | `add_sr_pp_features()` | `pp`, `r1`–`r4`, `s1`–`s4` (traditional/fibonacci) |
| Chuẩn hóa | `add_normalized_features()` | các biến thể `*_norm` |

---

## Tầng huấn luyện

### Kiến trúc

```text
TrainingConfig (dataclass)
        │
        ▼
runner.run_training()
        │
        ├── registry.get_backend_runner(config.backend)
        │           │ (nạp động qua BACKEND_REGISTRY)
        │     ┌─────┴───────────────────────────────────────────┐
        │     │          mlfx.training.backends/               │
        │     │  mlf.py  lstm.py  sgd.py  stats.py              │
        │     │  (mỗi bộ máy import data.py,                    │
        │     │   feature_selection.py, artifacts.py để dùng    │
        │     │   lại các helper chung)                         │
        │     └─────────────────────────────────────────────────┘
        │
        ├── tracking.tracker  (ghi params + metrics)
        └── registry.models   (đăng ký tệp đầu ra)
```

### Bố cục mô-đun huấn luyện

```text
mlfx/training/
├── backends/               ← Các phần cài đặt (vị trí chuẩn)
│   ├── __init__.py
│   ├── _pytorch_common.py  ← Tiện ích PyTorch dùng chung cho bộ máy học sâu
│   ├── _sequence_utils.py  ← Helper chuẩn bị chuỗi cho bộ máy học sâu
│   ├── base.py             ← BackendRunner protocol, TrainingConfig, TrainResult
│   ├── mlf.py              ← LightGBM qua MLForecast   (key: "mlf")
│   ├── lstm.py             ← PyTorch LSTM              (key: "lstm")
│   ├── sgd.py              ← Sklearn SGD               (key: "sgd")
│   ├── stats.py            ← Baseline StatsForecast    (key: "stats")
├── __init__.py             ← Tái xuất public từ data/feature_selection/artifacts
├── _utils.py               ← Tiện ích nội bộ
├── artifacts.py            ← Helper lưu mô hình (chuẩn)
├── config.py               ← Alias public cho TrainingConfig / TrainResult
├── data.py                 ← Helper nạp dữ liệu (chuẩn)
├── evaluation.py           ← Helper đánh giá mô hình
├── feature_selection.py    ← Helper chọn đặc trưng (chuẩn)
├── registry.py             ← BACKEND_REGISTRY: key → (module, function)
└── runner.py               ← Bộ điều phối cấp cao
```

### Giao diện bộ máy

Mọi bộ máy phải triển khai chữ ký tương thích với `BackendRunner`:

```python
def run_xxx(
    symbol: str,
    tf: str,
    label: str,
    force: bool,
    **kwargs,
) -> dict:
```

Các bộ máy được ánh xạ trong `mlfx.training.registry.BACKEND_REGISTRY`, dùng lazy import để tránh nạp các phụ thuộc nặng khi chỉ dùng những phần nhẹ hơn.

### Cấu hình huấn luyện

```python
from mlfx.training.config import TrainingConfig

cfg = TrainingConfig(
    symbol="XAUUSD",
    tf="1H",
    backend="mlf",
    n_trials=15,
    n_splits=5,
)
```

---

## Theo dõi thí nghiệm

`mlfx.tracking.tracker` cung cấp giao diện thống nhất với 2 bộ máy theo dõi:

| Bộ máy | Điều kiện | Nơi lưu |
|---|---|---|
| `MlflowTracker` | đã cài `mlflow` | MLflow server hoặc `mlruns/` cục bộ |
| `FileTracker` | phương án dự phòng mặc định | `outputs/runs/{symbol}/{tf}/*.json` |

Tracking được gọi tự động bên trong `runner.run_training()`. Muốn tắt:

```python
run_training(cfg, enable_tracking=False)
```

---

## Sổ đăng ký mô hình

`mlfx.registry.models.ModelRegistry` lưu metadata của mọi mô hình đã huấn luyện trong `outputs/models/registry.json`.

```python
from mlfx.registry import get_registry

reg = get_registry()
best = reg.best_model(symbol="XAUUSD", tf="1H", metric="best_cv_f1_macro")
```

Kết quả trả về có dạng:

```json
{"backend": "mlf", "artifact_path": "...", "metrics": {...}}
```

---

## Tầng đánh giá

```text
load_labelled_dataset()
        │
        ▼
simulate_trades()      ← tín hiệu → vào/ra lệnh với TP/SL/TIME
        │
        ▼
compute_metrics()      ← win_rate, sharpe, sortino, calmar, profit_factor, ...
        │
        ▼
generate_full_report() ← HTML nến + PNG đường vốn + PNG heatmap theo phiên
```

---

## Tầng phục vụ mô hình

### Thời gian thực (FastAPI)

```text
POST /predict
  body: {symbol, tf, label, features: {col: value}}
  → nạp mô hình tốt nhất từ registry
  → chạy suy luận
  → trả về {prediction, confidence}
```

Khởi động:

```bash
pixi run mlfx serve --port 8000
# hoặc
docker-compose up api
```

Bố cục mô-đun phục vụ:

```text
mlfx/serving/
├── __init__.py
├── api.py            ← FastAPI app (GET /health, GET /models, POST /predict)
├── batch.py          ← Bộ chạy suy luận theo lô
├── core.py           ← Tiện ích dùng chung cho lớp phục vụ
├── features.py       ← Chuẩn bị đặc trưng cho suy luận
├── inference.py      ← Nạp mô hình và dự đoán
└── torch_adapters.py ← Bộ điều hợp mô hình PyTorch cho lớp phục vụ
```

### Theo lô

```bash
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H
# → outputs/predictions/XAUUSD/1H/label_10/predictions.parquet
```

---

## Giám sát

### Độ lệch đặc trưng

1. Sau khi huấn luyện: `save_reference(train_df, feature_cols, symbol, tf)` → `outputs/monitoring/{symbol}/{tf}/`
2. Theo chu kỳ: `DriftDetector.load(symbol, tf).detect(live_df)` → KS-test + PSI

```bash
pixi run mlfx drift --symbol XAUUSD --tf 1H
# Tùy chỉnh ngưỡng:
pixi run mlfx drift --symbol XAUUSD --tf 1H --threshold-ks 0.1 --threshold-psi 0.2
```

### Ghi nhật ký có cấu trúc

Mọi log được xuất dưới dạng JSON lines khi chạy qua CLI:

```json
{"timestamp": "2025-01-01T10:00:00Z", "level": "INFO", "logger": "mlfx.training.runner",
 "message": "Training complete", "backend": "mlf", "elapsed_seconds": 45.2}
```

---

## Hệ thống cấu hình

### Luồng nạp cấu hình

```text
config.toml
    │
    ▼
mlfx.config.schema.ServingSettings
    │
    ▼
Lệnh CLI đọc giá trị mặc định từ config
    │
    ▼
Cờ CLI sẽ ghi đè giá trị từ config
```

Hệ thống cấu hình dùng Pydantic để kiểm tra hợp lệ:

```python
from mlfx.config.schema import ServingSettings

# Nạp từ config.toml + biến môi trường
settings = ServingSettings()
```

Biến môi trường có thể ghi đè:
- `MLFX_DATA_ROOT` — ghi đè thư mục dữ liệu
- `MLFX_OUTPUTS_ROOT` — ghi đè thư mục outputs

---

## Nội bộ bộ máy học sâu

### Tiện ích chuỗi (`_sequence_utils.py`)

Các helper dùng chung cho bộ máy PyTorch dạng chuỗi:

| Hàm | Mục đích |
|----------|---------|
| `create_sequences()` | Chuyển ma trận đặc trưng thành sliding windows |
| `train_sequence_model_once()` | Huấn luyện với early stopping |

Ví dụ tạo chuỗi:

```python
from mlfx.training.backends._sequence_utils import create_sequences

X_seq, y_seq = create_sequences(X, y, seq_len=60)
# X_seq shape: (n_samples - seq_len, seq_len, n_features)
# y_seq shape: (n_samples - seq_len,)
```

### PyTorch Common (`_pytorch_common.py`)

Khung HPO dùng chung cho mọi bộ máy học sâu:

```python
from mlfx.training.backends._pytorch_common import run_pytorch_hpo

# Mỗi bộ máy cung cấp:
# - train_once_fn: hàm train cho một fold
# - suggest_params_fn: hàm lấy siêu tham số bằng Optuna

model, metrics = run_pytorch_hpo(
    train_once_fn=train_lstm_once,
    suggest_params_fn=_suggest_lstm_params,
    X=X, y=y, feature_cols=feature_cols,
    model_type="LSTM",
    n_trials=10, n_splits=5,
    seq_len=60, epochs=30, batch_size=128, patience=5,
    top_k_features=20, seed=42,
)
```

Khung này xử lý:
1. Chọn đặc trưng (`SelectKBest`)
2. HPO bằng Optuna với time-series CV
3. Đánh giá ngoài mẫu
4. Huấn luyện mô hình cuối cùng

---

## Chi tiết kiến trúc serving

### Torch Adapters (`torch_adapters.py`)

Dựng lại mô hình PyTorch từ tệp đầu ra đã lưu:

```python
from mlfx.serving.torch_adapters import rebuild_torch_model, predict_with_torch_model

# Nạp mô hình từ payload trong registry
model = rebuild_torch_model(payload)

# Dự đoán (tự xử lý sequence padding)
preds = predict_with_torch_model(model, X, seq_len=60)
```

Các loại mô hình được hỗ trợ:
- `LSTM` — `FXLstm`

### Chuỗi suy luận

```text
POST /predict
    │
    ▼
resolve_and_predict()
    │
    ├── Nạp mô hình tốt nhất từ registry
    │   └── mlfx.registry.models.get_registry()
    │
    ├── Dựng lại mô hình (sklearn hoặc torch)
    │   └── mlfx.serving.torch_adapters.rebuild_torch_model()
    │
    ├── Tiền xử lý đặc trưng
    │   └── mlfx.serving.features.prepare_features()
    │
    └── Chạy suy luận
        └── model.predict() hoặc predict_with_torch_model()
```

### Tiền xử lý đặc trưng cho suy luận

```python
from mlfx.serving.features import prepare_features

# Căn chỉnh đặc trưng đầu vào với các cột mô hình mong đợi
X_aligned = prepare_features(
    features_dict={"rsi_14": 55.3, "atr_14": 2.1, ...},
    feature_columns=model_feature_cols,
)
```

---

## Triển khai

```text
Dockerfile        ← multi-stage build (TA-Lib + Python)
docker-compose.yml
  ├── api         ← máy chủ suy luận mlfx (cổng 8000)
  └── mlflow      ← máy chủ MLflow (cổng 5000, profile: tracking)
```

---

## Bản đồ phụ thuộc

### Phụ thuộc giữa các mô-đun

```text
mlfx.cli
  └── mlfx.training.runner
        ├── mlfx.training.config        (TrainingConfig)
        ├── mlfx.training.registry      (get_backend_runner)
        ├── mlfx.training.backends.*    (các hàm run_*)
        ├── mlfx.tracking.tracker       (tùy chọn)
        └── mlfx.registry.models        (tùy chọn)

mlfx.serving.api
  └── mlfx.registry.models

mlfx.serving.batch
  ├── mlfx.registry.models
  ├── mlfx.serving.features
  └── mlfx.serving.inference

mlfx.monitoring.drift
  └── scipy.stats (KS test)
```

### Phụ thuộc ngoài theo từng tầng

| Tầng | Phụ thuộc chính |
|-------|------------------|
| Dữ liệu | `polars`, `pyarrow`, `aiohttp` |
| Đặc trưng | `ta-lib`, `numpy` |
| Huấn luyện | `sklearn`, `lightgbm`, `torch`, `optuna` |
| Bộ máy học sâu | `torch`, `pytorch-forecasting` |
| Serving | `fastapi`, `uvicorn`, `cachetools` |
| Tracking | `mlflow` (tùy chọn) |
| Monitoring | `scipy` |

---

## Tham chiếu chính sách đường dẫn

Mọi đường dẫn filesystem được quản lý qua `mlfx.config.paths.ProjectPaths`:

```python
from mlfx.config.paths import DEFAULT_PATHS

# Đường dẫn dữ liệu
DEFAULT_PATHS.raw_data_dir("XAUUSD")         # data/raw/XAUUSD/
DEFAULT_PATHS.ohlcv_dir("XAUUSD", "1H")      # data/ohlcv/XAUUSD/1H/
DEFAULT_PATHS.features_dir("XAUUSD", "1H")   # data/features/XAUUSD/1H/
DEFAULT_PATHS.labels_dir("XAUUSD", "1H")     # data/labels/XAUUSD/1H/

# Đường dẫn đầu ra
DEFAULT_PATHS.models_dir("XAUUSD", "1H")                      # outputs/models/XAUUSD/1H/
DEFAULT_PATHS.models_label_dir("XAUUSD", "1H", "label_10")   # outputs/models/XAUUSD/1H/label_10/
DEFAULT_PATHS.reports_dir("XAUUSD", "1H")                     # outputs/reports/XAUUSD/1H/
DEFAULT_PATHS.report_run_dir("XAUUSD", "1H", "label_10", "model", "R15")   # outputs/reports/XAUUSD/1H/label_10/model/R15/
DEFAULT_PATHS.runs_dir("XAUUSD", "1H")                        # outputs/runs/XAUUSD/1H/
```
