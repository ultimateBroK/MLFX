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

### Keys Worth Remembering

- `asset_class`: `fx`, `crypto`
- `timeframe`: `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`
- `pivot_type`: `traditional`, `fibonacci`, `woodie`, `classic`, `demark`, `camarilla`
- `pivot_anchor`: `daily`, `weekly`, `monthly`
- `label_col`: `label_5`, `label_10`, `label_20`
- `backend`: `mlf`, `lstm`, `bilstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`

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

#### Backends Currently Exposed Through the CLI

- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

#### Key Arguments

- `--symbol`
- `--tf`
- `--label`
- `--backend`
- `--n-trials`
- `--n-splits`
- `--force`

#### Artifacts

- `outputs/models/{symbol}/{tf}/{label}/`

#### Notes

- `n_trials` is currently most meaningful for the `mlf` backend
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
    "label_col": "label_10",
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
```

---

### 4.10. MLflow Tracking (Optional)

Start the MLflow server through Docker:

```bash
docker-compose --profile tracking up mlflow
# UI available at http://localhost:5000
```

When the server is running, the tracking layer will automatically use MLflow instead of the file-based fallback tracker.

If you need to install MLflow:

```bash
pip install mlflow
```

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

### 5.2. Advanced Workflow

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
