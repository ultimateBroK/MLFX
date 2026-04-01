# MLFX - Configuration and Usage Guide

This document is the **operational CLI manual** for MLFX.

It focuses on:

- Which commands to run
- Which parameters matter most
- Which artifacts each stage produces
- When to use each command in the normal workflow

If you want the shortest fast-start path, read:

- [Quickstart](../getting-started/QUICKSTART.md)

If you are new and want to understand **why** the workflow is structured this way, read:

- [Beginner Guide](../getting-started/NOOB_GUIDE.md)

## Related Documentation

- [English Docs Hub](../README.md)
- [Quickstart](../getting-started/QUICKSTART.md)
- [Beginner Guide](../getting-started/NOOB_GUIDE.md)
- [Evaluation Guide](EVALUATION_GUIDE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Configuration Reference](../reference/CONFIG_REFERENCE.md)
- [API Reference](../reference/API_REFERENCE.md)
- [Feature Reference](../reference/FEATURE_REFERENCE.md)

---

## 1. Environment Setup

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

### Operating Rules

- Always run commands through `pixi run`
- Python and dependencies are managed through `pyproject.toml`
- The supported workflow does not require a separate `uv` or `venv`

### Useful Pixi Tasks

```bash
pixi run test
pixi run verify
pixi run clean-generated
```

---

## 2. Main Entrypoint

- `pixi run mlfx`: unified command-line interface

### Check Help

```bash
pixi run mlfx --help
pixi run mlfx pipeline --help
```

### Select Display Language

MLFX supports English and Vietnamese for table outputs:

```bash
# Use Vietnamese
pixi run mlfx --lang vi train --symbol XAUUSD --tf 1H

# Use English (default)
pixi run mlfx --lang en run-profile --profile research
```

- `--lang` — select display language (`en` or `vi`, default: `en`)

---

## 3. `config.toml`

The CLI reads `config.toml` to load default values.

Example:

```toml
[download]
symbol = "XAUUSD"
asset_class = "fx"
start_year = 2015
start_month = 1
concurrency = 20

[pipeline]
symbol = "XAUUSD"
tf = "1H"
pivot_type = "traditional"
pivot_anchor = "daily"

[train]
symbol = "XAUUSD"
tf = "1H"
backend = "mlf"
n_splits = 5

[backtest]
symbol          = "XAUUSD"
tf       = "1H"
label       = "label_10"
tp_r            = 1.5
sl_r            = 1.0
initial_capital = 10000.0
risk_pct        = 1.0
commission      = 0.1
```

### Keys Worth Remembering

- `asset_class`: `fx`, `crypto`
- `tf`: `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`
- `pivot_type`: `traditional`, `fibonacci`, `woodie`, `classic`, `demark`, `camarilla`
- `pivot_anchor`: `daily`, `weekly`, `monthly`
- `label`: `label_5`, `label_10`, `label_20`
- `backend`: `mlf`, `lstm`, `sgd`, `stats`

If you need the full mapping between `config.toml` and CLI flags, read:

- [Configuration Reference](../reference/CONFIG_REFERENCE.md)

---

## 4. CLI by Stage

### 4.1. Download Tick Data

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
```

#### Purpose

- download tick data into `data/raw/`
- store state so interrupted downloads can resume

#### Key Arguments

- `--symbol`
- `--asset-class`
- `--start-year`
- `--start-month`
- `--end-year` *(optional, default: current year)*
- `--end-month` *(optional, default: current month)*
- `--concurrency`
- `--force`
- `--skip-current-month` — skip checking or repairing the current month

#### Artifacts

- `data/raw/{symbol}/YYYY-MM.parquet`
- `data/raw/{symbol}/completed_months.json`

---

### 4.2. Audit Raw Data

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

#### Purpose

- detect meaningful data gaps
- write a data-quality report

#### Artifact

- `data/raw/{symbol}/{symbol}_Data_Quality_Report.md`

### 4.3. Run the Pipeline

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx pipeline --symbol XAUUSD --tf 1H 4H 1D
```

### Examples That Skip Individual Stages

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-resample
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-features
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-labels
```

#### Key Arguments

- `--symbol`
- `--tf` *(accepts multiple values, for example `1H 4H 1D`)*
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

### 4.4. Train a Model

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf --n-trials 15 --n-splits 5
```

