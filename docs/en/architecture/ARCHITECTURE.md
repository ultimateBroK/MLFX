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

Single entry point: `mlfx.pipeline.features.run_feature_pipeline()`.

Feature groups added:

| Group | Function | Output columns |
|---|---|---|
| TA Indicators | `add_ta_features()` | rsi_14, macd, macd_signal, atr_14, ema_* |
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
        │     │  mlf.py  lstm.py  sgd.py  stats.py              │
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
│   ├── mlf.py              ← LightGBM via MLForecast  (key: "mlf")
│   ├── lstm.py             ← PyTorch LSTM              (key: "lstm")
│   ├── sgd.py              ← Sklearn SGD               (key: "sgd")
│   ├── stats.py            ← StatsForecast baseline    (key: "stats")
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
    label: str,
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

The `mlfx.tracking` module provides a unified tracking interface with MLflow integration:

```
mlfx/tracking/
├── __init__.py       ← Public exports
├── context.py        ← ExperimentContext, workflow_context for run nesting
└── tracker.py        ← BaseTracker, FileTracker, MlflowTracker, get_tracker()
```

### Tracking Backends

| Backend | Condition | Storage |
|---|---|---|
| `MlflowTracker` | `mlflow` installed | MLflow server (SQLite backend: `mlflow.db`) |
| `FileTracker` | Default fallback | `outputs/runs/{symbol}/{tf}/*.json` |

### Usage

Tracking is called automatically within `runner.run_training()`. To disable:

```python
run_training(cfg, enable_tracking=False)
```

For programmatic access:

```python
from mlfx.tracking import get_tracker, experiment_context

tracker = get_tracker()
run_id = tracker.start_run("my_run", params={"lr": 0.01})
tracker.log_metrics(run_id, {"f1": 0.72})
tracker.end_run(run_id)

# Context manager for nested runs
with experiment_context("experiment_name", symbol="XAUUSD", tf="1H"):
    # Training code here
    pass
```

---

## Model Registry

The `mlfx.registry` module provides dual registry support for tracking trained model artifacts:

```
mlfx/registry/
├── __init__.py           ← Public exports, get_registry() factory
├── models.py             ← ModelRegistry (JSON-backed)
└── mlflow_registry.py    ← MlflowModelRegistry (MLflow-backed)
```

### Registry Backends

| Backend | Function | Storage |
|---|---|---|
| `MlflowModelRegistry` | `get_registry(use_mlflow=True)` | MLflow Model Registry |
| `ModelRegistry` | `get_registry(use_mlflow=False)` | `outputs/models/registry.json` |

### Usage

```python
from mlfx.registry import get_registry

# Use MLflow registry when available (default)
reg = get_registry(use_mlflow=True)

# Or use JSON registry explicitly
reg = get_registry(use_mlflow=False)

# Query best model
best = reg.best_model(symbol="XAUUSD", tf="1H", metric="best_cv_f1_macro")
```

Returns:

```json
{"backend": "mlf", "artifact_path": "...", "metrics": {...}}
```

The registry automatically falls back to JSON if MLflow is not installed.

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
  body: {symbol, tf, label, features: {col: value}}
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
├── batch.py         ← Batch inference runner
├── core.py          ← Shared serving utilities
├── features.py      ← Feature preparation for inference
├── inference.py     ← Model loading and prediction
└── torch_adapters.py ← PyTorch model adapters for serving
```

### Batch

```bash
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H
# → outputs/predictions/XAUUSD/1H/label_10/predictions.parquet
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

### MLflow Integration

Both `save_reference()` and `detect()` support automatic MLflow logging:

```python
from mlfx.monitoring.drift import DriftDetector, save_reference

# Log reference snapshot to MLflow
save_reference(train_df, feature_cols, "XAUUSD", "1H", log_to_mlflow=True)

# Log drift detection results to MLflow
detector = DriftDetector.load("XAUUSD", "1H")
report = detector.detect(live_df, log_to_mlflow=True)
```

When MLflow is available, drift metrics and artifacts are automatically logged to the `mlfx/monitoring/drift` experiment.

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

### MLflow Configuration

The `mlfx.config.mlflow` module provides centralized MLflow configuration:

```python
from mlfx.config.mlflow import get_mlflow_config

config = get_mlflow_config()
config.setup_mlflow()  # Configure MLflow with project settings
```

**Configuration options:**

| Setting | Default | Description |
|---|---|---|
| Tracking URI | `sqlite:///mlflow.db` | MLflow tracking server URI |
| Artifact Root | `outputs/mlflow_artifacts/` | Root directory for artifacts |
| Experiment Prefix | `mlfx` | Prefix for experiment names |

**Environment variable overrides:**

| Variable | Description |
|---|---|---|
| `MLFLOW_TRACKING_URI` | Override tracking server URI (e.g., `http://localhost:5000`) |
| `MLFLOW_ARTIFACT_ROOT` | Override artifact storage path |
| `MLFLOW_REGISTRY_URI` | Override model registry URI |

**Experiment naming convention:**

