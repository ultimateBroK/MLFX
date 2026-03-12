# MLFX Architecture

This document describes the overall MLOps architecture of the MLFX project, including modules, data flows, and design decisions.

---

## Overview (C4 Context)

```
[User / Researcher]
        │
        ▼
┌─────────────────────────────────┐
│          MLFX System            │
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

### Data Flow

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

All paths are managed via `mlfx.config.paths.ProjectPaths` (frozen dataclass). No hard-coded paths exist outside this module.

```python
from mlfx.config.paths import DEFAULT_PATHS

paths = DEFAULT_PATHS                         # or ProjectPaths(project_root=...)
in_dir = paths.features_dir("XAUUSD", "1H")  # data/features/XAUUSD/1H/
```

---

## Feature Engineering Layer

Single entry point: `mlfx.pipeline.feature_engineering.run_feature_pipeline()`.

Feature groups added:

| Group | Function | Output columns |
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

### Training Module Layout

```
mlfx/training/
├── backends/               ← Implementations (canonical location)
│   ├── __init__.py
│   ├── _pytorch_common.py  ← Shared PyTorch utilities for DL backends
│   ├── _sequence_utils.py  ← Sequence preparation helpers for DL backends
│   ├── base.py             ← BackendRunner protocol, TrainingConfig, TrainResult
│   ├── mlforecast.py       ← LightGBM via MLForecast  (key: "mlf")
│   ├── lstm.py             ← PyTorch LSTM              (key: "lstm")
│   ├── bilstm.py           ← PyTorch BiLSTM            (key: "bilstm")
│   ├── transformer.py      ← PyTorch Transformer       (key: "transformer")
│   ├── cnn_lstm.py         ← CNN + LSTM hybrid         (key: "cnn_lstm")
│   ├── online_sgd.py       ← Sklearn SGD               (key: "sgd")
│   ├── stats.py            ← StatsForecast baseline    (key: "stats")
│   └── neuralforecast.py   ← NeuralForecast            (key: "neuralforecast")
├── __init__.py             ← Public re-exports from data/feature_selection/artifacts
├── _utils.py               ← Internal utilities
├── artifacts.py            ← Model persistence helpers (canonical)
├── config.py               ← Public TrainingConfig / TrainResult aliases
├── data.py                 ← Dataset loading helpers (canonical)
├── evaluation.py           ← Model evaluation helpers
├── feature_selection.py    ← Feature selection helpers (canonical)
├── registry.py             ← BACKEND_REGISTRY: key → (module, function)
└── runner.py               ← High-level orchestrator
```

### Backend Interface

Every backend must implement a signature compatible with `BackendRunner`:

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

Backends are mapped in `mlfx.training.registry.BACKEND_REGISTRY`, with lazy imports to avoid pulling heavy dependencies when only using lightweight parts.

### Training Config

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

## Experiment Tracking

`mlfx.tracking.tracker` provides a unified interface with 2 backends:

| Backend | Condition | Storage |
|---|---|---|
| `MlflowTracker` | `mlflow` installed | MLflow server or `mlruns/` local |
| `FileTracker` | Default fallback | `outputs/runs/{symbol}/{tf}/*.json` |

Tracking is called automatically within `runner.run_training()`. To disable:

```python
run_training(cfg, enable_tracking=False)
```

---

## Model Registry

`mlfx.registry.models.ModelRegistry` stores metadata for all trained models in `outputs/models/registry.json`.

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
simulate_trades()      ← signal → entry/exit with TP/SL/TIME
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

Start:

```bash
pixi run mlfx serve --port 8000
# or
docker-compose up api
```

Serving module layout:

```
mlfx/serving/
├── __init__.py
├── api.py           ← FastAPI app (GET /health, GET /models, POST /predict)
├── batch.py         ← batch inference runner
├── core.py          ← shared serving utilities
├── features.py      ← feature preparation for inference
├── inference.py     ← model loading and prediction
└── torch_adapters.py ← PyTorch model adapters for serving
```

### Batch

```bash
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H
# → outputs/predictions/XAUUSD/1H/label_10_predictions.parquet
```

---

## Monitoring

### Feature Drift

1. After training: `save_reference(train_df, feature_cols, symbol, tf)` → `outputs/monitoring/{symbol}/{tf}/`
2. Periodically: `DriftDetector.load(symbol, tf).detect(live_df)` → KS-test + PSI

```bash
pixi run mlfx drift --symbol XAUUSD --tf 1H
# Custom thresholds:
pixi run mlfx drift --symbol XAUUSD --tf 1H --threshold-ks 0.1 --threshold-psi 0.2
```

### Structured Logging

All logs are output as JSON lines when running through CLI:

```json
{"timestamp": "2025-01-01T10:00:00Z", "level": "INFO", "logger": "mlfx.training.runner",
 "message": "Training complete", "backend": "mlf", "elapsed_seconds": 45.2}
```

---

## Configuration System

### Config Loading Flow

```
config.toml
    │
    ▼
mlfx.config.schema.ServingSettings
    │
    ▼
CLI commands read defaults from config
    │
    ▼
CLI flags override config values
```

The configuration system uses Pydantic for validation:

```python
from mlfx.config.schema import ServingSettings

# Load from config.toml + env vars
settings = ServingSettings()
```

Environment variable overrides:
- `MLFX_DATA_ROOT` — override data directory
- `MLFX_OUTPUTS_ROOT` — override outputs directory

---

## Deep Learning Backend Internals

### Sequence Utilities (`_sequence_utils.py`)

Shared helpers for PyTorch sequence-based backends:

| Function | Purpose |
|----------|---------|
| `create_sequences()` | Convert feature matrix to sliding windows |
| `train_sequence_model_once()` | Train with early stopping |

Sequence creation example:
```python
from mlfx.training.backends._sequence_utils import create_sequences

X_seq, y_seq = create_sequences(X, y, seq_len=60)
# X_seq shape: (n_samples - seq_len, seq_len, n_features)
# y_seq shape: (n_samples - seq_len,)
```

### PyTorch Common (`_pytorch_common.py`)

Shared HPO scaffold for all DL backends:

```python
from mlfx.training.backends._pytorch_common import run_pytorch_hpo

# Each backend provides:
# - train_once_fn: single-fold trainer
# - suggest_params_fn: Optuna hyperparameter sampler

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

The scaffold handles:
1. Feature selection (SelectKBest)
2. Optuna HPO with time-series CV
3. Out-of-sample evaluation
4. Final model training

---

## Serving Architecture Details

### Torch Adapters (`torch_adapters.py`)

Rebuilding PyTorch models from persisted artifacts:

```python
from mlfx.serving.torch_adapters import rebuild_torch_model, predict_with_torch_model

# Load model from registry payload
model = rebuild_torch_model(payload)

# Predict (handles sequence padding)
preds = predict_with_torch_model(model, X, seq_len=60)
```

Supported model types:
- `LSTM` — FXLstm
- `BiLSTM` — FXBiLstm
- `CNN_LSTM` — FXCnnLstm
- `Transformer` — FXTransformer

### Inference Chain

```
POST /predict
    │
    ▼
resolve_and_predict()
    │
    ├── Load best model from registry
    │   └── mlfx.registry.models.get_registry()
    │
    ├── Rebuild model (sklearn or torch)
    │   └── mlfx.serving.torch_adapters.rebuild_torch_model()
    │
    ├── Preprocess features
    │   └── mlfx.serving.features.prepare_features()
    │
    └── Run inference
        └── model.predict() or predict_with_torch_model()
```

### Feature Preprocessing for Inference

```python
from mlfx.serving.features import prepare_features

# Align input features with model's expected columns
X_aligned = prepare_features(
    features_dict={"rsi_14": 55.3, "atr_14": 2.1, ...},
    feature_columns=model_feature_cols,
)
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

### Module Dependencies

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

### External Dependencies by Layer

| Layer | Key Dependencies |
|-------|------------------|
| Data | `polars`, `pyarrow`, `aiohttp` |
| Features | `ta-lib`, `numpy` |
| Training | `sklearn`, `lightgbm`, `torch`, `optuna` |
| DL Backends | `torch`, `pytorch-forecasting` |
| Serving | `fastapi`, `uvicorn`, `cachetools` |
| Tracking | `mlflow` (optional) |
| Monitoring | `scipy` |

---

## Path Policy Reference

All filesystem paths are managed through `mlfx.config.paths.ProjectPaths`:

```python
from mlfx.config.paths import DEFAULT_PATHS

# Data paths
DEFAULT_PATHS.raw_data_dir("XAUUSD")        # data/raw/XAUUSD/
DEFAULT_PATHS.ohlcv_dir("XAUUSD", "1H")     # data/ohlcv/XAUUSD/1H/
DEFAULT_PATHS.features_dir("XAUUSD", "1H")  # data/features/XAUUSD/1H/
DEFAULT_PATHS.labels_dir("XAUUSD", "1H")    # data/labels/XAUUSD/1H/

# Output paths
DEFAULT_PATHS.models_dir("XAUUSD", "1H")    # outputs/models/XAUUSD/1H/
DEFAULT_PATHS.reports_dir("XAUUSD", "1H")   # outputs/reports/XAUUSD/1H/
DEFAULT_PATHS.runs_dir("XAUUSD", "1H")      # outputs/runs/XAUUSD/1H/
```