#### Using Date Ranges

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --train-start 20240101 --train-end 20241231
```

#### Using Profiles

```bash
pixi run mlfx train --profile research
```

#### Backends Currently Exposed Through the CLI

- `mlf`
- `lstm`
- `sgd`
- `stats`

#### Key Arguments

- `--symbol`
- `--tf`
- `--label`
- `--backend`
- `--n-trials`
- `--n-splits`
- `--train-start` — start date for training (YYYYMMDD format)
- `--train-end` — end date for training (YYYYMMDD format)
- `--profile` — use a workflow profile from config
- `--force`

#### Artifacts

- `outputs/models/{symbol}/{tf}/{label}/`

#### Notes

- `n_trials` applies to `mlf` and `lstm`
- `n_splits` is mapped differently depending on the backend in the codebase
- To choose the right backend, read:
  - [Backend Comparison](../architecture/BACKEND_COMPARISON.md)

---

### 4.5. Evaluate and Generate Reports

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

#### Using Date Ranges

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --eval-start 20250101 --eval-end 20250331
```

#### Using Profiles

```bash
pixi run mlfx evaluate --profile research
```

#### Default Behavior

- If a suitable model exists: backtest the **model**
- If no suitable model exists: fall back to **labels**
- If you want to backtest labels only: add `--use-labels`

#### Key Arguments

- `--symbol`
- `--tf`
- `--label`
- `--capital`
- `--risk`
- `--commission`
- `--tp`
- `--sl`
- `--slippage`
- `--eval-start` — start date for evaluation (YYYYMMDD format)
- `--eval-end` — end date for evaluation (YYYYMMDD format)
- `--profile` — use a workflow profile from config
- `--use-labels`

#### Default Artifacts

- `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/model_{label}_R{tp*10}_candlestick.html`
- `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/model_{label}_R{tp*10}_equity.png`
- `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/model_{label}_R{tp*10}_heatmap.png`

#### Read Next

- [Evaluation Guide](EVALUATION_GUIDE.md)

---

### 4.6. Serve Real-Time Inference with FastAPI

```bash
# Start the inference server
pixi run mlfx serve --port 8000

# Or via Docker
docker-compose up api

# Check status
curl http://localhost:8000/health

# List registered models
curl http://localhost:8000/models

# Predict
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "XAUUSD",
    "tf": "1H",
    "label": "label_10",
    "features": {"rsi_14": 65.2, "atr_14": 0.003, "...": "..."}
  }'
```

#### Read Next

- [API Reference](../reference/API_REFERENCE.md)

---

### 4.7. Batch Inference

Use this when you need to export prediction parquet files for deployment or integration into another system.

> **Do not use this to inspect backtest results** — use `evaluate` for that.

```bash
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H --label label_10
# → outputs/predictions/XAUUSD/1H/label_10/predictions.parquet
```

---

### 4.8. Detect Feature Drift

#### Step 1 — Save a Reference Snapshot After Training

```bash
python -c "
from mlfx.monitoring.drift import save_reference
import polars as pl
df = pl.read_parquet('data/labels/XAUUSD/1H/*.parquet')
feature_cols = [c for c in df.columns if c not in ['datetime','label_5','label_10','label_20']]
save_reference(df, feature_cols, 'XAUUSD', '1H')
"
```

#### Step 2 — Check Drift Periodically

```bash
pixi run mlfx drift --symbol XAUUSD --tf 1H
# Prints a JSON report and returns exit code 1 if severe drift is detected

# Custom thresholds:
pixi run mlfx drift --symbol XAUUSD --tf 1H --threshold-ks 0.1 --threshold-psi 0.2
```

#### Optional Arguments

- `--threshold-ks` — KS test threshold (default: `0.1`)
- `--threshold-psi` — PSI threshold (default: `0.2`)

---

### 4.9. Model Registry

```bash
pixi run mlfx models
pixi run mlfx models --symbol XAUUSD --tf 1H
pixi run mlfx models --backend mlf --label label_10
```

---

### 4.10. Benchmark Multiple Backends

Compare performance across multiple backends in a single run:

```bash
pixi run mlfx benchmark --symbol XAUUSD --tf 1H --backends mlf sgd stats --n-trials 10
```

#### Using Profiles

```bash
pixi run mlfx benchmark --profile benchmark_fast
```

#### Key Arguments

- `--symbol`
- `--tf`
- `--label`
- `--backends` — list of backends to compare
- `--n-trials` — trials per backend
- `--n-splits`
- `--train-start` / `--train-end` — training date range
- `--profile` — use a workflow profile
- `--force`

---

### 4.11. Drift Detection with Auto-Retrain

Check for feature drift and automatically retrain if detected:

```bash
pixi run mlfx drift-retrain --symbol XAUUSD --tf 1H --threshold-ks 0.1 --threshold-psi 0.2
```

#### Key Arguments