```python
# Generates: mlfx/XAUUSD/1H/label_10
experiment_name = config.experiment_name(symbol="XAUUSD", tf="1H", label="label_10")

# Generates: mlfx-XAUUSD-1H-label_10
model_name = config.model_name(symbol="XAUUSD", tf="1H", label="label_10")
```

---

## Workflow Orchestration

### Workflow Module

The `mlfx.workflow/` module provides end-to-end orchestration capabilities:

```
mlfx/workflow/
├── __init__.py           ← Public exports
├── results.py            ← StageResult, WorkflowResult, persist_workflow_result()
├── stages.py             ← Individual stage runners (run_download, run_train, etc.)
├── stage.py              ← Stage execution utilities
└── result.py             ← Result type definitions
```

### Workflow Stages

The `run-all` command executes stages sequentially:

```
Stage 1: download    → data/raw/{symbol}/
Stage 2: pipeline    → data/ohlcv/, data/features/, data/labels/
Stage 3: train       → outputs/models/{symbol}/{tf}/{label}/
Stage 4: evaluate    → outputs/reports/{symbol}/{tf}/{label}/
```

Each stage can be skipped independently via flags:
- `--skip-download`
- `--skip-pipeline`
- `--skip-train`
- `--skip-evaluate`

### Stage Results

Each stage returns a `StageResult` with structured output:

```python
from mlfx.workflow import StageResult, WorkflowResult, persist_workflow_result

# Stage result contains status, duration, and output paths
result: StageResult = run_train(symbol="XAUUSD", tf="1H", label="label_10")

# Workflow result aggregates all stages
workflow_result = WorkflowResult(
    stages=[download_result, pipeline_result, train_result, evaluate_result],
    total_duration=120.5
)

# Persist to JSON for CI/CD integration
persist_workflow_result(workflow_result, path="outputs/runs/workflow_result.json")
```

### Profiles System

Workflow profiles allow predefined configurations for reproducible experiments:

```toml
[profiles.research.train]
symbol      = "XAUUSD"
tf          = "1H"
label       = "label_10"
backend     = "mlf"
train_start = "20240101"
train_end   = "20241231"
n_trials    = 5

[profiles.research.evaluate]
symbol          = "XAUUSD"
tf              = "1H"
label           = "label_10"
eval_start      = "20250101"
eval_end        = "20250331"
tp_r            = 1.5
sl_r            = 1.0
initial_capital = 10000.0
```

Profile usage:

```bash
# List available profiles
pixi run mlfx profiles

# Run train + evaluate from profile
pixi run mlfx run-profile --profile research

# Use profile for individual commands
pixi run mlfx train --profile research
pixi run mlfx evaluate --profile research
pixi run mlfx benchmark --profile benchmark_fast
```

### Profile Resolution

When a profile is specified, the system:

1. Loads profile from `config.toml` via `WorkflowProfileConfig`
2. Merges profile settings with command-specific config
3. CLI flags override both profile and config defaults

```
CLI flags (highest priority)
    │
    ▼
Profile settings
    │
    ▼
config.toml defaults
    │
    ▼
Built-in defaults (lowest priority)
```

---

## CLI Architecture

### Command Structure

```
mlfx
├── download          # Tick data ingestion
├── pipeline          # Feature engineering
├── train             # Model training
├── evaluate          # Backtesting & reports
├── benchmark         # Multi-backend comparison
├── serve             # FastAPI inference server
├── batch-predict     # Batch inference
├── drift             # Feature drift detection
├── drift-retrain     # Drift detection with auto-retrain
├── models            # Model registry listing
├── profiles          # List workflow profiles
├── run-profile       # Train + evaluate from profile
└── run-all           # Full end-to-end pipeline
```

### Command Implementation

Each CLI command follows a consistent pattern:

```python
# mlfx/cli/main.py
@app.command("train")
def train_cmd(
    symbol: str = None,
    tf: str = None,
    label: str = None,
    profile: str = None,
    ...
):
    config = resolve_config("train", profile=profile)
    # Execute training logic
```

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
Dockerfile        ← Multi-stage build (TA-Lib + Python)
docker-compose.yml
  ├── api         ← mlfx inference server (port 8000)
  └── mlflow      ← MLflow tracking server (port 5000, profile: tracking)
```

---

## Dependency Map

### Module Dependencies

```
mlfx.cli
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
DEFAULT_PATHS.models_dir("XAUUSD", "1H")                 # outputs/models/XAUUSD/1H/
DEFAULT_PATHS.models_label_dir("XAUUSD", "1H", "label_10")      # outputs/models/XAUUSD/1H/label_10/
DEFAULT_PATHS.reports_dir("XAUUSD", "1H")                # outputs/reports/XAUUSD/1H/
DEFAULT_PATHS.report_run_dir("XAUUSD", "1H", "label_10", "model", "R15")   # outputs/reports/XAUUSD/1H/label_10/model/R15/
DEFAULT_PATHS.runs_dir("XAUUSD", "1H")                   # outputs/runs/XAUUSD/1H/
```
