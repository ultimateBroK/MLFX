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
- `pixi run mlfx-tui`: TUI

Check help:

```bash
pixi run mlfx --help
pixi run mlfx pipeline --help
```

## 3. `config.toml`

`config.toml` is read by both the CLI and the TUI for default values.

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
```

Key fields:
- `asset_class`: `fx`, `crypto`
- `timeframe`: `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`
- `pivot_type`: `traditional`, `fibonacci`, `woodie`, `classic`, `demark`, `camarilla`
- `pivot_anchor`: `daily`, `weekly`, `monthly`
- `label_col`: `label_5`, `label_10`, `label_20`
- `backend`: `mlf`, `lstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`

## 4. TUI

Launch it:

```bash
pixi run mlfx-tui
```

The TUI currently exposes four tabs:
- `Download Data`
- `Pipeline`
- `Train Model`
- `Backtest`

Shortcuts:
- `q`: quit
- `d`: toggle dark/light mode

## 5. CLI by Stage

### 5.1 Download tick data

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
- `--concurrency`
- `--force`

Artifacts:
- `data/raw/{symbol}/YYYY-MM.parquet`
- `data/raw/{symbol}/completed_months.json`

### 5.2 Audit raw data

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

Purpose:
- detect meaningful gaps
- write a data-quality report

Artifact:
- `data/raw/{symbol}/{symbol}_Data_Quality_Report.md`

### 5.3 Run the pipeline

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
```

Examples that skip individual stages:

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-resample
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-features
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-labels
```

Key arguments:
- `--symbol`
- `--tf`
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

### 5.4 Train a model

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf --n-trials 15 --n-splits 5
```

Backends currently exposed through the CLI/TUI:
- `mlf`
- `lstm`
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

### 5.5 Evaluate and generate reports

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

Default artifacts:
- `outputs/reports/{symbol}/{tf}/{symbol}_{tf}_{label}_R{tp*10}_candlestick.html`
- `outputs/reports/{symbol}/{tf}/{symbol}_{tf}_{label}_R{tp*10}_equity.png`
- `outputs/reports/{symbol}/{tf}/{symbol}_{tf}_{label}_R{tp*10}_heatmap.png`

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

## 7. Quick Verification Checklist

After each stage, check:
- after `download`: parquet files exist under `data/raw/{symbol}/`
- after `qa`: a quality report exists
- after `pipeline`: parquet files exist under `data/ohlcv/`, `data/features/`, and `data/labels/`
- after `train`: new artifacts appear under `outputs/models/{symbol}/{tf}/`
- after `evaluate`: new HTML/PNG reports appear under `outputs/reports/{symbol}/{tf}/`

## 8. Safe Cleanup

Clear common caches and generated artifacts:

```bash
pixi run clean-generated
```

Use it when:
- you want a cleaner workspace before rerunning benchmarks or smoke tests
- repeated training runs created many `lightning_logs`
- old reports and caches are making validation harder

For incident handling and diagnostics, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