- `--symbol`
- `--tf`
- `--label`
- `--threshold-ks` — KS test threshold
- `--threshold-psi` — PSI threshold
- `--min-samples` — minimum samples per feature

---

### 4.12. List Workflow Profiles

View all available workflow profiles defined in `config.toml`:

```bash
pixi run mlfx profiles
```

---

### 4.13. Run Train + Evaluate from Profile

Execute a complete train + evaluate workflow using a predefined profile:

```bash
pixi run mlfx run-profile --profile research
```

#### Skipping Steps

```bash
pixi run mlfx run-profile --profile research --skip-train
pixi run mlfx run-profile --profile research --skip-evaluate
pixi run mlfx run-profile --profile research --skip-benchmark
```

#### Force Retraining

```bash
# Retrain even if a model already exists
pixi run mlfx run-profile --profile research --force
```

#### Save JSON Summary

```bash
# Save summary to file instead of printing to stdout
pixi run mlfx run-profile --profile research --json
# → outputs/runs/workflows/{timestamp}_{profile}_summary.json
```

#### Key Arguments

- `--profile` — **required**, name of the profile to use
- `--skip-train` — skip training step
- `--skip-evaluate` — skip evaluation step
- `--skip-benchmark` — skip benchmark step (if defined in profile)
- `--force` — force retraining even if a model already exists
- `--json` — save JSON summary to `outputs/runs/workflows/`

---

### 4.14. Run Full End-to-End Workflow

Execute the complete pipeline from download to evaluation:

```bash
pixi run mlfx run-all --symbol XAUUSD --tf 1H --label label_10 --backend mlf
```

#### Skipping Steps

```bash
pixi run mlfx run-all --symbol XAUUSD --tf 1H --skip-download
pixi run mlfx run-all --symbol XAUUSD --tf 1H --skip-pipeline
pixi run mlfx run-all --symbol XAUUSD --tf 1H --skip-train
pixi run mlfx run-all --symbol XAUUSD --tf 1H --skip-evaluate
```

#### Continue on Error

```bash
pixi run mlfx run-all --symbol XAUUSD --tf 1H --continue-on-error --json
```

#### Key Arguments

- `--symbol` — override symbol (overrides profile)
- `--tf` — override timeframe (overrides profile)
- `--label` — override label column (overrides profile)
- `--backend` — training backend
- `--skip-download` — skip data download
- `--skip-pipeline` — skip feature pipeline
- `--skip-train` — skip model training
- `--skip-evaluate` — skip evaluation
- `--continue-on-error` — continue even if a step fails
- `--json` — save JSON summary to `outputs/runs/workflows/`

---

### 4.15. MLflow Tracking (Optional)

Start the MLflow server through Docker:

```bash
docker-compose --profile tracking up mlflow
# UI available at http://localhost:5000
```

When the server is running, the tracking layer will automatically use MLflow instead of the file-based fallback tracker.

#### MLflow Configuration

MLflow can be configured via environment variables:

| Variable | Description | Example |
|---|---|---|
| `MLFLOW_TRACKING_URI` | MLflow tracking server URI | `http://localhost:5000` |
| `MLFLOW_ARTIFACT_ROOT` | Root directory for artifacts | `/data/mlflow_artifacts` |
| `MLFLOW_REGISTRY_URI` | Model registry URI | `http://localhost:5000` |

Example:

```bash
# Use remote MLflow server
export MLFLOW_TRACKING_URI="http://mlflow.example.com:5000"
pixi run mlfx train --symbol XAUUSD --tf 1H

# Use custom artifact storage
export MLFLOW_ARTIFACT_ROOT="/mnt/shared/mlflow_artifacts"
pixi run mlfx train --symbol XAUUSD --tf 1H
```

#### Default Backend

By default, MLflow uses SQLite (`mlflow.db`) as the backend store, which is recommended over the deprecated file-based store.

If you need to install MLflow:

```bash
pixi add mlflow
```

---

### 4.16. MLflow Server Management

Manage MLflow tracking server and migrate existing artifacts:

#### Start MLflow UI

```bash
pixi run mlfx mlflow ui --port 5000
# UI available at http://127.0.0.1:5000
```

#### Key Arguments for `mlflow ui`

- `--host` — Host to bind the UI server (default: `127.0.0.1`)
- `--port` — Port for the UI server (default: `5000`)
- `--backend-store-uri` — URI for MLflow backend store (default: from config)
- `--default-artifact-root` — Default artifact root path (default: from config)

#### Migrate Existing Artifacts

Migrate existing model artifacts and run metadata to MLflow:

