# MLFX - Configuration and Usage Guide

This guide is the **operational CLI manual** for MLFX.

It focuses on:

- Which commands to run
- Which parameters matter most
- Which artifacts each stage produces
- When to use each command in the normal workflow

If you want the shortest onboarding path, start with:

- [Quickstart](../getting-started/QUICKSTART.md)

If you are new to the repository and want the conceptual overview first, read:

- [Beginner Guide](../getting-started/NOOB_GUIDE.md)

## Related Documentation

- [English Docs Hub](../README.md)
- [Quickstart](../getting-started/QUICKSTART.md)
- [Beginner Guide](../getting-started/NOOB_GUIDE.md)
- [Evaluation Guide](EVALUATION_GUIDE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Configuration Reference](../reference/CONFIG_REFERENCE.md)
- [API Reference](../reference/API_REFERENCE.md)
- [Backend Comparison](../architecture/BACKEND_COMPARISON.md)

---

## 1. Environment Setup

Install the environment with Pixi:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

### Operating Rules

- Run commands through `pixi run`
- Python and dependencies are managed from `pyproject.toml`
- No separate `uv` or `venv` workflow is required for the supported setup

### Useful Pixi Tasks

```bash
pixi run test
pixi run verify
pixi run clean-generated
```

---

## 2. Official Entrypoints

The main entrypoint is:

- `pixi run mlfx` — unified CLI

Check help:

```bash
pixi run mlfx --help
pixi run mlfx pipeline --help
```

---

## 3. Configuration Model

MLFX uses a layered configuration model:

1. `config.toml` provides project defaults
2. CLI flags override those defaults per command

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
symbol = "XAUUSD"
timeframe = "1H"
label_col = "label_10"

[features]
rsi_period = 14
atr_period = 14
ema_periods = [20, 50, 200]
macd_fast = 12
macd_slow = 26
macd_signal = 9
avg_range_n = 5
```

### Common Keys to Remember

- `asset_class`: `fx`, `crypto`
- `timeframe`: `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`
- `pivot_type`: `traditional`, `fibonacci`, `woodie`, `classic`, `demark`, `camarilla`
- `pivot_anchor`: `daily`, `weekly`, `monthly`
- `label_col`: `label_5`, `label_10`, `label_20`
- `backend`: `mlf`, `lstm`, `bilstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`
- `rsi_period`: RSI window (default: `14`)
- `atr_period`: ATR window (default: `14`)
- `ema_periods`: list of EMA periods (default: `[20, 50, 200]`)
- `macd_fast` / `macd_slow` / `macd_signal`: MACD parameters (default: `12`, `26`, `9`)
- `avg_range_n`: rolling window for killzone average range (default: `5`)

For the complete setting-by-setting reference, see:

- [Configuration Reference](../reference/CONFIG_REFERENCE.md)

---

## 4. Standard Workflow

The normal MLFX workflow is:

```text
download
  -> qa
  -> pipeline
  -> train
  -> evaluate
  -> serve / batch-predict
  -> drift
```

At a high level:

- `download` fetches raw tick data
- `qa` audits raw data quality
- `pipeline` creates OHLCV, features, and labels
- `train` fits a backend and stores artifacts
- `evaluate` runs backtests and generates reports
- `serve` starts the inference API
- `batch-predict` writes offline predictions
- `drift` compares new data distributions against reference snapshots

If you only want the fastest runnable flow, use:

- [Quickstart](../getting-started/QUICKSTART.md)

---

## 5. CLI by Stage

## 5.1 Download Tick Data

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
```

### Purpose

- Fetch raw tick data into `data/raw/`
- Maintain download state for resume behavior

### Key Arguments

- `--symbol`
- `--asset-class`
- `--start-year`
- `--start-month`
- `--end-year` *(optional, defaults to current year)*
- `--end-month` *(optional, defaults to current month)*
- `--concurrency`
- `--force`
- `--skip-current-month` — skip checking or repairing the current month

### Artifacts

- `data/raw/{symbol}/YYYY-MM.parquet`
- `data/raw/{symbol}/completed_months.json`

---

## 5.2 Audit Raw Data

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

### Purpose

- Detect meaningful gaps
- Write a data-quality report

### Artifact

- `data/raw/{symbol}/{symbol}_Data_Quality_Report.md`

