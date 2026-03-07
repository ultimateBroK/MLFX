# ML_FX Architecture

Tài liệu này mô tả kiến trúc MLOps tổng thể của dự án ML_FX, bao gồm các module, luồng dữ liệu, và quyết định thiết kế.

---

## Tổng quan (C4 Context)

```
[User / Researcher]
        │
        ▼
┌─────────────────────────────────┐
│          ML_FX System           │
│   (ingestion → pipeline →       │
│    training → evaluation →      │
│    serving → monitoring)        │
└─────────────────────────────────┘
        │
        ├── Dukascopy API   (tick data source)
        ├── Local filesystem (data/*, outputs/*)
        └── MLflow Server   (optional tracking)
```

---

## Data Layer

### Luồng dữ liệu

```
Dukascopy API
    │  (async HTTP, bi5 decompression)
    ▼
data/raw/{symbol}/
    YYYY-MM.parquet          ← tick data (timestamp, bid, ask, volumes)
    completed_months.json    ← download state

    │  resample_symbol_tf()
    ▼
data/ohlcv/{symbol}/{tf}/
    YYYY-MM.parquet          ← OHLCV + tick_count

    │  run_feature_pipeline()
    ▼
data/features/{symbol}/{tf}/
    YYYY-MM.parquet          ← OHLCV + all technical indicators

    │  run_label_pipeline()
    ▼
data/labels/{symbol}/{tf}/
    YYYY-MM.parquet          ← features + label_5, label_10, label_20
```

### Path Policy

Tất cả đường dẫn được quản lý qua `mlfx.config.paths.ProjectPaths` (frozen dataclass).  Không có hard-coded paths nào bên ngoài module này.

```python
from mlfx.config.paths import DEFAULT_PATHS

paths = DEFAULT_PATHS                         # hoặc ProjectPaths(project_root=...)
in_dir = paths.features_dir("XAUUSD", "1H")  # data/features/XAUUSD/1H/
```

---

## Feature Engineering Layer

Entry-point duy nhất: `mlfx.pipeline.feature_engineering.run_feature_pipeline()`.

Các group feature được thêm vào:

| Group | Hàm | Output columns |
|---|---|---|
| TA Indicators | `add_ta_features()` | rsi_14, macd, macd_signal, atr_14, ema_* |
| ICT Order Blocks | `add_order_block_features()` | ob_bull/bear_distance |
| ICT Fair Value Gaps | `add_fair_value_gap_features()` | fvg_bull/bear_distance |
| Killzone sessions | `add_killzone_features()` | is_london, is_ny, is_asian |
| SR / Pivot Points | `add_sr_pp_features()` | pp, r1–r4, s1–s4 (traditional/fibonacci) |
| Normalization | `add_normalized_features()` | *_norm variants |

---

## Training Layer

### Architecture

```
TrainingConfig (dataclass)
        │
        ▼
runner.run_training()
        │
        ├── registry.get_backend_runner(config.backend)
        │           │ (dynamic import via BACKEND_REGISTRY)
        │     ┌─────┴───────────────────────────────────────────┐
        │     │          mlfx.training.backends/                │
        │     │  mlforecast.py  lstm.py  bilstm.py  ...         │
        │     │  (each import data.py, feature_selection.py,    │
        │     │   artifacts.py for shared helpers)              │
        │     └─────────────────────────────────────────────────┘
        │
        ├── tracking.tracker  (log params + metrics)
        └── registry.models   (register artifact)
```

### Training module layout

```
mlfx/training/
├── backends/               ← implementations (canonical location)
│   ├── base.py             ← BackendRunner protocol, TrainingConfig, TrainResult
│   ├── mlforecast.py       ← LightGBM via MLForecast  (key: "mlf")
│   ├── lstm.py             ← PyTorch LSTM              (key: "lstm")
│   ├── bilstm.py           ← PyTorch BiLSTM            (key: "bilstm")
│   ├── transformer.py      ← PyTorch Transformer       (key: "transformer")
│   ├── cnn_lstm.py         ← CNN + LSTM hybrid         (key: "cnn_lstm")
│   ├── online_sgd.py       ← sklearn SGD               (key: "sgd")
│   ├── stats.py            ← StatsForecast baseline    (key: "stats")
│   └── neuralforecast.py   ← NeuralForecast            (key: "neuralforecast")
├── backend_*.py            ← backward-compat shims (re-export from backends/)
├── data.py                 ← dataset loading helpers (canonical)
├── feature_selection.py    ← feature selection helpers (canonical)
├── artifacts.py            ← model persistence helpers (canonical)
├── __init__.py             ← public re-exports from data/feature_selection/artifacts
├── registry.py             ← BACKEND_REGISTRY: key → (module, function)
├── runner.py               ← high-level orchestrator
└── config.py               ← public TrainingConfig / TrainResult aliases
```

