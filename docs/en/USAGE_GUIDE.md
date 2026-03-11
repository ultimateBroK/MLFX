# MLFX - Configuration and Usage Guide

This guide describes the supported `Pixi-first` workflow for operating the project.

Related docs:
- [README.md](README.md)
- [NOOB_GUIDE.md](NOOB_GUIDE.md)
- [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 1. Environment Setup

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

Operating rules:
- run commands through `pixi run`
- Python and dependencies are managed from `pyproject.toml`
- no separate `uv` or `venv` workflow is required for the supported setup

Useful Pixi tasks:

```bash
pixi run test
pixi run verify
pixi run clean-generated
```

## 2. Official Entrypoints

- `pixi run mlfx`: unified CLI

Check help:

```bash
pixi run mlfx --help
pixi run mlfx pipeline --help
```

## 3. `config.toml`

`config.toml` is read by the CLI for default values.

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

Key fields:
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

## 4. CLI by Stage

### 4.1 Download tick data

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
```

Purpose:
- fetch raw tick data into `data/raw/`
- maintain download state for resume behavior

Key arguments:
- `--symbol`
- `--asset-class`
- `--start-year`
- `--start-month`
- `--end-year` *(optional, defaults to current year)*
- `--end-month` *(optional, defaults to current month)*
- `--concurrency`
- `--force`
- `--skip-current-month` — skip checking/repairing the current month

Artifacts:
- `data/raw/{symbol}/YYYY-MM.parquet`
- `data/raw/{symbol}/completed_months.json`

### 4.2 Audit raw data

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

Purpose:
- detect meaningful gaps
- write a data-quality report

Artifact:
- `data/raw/{symbol}/{symbol}_Data_Quality_Report.md`

### 4.3 Run the pipeline

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
# Multiple timeframes at once:
pixi run mlfx pipeline --symbol XAUUSD --tf 1H 4H 1D
```

Examples that skip individual stages:

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-resample
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-features
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-labels
```

Key arguments:
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

Artifacts:
- `data/ohlcv/{symbol}/{tf}/`
- `data/features/{symbol}/{tf}/`
- `data/labels/{symbol}/{tf}/`

### 4.4 Train a model

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf --n-trials 15 --n-splits 5
```

Backends currently exposed through the CLI:
- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

Key arguments:
- `--symbol`
- `--tf`
- `--label`
- `--backend`
- `--n-trials`
- `--n-splits`
- `--force`

Artifacts:
- `outputs/models/{symbol}/{tf}/`

Notes:
- `n_trials` is most relevant for the `mlf` backend
- `n_splits` is mapped differently depending on the selected backend

### 4.5 Evaluate and generate reports

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

Key arguments:
- `--symbol`
- `--tf`
- `--label`
- `--capital`
- `--risk`
- `--commission`
- `--tp`
- `--sl`
- `--slippage`
- `--use-labels` — backtest the raw labels directly (no model). Useful as a baseline before evaluating a trained model. Default: automatically uses the best registered model if one exists, otherwise falls back to labels.

Default artifacts:
- `outputs/reports/{symbol}/{tf}/{symbol}_{tf}_{label}_R{tp*10}_candlestick.html`
- `outputs/reports/{symbol}/{tf}/{symbol}_{tf}_{label}_R{tp*10}_equity.png`
- `outputs/reports/{symbol}/{tf}/{symbol}_{tf}_{label}_R{tp*10}_heatmap.png`

### 4.6 Start the inference server

```bash
pixi run mlfx serve
pixi run mlfx serve --host 0.0.0.0 --port 8000
pixi run mlfx serve --reload  # hot-reload for development
```

Launches a FastAPI server exposing real-time prediction endpoints. The server loads the best registered model on demand.

Key arguments:
- `--host` — bind address (default: `0.0.0.0`)
- `--port` — listen port (default: `8000`)
- `--reload` — enable hot-reload (development mode only)

See [Section 8](#8-rest-api-reference) for the full API reference.

### 4.7 Benchmark multiple backends

```bash
pixi run mlfx benchmark --symbol XAUUSD --tf 1H --label label_10 --backends mlf sgd stats
```

Runs multiple backends sequentially on the same dataset and prints a comparison table.

Key arguments:
- `--backends` — space-separated list (default: `mlf sgd stats`; all options: `mlf lstm bilstm transformer cnn_lstm sgd stats neuralforecast`)
- `--n-trials` — Optuna trials per backend (default: `5`)
- `--n-splits` — cross-validation folds (default: `3`)
- `--force` — retrain even if a saved model exists (default: `false`)

Artifact:
- `outputs/reports/{symbol}/{tf}/benchmark_{timestamp}.json`

### 4.8 Batch inference

```bash
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H --label label_10
```

Runs the best registered model over all bars and writes predictions to disk.

Key arguments:
- `--symbol`
- `--tf`
- `--label`

Artifact:
- `outputs/predictions/{symbol}/{tf}/{label}_predictions.parquet`

### 4.9 List registered models

```bash
pixi run mlfx models
pixi run mlfx models --symbol XAUUSD
pixi run mlfx models --tf 1H --backend mlf
```

Lists all entries in the model registry (`outputs/models/registry.json`) with optional filtering.

Key arguments:
- `--symbol` — filter by symbol
- `--tf` — filter by timeframe
- `--backend` — filter by backend key

## 5. Artifacts & Tracking

Every training run produces:
- **Model artifact** — `outputs/models/{symbol}/{tf}/{run_id}.pkl` (or `.pt` for DL backends)
- **Registry entry** — appended to `outputs/models/registry.json` (best CV F1 used to select the "best" model)
- **Metrics log** — `outputs/runs/{symbol}/{tf}/metrics_log.jsonl` — one JSON line per run, append-only
- **Run files** — `outputs/runs/{symbol}/{tf}/{run_id}.json` — full run details when MLflow is not installed

### Experiment tracking

MLflow is used automatically when installed. If it is not installed, a lightweight `FileTracker` is used instead:

```bash
# With MLflow:
pixi run mlfx train ...  # logs to MLflow experiment named "mlfx"

# Without MLflow (FileTracker):
pixi run mlfx train ...  # logs to outputs/runs/{symbol}/{tf}/
```

To install MLflow:
```bash
pip install mlflow
```

## 6. Full Workflow

```bash
# 1) Download tick data
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024

# 2) Audit raw data
pixi run mlfx qa --symbol XAUUSD --asset-class fx

# 3) Build OHLCV, features, and labels
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --pivot traditional --anchor daily --atr-mult 0.5

# 4) Train
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf --n-trials 15 --n-splits 5

# 5) Evaluate
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

## 6. Quick Verification Checklist

After each stage, check:
- after `download`: parquet files exist under `data/raw/{symbol}/`
- after `qa`: a quality report exists
- after `pipeline`: parquet files exist under `data/ohlcv/`, `data/features/`, and `data/labels/`
- after `train`: new artifacts appear under `outputs/models/{symbol}/{tf}/`
- after `evaluate`: new HTML/PNG reports appear under `outputs/reports/{symbol}/{tf}/`

## 7. Safe Cleanup

Clear common caches and generated artifacts:

```bash
pixi run clean-generated
```

Use it when:
- you want a cleaner workspace before rerunning benchmarks or smoke tests
- repeated training runs created many `lightning_logs`
- old reports and caches are making validation harder

For incident handling and diagnostics, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

> **Note on `drift`**: The threshold parameters `--threshold-ks` (default: 0.1) and `--threshold-psi` (default: 0.2) can be adjusted to tune sensitivity. Run `pixi run mlfx drift --help` for full options.

> **Note on `benchmark`**: After completion, a JSON report is saved to `outputs/reports/{symbol}/{tf}/benchmark_{timestamp}.json` alongside the console table.

---

## 8. Training Backend Defaults

The CLI `--n-trials` and `--n-splits` flags apply to the `mlf` backend (via Optuna). Deep-learning and other backends use fixed defaults that can be overridden via `config.toml`.

| Backend | Key defaults |
|---|---|
| `mlf` | `n_trials` from CLI (default 15), `n_splits` from CLI (default 5) |
| `lstm` | `n_trials=10`, `seq_len=60`, `epochs=30`, `batch_size=128`, `patience=5`, `top_k_features=20` |
| `bilstm` | same as `lstm` |
| `transformer` | same as `lstm` |
| `cnn_lstm` | same as `lstm` |
| `sgd` | `batch_size=500` |
| `stats` | `n_splits` from CLI, `season_length=24` |
| `neuralforecast` | `input_size=48`, `max_steps=200`, `max_samples=5000` |

---

## 9. REST API Reference

When `mlfx serve` is running, the following endpoints are available.

### `GET /health`

Liveness probe — returns `{"status": "ok"}`. Use for load-balancer health checks.

### `GET /models`

List all registered models. Optional query parameters: `symbol`, `tf`, `backend`.

```
GET /models?symbol=XAUUSD&tf=1H
```

Returns: array of registry entries (same format as `mlfx models`).

### `POST /predict`

Run inference for a single feature vector.

**Request body:**

```json
{
  "symbol": "XAUUSD",
  "tf": "1H",
  "label_col": "label_10",
  "features": {
    "rsi_14": 55.3,
    "atr_14": 2.1,
    "ema_20": 1940.5,
    "...": "..."
  }
}
```

**Response body:**

```json
{
  "symbol": "XAUUSD",
  "tf": "1H",
  "prediction": 1,
  "confidence": 0.72,
  "model_backend": "mlf"
}
```

Field notes:
- `prediction`: one of `-2, -1, 0, 1, 2` (ordinal label)
- `confidence`: probability of the predicted class from `predict_proba()` — `null` for deep-learning backends
- `model_backend`: the backend key of the loaded model

Errors:
- `404` — no registered model for the requested symbol/tf/label_col
- `422` — missing required feature columns in the request body