---

## 5.3 Run the Pipeline

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H

# Multiple timeframes at once
pixi run mlfx pipeline --symbol XAUUSD --tf 1H 4H 1D
```

### Examples That Skip Individual Stages

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-resample
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-features
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-labels
```

### Key Arguments

- `--symbol`
- `--tf` *(accepts multiple values, e.g. `1H 4H 1D`)*
- `--pivot`
- `--anchor`
- `--atr-period`
- `--atr-mult`
- `--force`
- `--skip-resample`
- `--skip-features`
- `--skip-labels`

### Artifacts

- `data/ohlcv/{symbol}/{tf}/`
- `data/features/{symbol}/{tf}/`
- `data/labels/{symbol}/{tf}/`

---

## 5.4 Train a Model

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf --n-trials 15 --n-splits 5
```

### Backends Exposed Through the CLI

- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

### Key Arguments

- `--symbol`
- `--tf`
- `--label`
- `--backend`
- `--n-trials`
- `--n-splits`
- `--force`

### Artifacts

- `outputs/models/{symbol}/{tf}/`

### Notes

- `n_trials` is most relevant for the `mlf` backend
- `n_splits` is mapped differently depending on the selected backend

For backend trade-offs, see:

- [Backend Comparison](../architecture/BACKEND_COMPARISON.md)

---

## 5.5 Evaluate and Generate Reports

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

### Key Arguments

- `--symbol`
- `--tf`
- `--label`
- `--capital`
- `--risk`
- `--commission`
- `--tp`
- `--sl`
- `--slippage`
- `--use-labels` — backtest the raw labels directly instead of model predictions

### Default Artifacts

- `outputs/reports/{symbol}/{tf}/{symbol}_{tf}_{label}_R{tp*10}_candlestick.html`
- `outputs/reports/{symbol}/{tf}/{symbol}_{tf}_{label}_R{tp*10}_equity.png`
- `outputs/reports/{symbol}/{tf}/{symbol}_{tf}_{label}_R{tp*10}_heatmap.png`

For a deeper explanation of reports and metrics, see:

- [Evaluation Guide](EVALUATION_GUIDE.md)

---

## 5.6 Start the Inference Server

```bash
pixi run mlfx serve
pixi run mlfx serve --host 0.0.0.0 --port 8000
pixi run mlfx serve --reload
```

### Purpose

Launch a FastAPI server exposing real-time prediction endpoints. The server loads the best registered model on demand.

### Key Arguments

- `--host` — bind address (default: `0.0.0.0`)
- `--port` — listen port (default: `8000`)
- `--reload` — enable hot-reload for development only

For endpoint details, see:

- [API Reference](../reference/API_REFERENCE.md)

---

## 5.7 Benchmark Multiple Backends

```bash
pixi run mlfx benchmark --symbol XAUUSD --tf 1H --label label_10 --backends mlf sgd stats
```

### Purpose

Run multiple backends sequentially on the same dataset and print a comparison table.

### Key Arguments

- `--backends` — space-separated list  
  Default: `mlf sgd stats`  
  Full set: `mlf lstm bilstm transformer cnn_lstm sgd stats neuralforecast`
- `--n-trials` — Optuna trials per backend (default: `5`)
- `--n-splits` — cross-validation folds (default: `3`)
- `--force` — retrain even if a saved model exists (default: `false`)

### Artifact

- `outputs/reports/{symbol}/{tf}/benchmark_{timestamp}.json`

---

## 5.8 Batch Inference

```bash
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H --label label_10
```

### Purpose

Run the best registered model over all bars and write predictions to disk.

### Key Arguments

- `--symbol`
- `--tf`
- `--label`

### Artifact

- `outputs/predictions/{symbol}/{tf}/{label}_predictions.parquet`

---

## 5.9 List Registered Models

```bash
pixi run mlfx models
pixi run mlfx models --symbol XAUUSD
pixi run mlfx models --tf 1H --backend mlf
```

### Purpose

List all entries in the model registry stored in `outputs/models/registry.json`.

### Key Arguments

- `--symbol` — filter by symbol
- `--tf` — filter by timeframe
- `--backend` — filter by backend key

---

## 5.10 Detect Drift

```bash
pixi run mlfx drift --symbol XAUUSD --tf 1H
pixi run mlfx drift --symbol XAUUSD --tf 1H --threshold-ks 0.1 --threshold-psi 0.2
```

### Purpose

Compare recent feature distributions against reference snapshots and detect drift.

### Key Arguments

- `--symbol`
- `--tf`
- `--threshold-ks` — KS test threshold (default: `0.1`)
- `--threshold-psi` — PSI threshold (default: `0.2`)

---

## 6. Artifacts and Tracking

Every training run produces:

- **Model artifact** — `outputs/models/{symbol}/{tf}/{run_id}.pkl` (or `.pt` for deep learning backends)
- **Registry entry** — appended to `outputs/models/registry.json`
- **Metrics log** — `outputs/runs/{symbol}/{tf}/metrics_log.jsonl`
- **Run files** — `outputs/runs/{symbol}/{tf}/{run_id}.json` when MLflow is not installed

### Experiment Tracking

MLflow is used automatically when installed. If it is not installed, a lightweight `FileTracker` is used instead.

```bash
# With MLflow
pixi run mlfx train ...