### Backend Interface

Mọi backend phải triển khai signature tương thích với `BackendRunner`:

```python
def run_xxx(
    symbol: str,
    tf: str,
    label_col: str,
    force: bool,
    **kwargs,
) -> dict:
    ...
```

Backend được ánh xạ trong `mlfx.training.registry.BACKEND_REGISTRY`, import lazy để tránh kéo heavy deps khi chỉ dùng lightweight parts.

### Training Config

```python
from mlfx.training.config import TrainingConfig

cfg = TrainingConfig(
    symbol="XAUUSD",
    tf="1H",
    backend="mlf",
    n_trials=30,
    n_splits=5,
)
```

---

## Experiment Tracking

`mlfx.tracking.tracker` cung cấp interface thống nhất với 2 backend:

| Backend | Điều kiện | Storage |
|---|---|---|
| `MlflowTracker` | `mlflow` đã cài | MLflow server hoặc `mlruns/` local |
| `FileTracker` | Fallback mặc định | `outputs/runs/{symbol}/{tf}/*.json` |

Tracking được gọi tự động trong `runner.run_training()`.  Để tắt:

```python
run_training(cfg, enable_tracking=False)
```

---

## Model Registry

`mlfx.registry.models.ModelRegistry` lưu metadata của mọi model đã train vào `outputs/models/registry.json`.

```python
from mlfx.registry import get_registry

reg = get_registry()
best = reg.best_model(symbol="XAUUSD", tf="1H", metric="best_cv_f1_macro")
# → {"backend": "mlf", "artifact_path": "...", "metrics": {...}}
```

---

## Evaluation Layer

```
load_labelled_dataset()
        │
        ▼
simulate_trades()      ← signal → entry/exit với TP/SL/TIME
        │
        ▼
compute_metrics()      ← win_rate, sharpe, sortino, calmar, profit_factor, ...
        │
        ▼
generate_full_report() ← candlestick HTML + equity PNG + session heatmap PNG
```

---

## Serving Layer

### Real-time (FastAPI)

```
POST /predict
  body: {symbol, tf, label_col, features: {col: value}}
  → loads best model from registry
  → runs inference
  → returns {prediction, confidence}
```

Khởi động:

```bash
pixi run mlfx serve --port 8000
# hoặc
docker-compose up api
```

### Batch

```bash
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H
# → outputs/predictions/XAUUSD/1H/label_10_predictions.parquet
```

---

## Monitoring

### Feature Drift

1. Sau training: `save_reference(train_df, feature_cols, symbol, tf)` → `outputs/monitoring/{symbol}/{tf}/`
2. Định kỳ: `DriftDetector.load(symbol, tf).detect(live_df)` → KS-test + PSI

```bash
pixi run mlfx drift --symbol XAUUSD --tf 1H
```

### Structured Logging

Tất cả log được xuất ra JSON lines khi chạy qua CLI:

```json
{"timestamp": "2025-01-01T10:00:00Z", "level": "INFO", "logger": "mlfx.training.runner",
 "message": "Training complete", "backend": "mlf", "elapsed_seconds": 45.2}
```

---

## Deployment

```
Dockerfile        ← multi-stage build (TA-Lib + Python)
docker-compose.yml
  ├── api         ← mlfx inference server (port 8000)
  └── mlflow      ← MLflow tracking server (port 5000, profile: tracking)
```

---

## Dependency Map

```
mlfx.app.cli
  └── mlfx.training.runner
        ├── mlfx.training.config        (TrainingConfig)
        ├── mlfx.training.registry      (get_backend_runner)
        ├── mlfx.training.backends.*    (run_* implementations)
        ├── mlfx.tracking.tracker       (optional)
        └── mlfx.registry.models        (optional)

mlfx.serving.api
  └── mlfx.registry.models

mlfx.serving.batch
  ├── mlfx.registry.models
  ├── mlfx.serving.features
  └── mlfx.serving.inference

mlfx.monitoring.drift
  └── scipy.stats (KS test)
```