```bash
# Migrate all models
pixi run mlfx mlflow migrate

# Migrate only specific symbol
pixi run mlfx mlflow migrate --symbol XAUUSD

# Migrate only specific symbol and timeframe
pixi run mlfx mlflow migrate --symbol XAUUSD --tf 1H

# Preview migration without making changes
pixi run mlfx mlflow migrate --dry-run
```

#### Key Arguments for `mlflow migrate`

- `--symbol` — Migrate only models for this symbol (default: all)
- `--tf` — Migrate only models for this timeframe (default: all)
- `--backend` — Migrate only models for this backend (default: all)
- `--dry-run` — Preview migration without making changes
- `--register-models` — Register migrated models in MLflow Model Registry (default: True)

---

## 5. Full Workflow Examples

### 5.1. Minimal Workflow

Enough to produce a backtest result:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

### 5.2. One-Command End-to-End

Use `run-all` for the complete pipeline:

```bash
pixi run mlfx run-all --symbol XAUUSD --tf 1H --label label_10 --backend mlf
```

### 5.3. Profile-Based Workflow

Define profiles in `config.toml` and use them for reproducible experiments:

```bash
# List available profiles
pixi run mlfx profiles

# Run train + evaluate using a profile
pixi run mlfx run-profile --profile research

# Train using a profile
pixi run mlfx train --profile research

# Evaluate using a profile
pixi run mlfx evaluate --profile research

# Benchmark using a profile
pixi run mlfx benchmark --profile benchmark_fast
```

### 5.4. Advanced Workflow

```bash
# Audit raw data
pixi run mlfx qa --symbol XAUUSD --asset-class fx

# View the model registry
pixi run mlfx models --symbol XAUUSD --tf 1H

# Run batch inference
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H --label label_10

# Serve a real-time API
pixi run mlfx serve --port 8000

# Check feature drift
pixi run mlfx drift --symbol XAUUSD --tf 1H

# Drift detection with auto-retrain
pixi run mlfx drift-retrain --symbol XAUUSD --tf 1H
```

---

## 6. Artifacts and Tracking

Each training run usually produces:

- **Model artifact** — stored in `outputs/models/{symbol}/{tf}/{label}/`
- **Registry record** — appended to `outputs/models/registry.json`
- **Metrics record** — usually stored in `outputs/runs/{symbol}/{tf}/`
- **Run metadata file** — detailed run output when using the file-based tracker

### Experiment Tracking

MLflow is used automatically if it is installed. If not, the system uses the fallback file-based tracker.

Example:

```bash
pixi run mlfx train ...
pixi run mlfx train ...
```

---

## 7. Quick Verification Checklist

After each stage, verify:

- After `download`: parquet files exist in `data/raw/{symbol}/`
- After `qa`: a data-quality report exists
- After `pipeline`: parquet files exist in `data/ohlcv/`, `data/features/`, and `data/labels/`
- After `train`: new artifacts exist in `outputs/models/{symbol}/{tf}/{label}/`
- After `evaluate`: new HTML or PNG files exist in `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/` or `outputs/reports/{symbol}/{tf}/{label}/labels/R{tp*10}/`
- After `batch-predict`: parquet files exist in `outputs/predictions/{symbol}/{tf}/{label}/`
- After `drift`: there is no severe drift alert, or you already understand the reason

---

## 8. Safe Cleanup

Clear common caches and generated artifacts:

```bash
pixi run clean-generated
```

### When to Use It

- Before rerunning benchmarks or smoke tests
- After long training runs created many `lightning_logs`
- When old outputs or reports make validation harder

If you need incident handling guidance, read:

- [Troubleshooting](TROUBLESHOOTING.md)

If you need the fastest runnable path, read:

- [Quickstart](../getting-started/QUICKSTART.md)

---

## 9. Notes on the Role of This Document

- `QUICKSTART.md` is the fastest path
- `NOOB_GUIDE.md` is for new users who need the workflow and mental model first
- this file is the main operational manual for the CLI
- `CONFIG_REFERENCE.md` is the canonical reference when you need exact config or CLI flag mappings
- `API_REFERENCE.md` is the canonical reference for serving endpoints

---

## 10. See Also

- [Quickstart](../getting-started/QUICKSTART.md)
- [Beginner Guide](../getting-started/NOOB_GUIDE.md)
- [Evaluation Guide](EVALUATION_GUIDE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Configuration Reference](../reference/CONFIG_REFERENCE.md)
- [API Reference](../reference/API_REFERENCE.md)
- [Feature Reference](../reference/FEATURE_REFERENCE.md)
- [Backend Comparison](../architecture/BACKEND_COMPARISON.md)
- [English Docs Hub](../README.md)