# Without MLflow (FileTracker)
pixi run mlfx train ...
```

To install MLflow:

```bash
pip install mlflow
```

---

## 7. Quick Verification Checklist

After each stage, check:

- After `download`: parquet files exist under `data/raw/{symbol}/`
- After `qa`: a quality report exists
- After `pipeline`: parquet files exist under `data/ohlcv/`, `data/features/`, and `data/labels/`
- After `train`: new artifacts appear under `outputs/models/{symbol}/{tf}/`
- After `evaluate`: new HTML and PNG reports appear under `outputs/reports/{symbol}/{tf}/`
- After `batch-predict`: prediction parquet files appear under `outputs/predictions/{symbol}/{tf}/`
- After `drift`: thresholds are evaluated and output is produced as expected

---

## 8. Safe Cleanup

Clear common caches and generated artifacts:

```bash
pixi run clean-generated
```

Use it when:

- You want a cleaner workspace before rerunning benchmarks or smoke tests
- Repeated training runs created many `lightning_logs`
- Old reports and caches are making validation harder

For incident handling and diagnostics, see:

- [Troubleshooting](TROUBLESHOOTING.md)

If you need the fastest runnable flow, use:

- [Quickstart](../getting-started/QUICKSTART.md)

---

## 9. Training Backend Defaults

The CLI `--n-trials` and `--n-splits` flags apply mainly to the `mlf` backend via Optuna. Other backends use built-in defaults unless configured otherwise.

| Backend | Key Defaults |
|---|---|
| `mlf` | `n_trials` from CLI (default `15`), `n_splits` from CLI (default `5`) |
| `lstm` | `n_trials=10`, `seq_len=60`, `epochs=30`, `batch_size=128`, `patience=5`, `top_k_features=20` |
| `bilstm` | same as `lstm` |
| `transformer` | same as `lstm` |
| `cnn_lstm` | same as `lstm` |
| `sgd` | `batch_size=500` |
| `stats` | `n_splits` from CLI, `season_length=24` |
| `neuralforecast` | `input_size=48`, `max_steps=200`, `max_samples=5000` |

---

## 10. Practical Notes

### Drift Thresholds

The `drift` command supports:

- `--threshold-ks` (default: `0.1`)
- `--threshold-psi` (default: `0.2`)

Use stricter thresholds when you want earlier alerts, and looser thresholds when the workflow is producing too many false positives.

### Benchmark Reports

After `benchmark` completes, a JSON report is saved to:

- `outputs/reports/{symbol}/{tf}/benchmark_{timestamp}.json`

### Serving API

When `mlfx serve` is running, the following endpoints are available:

- `GET /health`
- `GET /models`
- `POST /predict`

For full schemas and examples, see:

- [API Reference](../reference/API_REFERENCE.md)

---

## 11. See Also

- [Quickstart](../getting-started/QUICKSTART.md)
- [Beginner Guide](../getting-started/NOOB_GUIDE.md)
- [Evaluation Guide](EVALUATION_GUIDE.md)
- [Configuration Reference](../reference/CONFIG_REFERENCE.md)
- [API Reference](../reference/API_REFERENCE.md)
- [Backend Comparison](../architecture/BACKEND_COMPARISON.md)
- [English Docs Hub](../README.md)
