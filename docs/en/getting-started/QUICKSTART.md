# MLFX Quickstart

This is the canonical onboarding flow for getting MLFX running end to end with the default `Pixi` workflow.

If you are new to the repository, start here first.

## What you will do

In the standard flow, you will:

1. Install the environment
2. Download historical tick data
3. Build OHLCV, features, and labels
4. Train a model
5. Evaluate the result with a backtest report

## Prerequisites

- `Pixi` installed locally
- Repository dependencies installed with `pixi install`
- A supported Linux environment

Install dependencies:

```bash
pixi install
```

## Canonical 5-step flow

### 1. Download raw tick data

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
```

What this does:
- Downloads Dukascopy tick data
- Stores raw parquet files under `data/raw/{symbol}/`
- Creates download state files for resume support

Expected output:
- `data/raw/XAUUSD/YYYY-MM.parquet`
- `data/raw/XAUUSD/completed_months.json`

---

### 2. Audit raw data quality

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

What this does:
- Checks raw data for gaps and anomalies
- Generates a quality report before downstream processing

Expected output:
- `data/raw/XAUUSD/XAUUSD_Data_Quality_Report.md`

> You can skip this step for a first trial run, but it is recommended for normal research workflows.

---

### 3. Run the feature pipeline

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
```

What this does:
- Resamples tick data into OHLCV bars
- Computes technical and ICT-oriented features
- Generates labels such as `label_5`, `label_10`, and `label_20`

Expected output:
- `data/ohlcv/XAUUSD/1H/`
- `data/features/XAUUSD/1H/`
- `data/labels/XAUUSD/1H/`

---

### 4. Train a model

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
```

What this does:
- Loads labeled data
- Trains the selected backend
- Stores model artifacts and metadata

Expected output:
- `outputs/models/XAUUSD/1H/`

Common backend choices:
- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

---

### 5. Evaluate with backtesting

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

What this does:
- Backtests the trained model if one exists
- Falls back to labels if no trained model is found
- Generates visual reports and summary metrics

Expected output:
- `outputs/reports/XAUUSD/1H/XAUUSD_1H_label_10_R15_candlestick.html`
- `outputs/reports/XAUUSD/1H/XAUUSD_1H_label_10_R15_equity.png`
- `outputs/reports/XAUUSD/1H/XAUUSD_1H_label_10_R15_heatmap.png`

## Minimal command set

If you want the shortest useful flow, run:

```bash
pixi install
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

## How to know each stage worked

- `download`: Raw parquet files exist under `data/raw/{symbol}/`
- `qa`: A markdown quality report exists under `data/raw/{symbol}/`
- `pipeline`: Parquet files exist under `data/ohlcv/`, `data/features/`, and `data/labels/`
- `train`: Model artifacts exist under `outputs/models/{symbol}/{tf}/`
- `evaluate`: HTML and PNG reports exist under `outputs/reports/{symbol}/{tf}/`

## Common first-run choices

For a stable first run, use:

- `symbol`: `XAUUSD`
- `asset-class`: `fx`
- `tf`: `1H`
- `label`: `label_10`
- `backend`: `mlf`

These defaults are practical because they keep the workflow simple and relatively lightweight.

## If something fails

Check these first:

1. Did you run `pixi install`?
2. Are you running commands with `pixi run`?
3. Does the previous stage's output exist?
4. Are you using the correct `symbol`, `tf`, and `label` consistently?

Typical stage order:

```text
download -> qa -> pipeline -> train -> evaluate
```

## Next reading

- `../README.md` — English docs hub
- `NOOB_GUIDE.md` — why the workflow is structured this way
- `../guides/USAGE_GUIDE.md` — full CLI usage and parameters
- `../guides/EVALUATION_GUIDE.md` — how to interpret reports and metrics
- `../guides/TROUBLESHOOTING.md` — common environment and data issues
- `../reference/CONFIG_REFERENCE.md` — `config.toml` defaults and CLI mappings
