# ML_FX — Configuration & Usage Guide

This guide explains **every parameter** of all tools in ML_FX — from the TUI (`main.py`) to each individual CLI script.

> 📚 **New here?** Read these first:
> - [NOOB_GUIDE.md](NOOB_GUIDE.md) — Understand how the system works
> - [GLOSSARY.md](GLOSSARY.md) — Trading / ML terminology definitions

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [The Fastest Way — TUI (`main.py`)](#2-the-fastest-way--tui-mainpy)
3. [`config.toml` Configuration](#3-configtoml-configuration)
4. [CLI: Download Data](#4-cli-download-data)
5. [CLI: Resample (Tick → OHLCV)](#5-cli-resample-tick--ohlcv)
6. [CLI: Feature Engineering](#6-cli-feature-engineering)
7. [CLI: Label Generation](#7-cli-label-generation)
8. [CLI: Train Model](#8-cli-train-model)
9. [CLI: Backtest & Evaluation](#9-cli-backtest--evaluation)
10. [Environment Reproducibility](#10-environment-reproducibility)

---

## 1. Environment Setup

```bash
# Install Pixi (first time only)
curl -fsSL https://pixi.sh/install.sh | bash

# Install all project dependencies
pixi install
```

> **Why Pixi?** Pixi locks the exact versions of TA-Lib, Polars, PyTorch, and XGBoost in `pixi.lock`. Anyone cloning the repo gets the _exact_ same environment.

---

## 2. The Fastest Way — TUI (`main.py`)

Launch the interactive Terminal interface:

```bash
pixi run python main.py
```

| Key           | Function                 |
| ------------- | ------------------------ |
| `q`           | Quit                     |
| `d`           | Toggle dark / light mode |
| `Tab` / click | Switch tabs              |

The UI has **4 tabs**, each corresponding to a pipeline step:

| Tab             | Step                              |
| --------------- | --------------------------------- |
| 📥 Download Data | Download tick data from Dukascopy |
| 🔄 Pipeline      | Resample → Features → Labels      |
| 🧠 Train Model   | Train XGBoost / LightGBM          |
| 📊 Backtest      | Run walk-forward backtest         |

When you click **▶ Run** on any tab, the task runs in the background — the UI remains responsive, and logs stream directly into the right panel.

---

## 3. `config.toml` Configuration

The `config.toml` file in the root directory contains **default values** that populate the TUI forms on startup. Edit this file to change your defaults.

```toml
# ── Download ──────────────────────────────────────────────────
[download]
symbol      = "XAUUSD"    # Symbol to download
asset_class = "fx"        # "fx" (Forex/Gold) | "crypto" (Bitcoin...)
start_year  = 2015        # Starting year for download
start_month = 1           # Starting month (1–12)
concurrency = 20          # Concurrent connections (20 is optimal)

# ── Pipeline (Resample + Features + Labels) ───────────────────
[pipeline]
symbol       = "XAUUSD"
timeframe    = "1H"          # Timeframe (see table below)
pivot_type   = "traditional" # Pivot Point type
pivot_anchor = "daily"       # Anchor TF for Pivots

# ── Train Model ───────────────────────────────────────────────
[train]
symbol    = "XAUUSD"
timeframe = "1H"
label_col = "label_10"  # "label_5" | "label_10" | "label_20"
backend   = "xgb"       # "xgb" (XGBoost) | "lgb" (LightGBM)
n_trials  = 30          # Optuna trials (higher = better but slower)
n_splits  = 5           # TimeSeriesSplit (CV) folds

# ── Backtest ──────────────────────────────────────────────────
[backtest]
symbol    = "XAUUSD"
timeframe = "1H"
label_col = "label_10"
```

### Valid Values

**Symbol (all scripts):**

| Symbol                       | Type   | Notes                        |
| ---------------------------- | ------ | ---------------------------- |
| `XAUUSD`                     | Gold   | Project default              |
| `EURUSD`, `GBPUSD`, `USDJPY` | Forex  | Popular pairs                |
| `BTCUSD`, `ETHUSD`           | Crypto | Use `asset_class = "crypto"` |

**Timeframe (`timeframe`):**

| Value         | Meaning         | Notes                               |
| ------------- | --------------- | ----------------------------------- |
| `1m`          | 1 minute        | Very large files, needs lots of RAM |
| `5m`          | 5 minutes       | Common for scalping                 |
| `15m` / `30m` | 15 / 30 minutes | Intraday swing                      |
| `1H`          | 1 hour          | **Recommended default**             |
| `2H` / `4H`   | 2 / 4 hours     | Swing trading                       |
| `1D`          | 1 day           | Long term                           |

**Label Column (`label_col`):**

| Value      | Meaning                                             |
| ---------- | --------------------------------------------------- |
| `label_5`  | Forecast 5 candles ahead (~5 hours on 1H TF)        |
| `label_10` | Forecast 10 candles ahead (~10 hours) — Recommended |
| `label_20` | Forecast 20 candles ahead (~1 market day)           |

**Pivot Type (`pivot_type`):**

| Value         | Description                      |
| ------------- | -------------------------------- |
| `traditional` | `P = (H+L+C)/3` — Most common    |
| `fibonacci`   | Fib levels 0.236 / 0.382 / 0.618 |
| `woodie`      | Emphasizes closing price         |
| `classic`     | Classic pivots                   |
| `demark`      | Only 3 levels: P, R1, S1         |
| `camarilla`   | 9 intraday levels                |

**Pivot Anchor (`pivot_anchor`):**

| Value     | Description                      |
| --------- | -------------------------------- |
| `daily`   | Reset pivots daily — Recommended |
| `weekly`  | Reset pivots weekly              |
| `monthly` | Reset pivots monthly             |

---

## 4. CLI: Download Data

```bash
pixi run python pipeline/download_data.py [OPTIONS]
```

| Parameter        | Default       | Description                                    |
| ---------------- | ------------- | ---------------------------------------------- |
| `--symbol`       | `XAUUSD`      | Symbol to download                             |
| `--start-year`   | `2015`        | Starting year                                  |
| `--start-month`  | `1`           | Starting month (1–12)                          |
| `--end-year`     | Current year  | Ending year                                    |
| `--end-month`    | Current month | Ending month                                   |
| `--asset-class`  | `fx`          | `fx` or `crypto`                               |
| `--concurrency`  | `20`          | Concurrent async connections                   |
| `--force-repair` | False         | Force re-verification of ALL downloaded months |

**Examples:**
```bash
# Download XAUUSD from 2020 to present
pixi run python pipeline/download_data.py --start-year 2020

# Download Bitcoin (24/7, doesn't skip weekends)
pixi run python pipeline/download_data.py --symbol BTCUSD --asset-class crypto

# Slower but more stable download (reduce concurrency)
pixi run python pipeline/download_data.py --concurrency 5

# Verify and patch missing hours for all months
pixi run python pipeline/download_data.py --force-repair
```

> 💡 **Subsequent runs are faster:** The script reads `data/raw/{symbol}/completed_months.json` and _skips_ completely downloaded months.

---

## 5. CLI: Resample (Tick → OHLCV)

```bash
pixi run python pipeline/resample.py [OPTIONS]
```

| Parameter  | Default  | Description                                    |
| ---------- | -------- | ---------------------------------------------- |
| `--symbol` | `XAUUSD` | Symbol to resample                             |
| `--tf`     | _(all)_  | Specific timeframe. Empty = resample all 8 TFs |
| `--force`  | False    | Overwrite existing files                       |

**Examples:**
```bash
# Resample all 8 timeframes (1m, 5m, 15m, 30m, 1H, 2H, 4H, 1D)
pixi run python pipeline/resample.py --symbol XAUUSD

# Only resample 1H
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H

# Regenerate from scratch (clear cache)
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H --force
```

*Output directory:* `data/ohlcv/{symbol}/{tf}/YYYY-MM.parquet`

---

## 6. CLI: Feature Engineering

```bash
pixi run python pipeline/features.py [OPTIONS]
```

| Parameter  | Default       | Description                                |
| ---------- | ------------- | ------------------------------------------ |
| `--symbol` | `XAUUSD`      | Symbol                                     |
| `--tf`     | `1H`          | Timeframe (matching OHLCV file must exist) |
| `--pivot`  | `traditional` | Pivot Point type                           |
| `--anchor` | `daily`       | Target Anchor timeframe for Pivots         |
| `--force`  | False         | Overwrite existing files                   |

**Examples:**
```bash
# Default features (133+ columns)
pixi run python pipeline/features.py --symbol XAUUSD --tf 1H

# Use Fibonacci pivots with weekly anchors
pixi run python pipeline/features.py --symbol XAUUSD --tf 4H --pivot fibonacci --anchor weekly
```

*Output directory:* `data/features/{symbol}/{tf}/YYYY-MM.parquet`

---

## 7. CLI: Label Generation

```bash
pixi run python pipeline/labels.py [OPTIONS]
```

| Parameter    | Default   | Description                                                                   |
| ------------ | --------- | ----------------------------------------------------------------------------- |
| `--symbol`   | `XAUUSD`  | Symbol                                                                        |
| `--tf`       | `1H`      | Timeframe                                                                     |
| `--horizons` | `5 10 20` | Look-ahead horizons list (in candles)                                         |
| `--atr-mult` | `0.5`     | ATR multiplier for LONG/SHORT thresholds. Higher = fewer but stronger signals |
| `--force`    | False     | Overwrite                                                                     |

**Examples:**
```bash
# Default labels (3 horizons: 5, 10, 20 candles)
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H

# Only label 10 candles, higher ATR threshold (fewer LONG/SHORT, more NEUTRAL)
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H --horizons 10 --atr-mult 1.0
```

> **What does `atr-mult` do?**
> - `0.3` → Sensitive — many LONG/SHORT signals, more noise
> - `0.5` → Balanced (recommended)
> - `1.0` → Conservative — few signals, captures large moves only

*Output directory:* `data/labels/{symbol}/{tf}/YYYY-MM.parquet`

---

## 8. CLI: Train Model

### XGBoost / LightGBM

```bash
pixi run python models/gradient_boost.py [OPTIONS]
```

| Parameter   | Default    | Description                                               |
| ----------- | ---------- | --------------------------------------------------------- |
| `--symbol`  | `XAUUSD`   | Symbol                                                    |
| `--tf`      | `1H`       | Timeframe                                                 |
| `--label`   | `label_10` | Target label column                                       |
| `--backend` | `xgb`      | `xgb` (XGBoost) or `lgb` (LightGBM)                       |
| `--trials`  | `30`       | Optuna trials. Higher = better tuning but slower run time |
| `--splits`  | `5`        | TimeSeriesSplit CV folds                                  |
| `--force`   | False      | Retrain even if an existing model is found                |
| `--no-shap` | False      | Skip SHAP value computation (faster)                      |

**Examples:**
```bash
# Fast train (few trials, skip SHAP)
pixi run python models/gradient_boost.py --trials 10 --no-shap

# Comprehensive train with LightGBM
pixi run python models/gradient_boost.py --backend lgb --trials 100 --splits 7

# Force retrain from scratch
pixi run python models/gradient_boost.py --force
```

### KNN (Baseline)

```bash
pixi run python models/knn.py [OPTIONS]
```

| Parameter  | Default    | Description                                       |
| ---------- | ---------- | ------------------------------------------------- |
| `--symbol` | `XAUUSD`   | Symbol                                            |
| `--tf`     | `1H`       | Timeframe                                         |
| `--label`  | `label_10` | Label column                                      |
| `--k`      | `10`       | Neighbors (K). Lower = sensitive, Higher = stable |

### LSTM (Deep Learning)

```bash
pixi run python models/lstm.py [OPTIONS]
```

| Parameter      | Default    | Description                                      |
| -------------- | ---------- | ------------------------------------------------ |
| `--symbol`     | `XAUUSD`   | Symbol                                           |
| `--tf`         | `1H`       | Timeframe                                        |
| `--label`      | `label_10` | Label column                                     |
| `--epochs`     | `50`       | Training epochs. Higher = learns longer          |
| `--seq-len`    | `50`       | Input sequence length (candles/step). Try 50–200 |
| `--batch-size` | `64`       | Batch size. Reduce if you run out of GPU/RAM     |

---

## 9. CLI: Backtest & Evaluation

```bash
pixi run python eval/run_eval.py [OPTIONS]
```

| Parameter | Example                                 | Description                             |
| --------- | --------------------------------------- | --------------------------------------- |
| `--data`  | `data/labels/XAUUSD/1H/2026-02.parquet` | Labeled data file                       |
| `--label` | `label_5`                               | Target label column to evaluate against |
| `--tp`    | `1.5`                                   | Take Profit (in R-multiple)             |
| `--sl`    | `1.0`                                   | Stop Loss (in R-multiple)               |

**Examples:**
```bash
# Backtest with Risk:Reward = 1:1.5
pixi run python eval/run_eval.py \
  --data data/labels/XAUUSD/1H/2026-02.parquet \
  --label label_5 --tp 1.5 --sl 1.0
```

*Output:* Metrics output to terminal + performance charts generated in `outputs/reports/`

---

## 10. Environment Reproducibility

This project uses two files to ensure identical setups everywhere:

| File             | Purpose                                       |
| ---------------- | --------------------------------------------- |
| `pyproject.toml` | Declares dependencies and version constraints |
| `pixi.lock`      | Locks exact versions of EVERY package         |

**Always commit `pixi.lock` to Git** so peers don't run into version mismatch errors.

```bash
# Install exact environment from lock file
pixi install

# Update all packages to latest allowed versions (modifies pixi.lock)
pixi update
```

> ⚠️ Always run `pixi run pytest` after `pixi update` to ensure there are no breaking changes.
