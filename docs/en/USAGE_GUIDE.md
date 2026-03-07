# ML_FX - Configuration and Usage Guide

This guide explains how to run the project through the TUI and CLI based on the current codebase.

Related docs:
- [README.md](README.md)
- [NOOB_GUIDE.md](NOOB_GUIDE.md)
- [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 1. Environment Setup

The repository is intended to be run through `Pixi`.

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

Notes:
- [pyproject.toml](../../pyproject.toml) declares `requires-python >= 3.11`
- the Pixi environment is currently pinned to Python `3.13`
- the safest way to run commands is through `pixi run`

## 2. Launch the TUI

```bash
pixi run python main.py
```

The TUI exposes 4 tabs:
- `Download Data`
- `Pipeline`
- `Train Model`
- `Backtest`

Shortcuts:
- `q`: quit
- `d`: toggle dark/light mode

[main.py](../../main.py) reads [config.toml](../../config.toml) on startup and pre-fills the form values.

## 3. `config.toml`

Example configuration:

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
```

Key values:
- `asset_class`: `fx`, `crypto`
- `timeframe`: `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`
- `pivot_type`: `traditional`, `fibonacci`, `woodie`, `classic`, `demark`, `camarilla`
- `pivot_anchor`: `daily`, `weekly`, `monthly`
- `label_col`: `label_5`, `label_10`, `label_20`
- TUI `backend` options:
  - `mlf`
  - `lstm`
  - `transformer`
  - `cnn_lstm`
  - `sgd`
  - `stats`
  - `neuralforecast`

## 4. Full Workflow

The block below shows the standard end-to-end sequence for downloading data, generating features, labeling, training, and evaluating:

```bash
# 1) Download tick data
pixi run python pipeline/download_data.py --symbol XAUUSD --asset-class fx --start-year 2024

# 2) Audit raw data quality
pixi run python pipeline/qa_data.py --symbol XAUUSD --asset-class fx

# 3) Resample into OHLCV
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H

# 4) Build features
pixi run python pipeline/features.py --symbol XAUUSD --tf 1H --pivot traditional --anchor daily

# 5) Generate labels
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H --horizons 5 10 20 --atr-mult 0.5

# 6) Train a default backend
pixi run python models/ml_models.py --symbol XAUUSD --tf 1H --label label_10 --n-trials 15 --n-splits 5

# 7) Run evaluation on a labeled parquet file
pixi run python eval/run_eval.py \
  --data data/labels/XAUUSD/1H/2024-01.parquet \
  --symbol XAUUSD \
  --tf 1H \
  --label label_10 \
  --tp 1.5 \
  --sl 1.0 \
  --outdir outputs/reports
```

## 5. CLI by Stage

### 5.1 Download tick data

```bash
pixi run python pipeline/download_data.py [OPTIONS]
```

Arguments:
- `--symbol`: default `XAUUSD`
- `--start-year`: default `2015`
- `--start-month`: default `1`
- `--end-year`: current year by default
- `--end-month`: current month by default
- `--asset-class`: `fx` or `crypto`
- `--concurrency`: default `20`
- `--force-repair`: re-verify months that were already marked complete

Outputs:
- `data/raw/{symbol}/YYYY-MM.parquet`
- `data/raw/{symbol}/completed_months.json`

### 5.2 Raw data QA

```bash
pixi run python pipeline/qa_data.py --symbol XAUUSD --asset-class fx
```

This script reads `completed_months.json`, audits raw tick data, and generates a Markdown QA report inside the raw data directory.

### 5.3 Resample into OHLCV

```bash
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H
pixi run python pipeline/resample.py --symbol XAUUSD
```

Arguments:
- `--symbol`
- `--tf`: omit it to process every supported timeframe
- `--force`

Output:
- `data/ohlcv/{symbol}/{tf}/YYYY-MM.parquet`

### 5.4 Feature generation

```bash
pixi run python pipeline/features.py --symbol XAUUSD --tf 1H --pivot traditional --anchor daily
```

Arguments:
- `--symbol`
- `--tf`
- `--pivot`
- `--anchor`
- `--force`

Output:
- `data/features/{symbol}/{tf}/YYYY-MM.parquet`

### 5.5 Label generation

```bash
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H --horizons 5 10 20 --atr-mult 0.5
```

Arguments:
- `--symbol`
- `--tf`
- `--horizons`
- `--atr-mult`
- `--force`

Output:
- `data/labels/{symbol}/{tf}/YYYY-MM.parquet`

## 6. Train Models

### 6.1 `mlf` backend

```bash
pixi run python models/ml_models.py --symbol XAUUSD --tf 1H --label label_10 --n-trials 15 --n-splits 5
```

Use this when you want the main `MLForecast + LightGBM` baseline.

### 6.2 `lstm` backend

```bash
pixi run python models/lstm.py --symbol XAUUSD --tf 1H --label label_10
```

### 6.3 `transformer` backend

```bash
pixi run python models/transformer.py --symbol XAUUSD --tf 1H --label label_10
```

### 6.4 `cnn_lstm` backend

```bash
pixi run python models/cnn_lstm.py --symbol XAUUSD --tf 1H --label label_10
```

### 6.5 `sgd` backend

```bash
pixi run python models/online_sgd.py --symbol XAUUSD --tf 1H --label label_10
```

### 6.6 `stats` backend

```bash
pixi run python models/stats_baseline.py --symbol XAUUSD --tf 1H --label label_10 --n-splits 5
```

### 6.7 `neuralforecast` backend

```bash
pixi run python models/neural_forecast.py --symbol XAUUSD --tf 1H --label label_10 --n-windows 5 --input-size 48 --max-steps 200
```

Model artifacts and metrics are written to:
- `outputs/models/{symbol}/{tf}/`

Examples:
- `ml_models_label_10.pkl`
- `lstm_label_10.pt`
- `transformer_label_10.pt`
- `cnn_lstm_label_10.pt`
- `online_sgd_label_10.pkl`
- `stats_baseline_label_10.pkl`
- `neural_forecast_label_10.pkl`

## 7. Backtest and Evaluation

```bash
pixi run python eval/run_eval.py \
  --data data/labels/XAUUSD/1H/2024-01.parquet \
  --symbol XAUUSD \
  --tf 1H \
  --label label_10 \
  --tp 1.5 \
  --sl 1.0 \
  --slippage 0.0 \
  --outdir outputs/reports
```

Key arguments:
- `--data`: labeled parquet file
- `--symbol`
- `--tf`
- `--label`
- `--tp`
- `--sl`
- `--slippage`
- `--outdir`

Default outputs:
- `outputs/reports/{prefix}_candlestick.html`
- `outputs/reports/{prefix}_equity.png`
- `outputs/reports/{prefix}_heatmap.png`

Metric interpretation and chart reading are covered in [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md).

## 8. Operational Notes

- Run the pipeline in order: raw -> ohlcv -> features -> labels -> train -> backtest
- If training fails on missing files, inspect `data/features/` and `data/labels/`
- If a download is interrupted, rerun [pipeline/download_data.py](../../pipeline/download_data.py); progress is resumed via `completed_months.json`
- If you need a clean reset of generated data, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
