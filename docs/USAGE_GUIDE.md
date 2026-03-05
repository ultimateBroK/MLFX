# ML_FX Pipeline Usage Guide

This project is a dedicated Data Pipeline and Machine Learning Engine for trading **XAUUSD (Gold)**. It is managed by `pixi` and uses Polars to process 10+ years of tick data efficiently on standard hardware.

> 📚 **NEW HERE? Start by reading these guides before running any code:**
> 1. [NOOB_GUIDE.md](NOOB_GUIDE.md) - High-level overview of how the system works.
> 2. [GLOSSARY.md](GLOSSARY.md) - Definitions for common trading and ML terms.
> 3. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Solutions for common errors.

---

## 1. Environment Setup

We use `pixi` (a fast, Rust-based package manager) to handle all dependencies instead of `pip` or `conda`.

```bash
# Install Pixi (if you don't have it yet)
curl -fsSL https://pixi.sh/install.sh | bash

# Install all project dependencies
pixi install
```

---

## 2. The Data Pipeline (Tick Data to ML Features)

### Step 1: Download Data
Download historical tick data from Dukascopy. Data is saved as partitioned Parquet files in `data/raw/{symbol}/`.

```bash
# Download XAUUSD (default)
pixi run python pipeline/download_data.py

# Download Crypto or other Forex symbols
pixi run python pipeline/download_data.py --symbol BTCUSD --asset-class crypto
```
> *Tip*: If your download is interrupted, you can safely restart it. The script tracks progress in `completed_months.json` and resumes automatically.

---

### Step 1.5: Data Quality Assurance (QA)
Scan the raw Parquet files to detect any significant gaps, missing hours, or bad data (e.g., negative prices).

```bash
pixi run python pipeline/qa_data.py --symbol XAUUSD
```
*Reports are saved at*: `data/raw/{symbol}/{symbol}_Data_Quality_Report.md`

---

### Step 2: Resample Data (Tick to OHLCV Candlesticks)
Tick data is too dense for direct Machine Learning. This script converts ticks into structured timeframes (e.g., 1m, 5m, 15m, 30m, 1H, 2H, 4H, 1D) and correctly handles weekend market gaps.

```bash
# Generate 1-Hour (1H) and 5-Minute (5m) candlesticks
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H
pixi run python pipeline/resample.py --symbol XAUUSD --tf 5m
```
*Output*: `data/ohlcv/XAUUSD/1H/`

---

### Step 3: Feature Engineering
Generates over **133 technical features** to help the AI understand the market.
* **Momentum**: RSI, MACD, EMA.
* **Structure**: Pivot points and Support/Resistance logic based on volume.
* **ICT Concepts**: Order Blocks, Fair Value Gaps, and Session Killzones (Asian, London, New York).

```bash
pixi run python pipeline/features.py --symbol XAUUSD --tf 1H
```
*Output*: `data/features/XAUUSD/1H/`

---

### Step 4: Label Generation (Defining the Target)
The AI needs to know the correct answer for historical data. The label designates the expected price direction after `N` future candles using dynamic ATR-based thresholds (filtering out sideways noise).

* **`+1`**: LONG (Price goes up)
* **`-1`**: SHORT (Price goes down)
* **`0`**: NEUTRAL (Sideways/Choppy)

```bash
# Create target labels for 5, 10, and 20 candles into the future
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H --horizons 5 10 20
```
*Output*: `data/labels/XAUUSD/1H/`

---

## 3. Train Machine Learning Models

Now that the data is ready, you can train models to predict future price direction. Our pipelines leverage Time Series Splits and Optuna hyperparameter tuning to prevent lookahead bias.

```bash
# 1. Train a Baseline KNN model
pixi run python models/knn.py --symbol XAUUSD --tf 1H --label label_10 --k 10

# 2. Train XGBoost/LightGBM (Robust Gradient Boosting)
pixi run python models/gradient_boost.py --symbol XAUUSD --tf 1H --label label_10 --backend xgb --trials 30

# 3. Train LSTM (Deep Learning for sequential patterns)
pixi run python models/lstm.py --symbol XAUUSD --tf 1H --label label_10 --epochs 50 --seq-len 50
```

> **How do I know the model is learning?**
> The `gradient_boost.py` script automatically exports `Feature Importance` and `SHAP values` plots in `outputs/models/`. These charts show exactly which technical conditions effectively triggered the AI's Buy or Sell decisions.

---

## 4. Backtesting and Evaluation

Once a model is trained, it's injected directly into the backtesting engine. The script simulates trades using clear Risk/Reward parameters (e.g., Risking 1R to make 1.5R) and calculates performance metrics.

To run a simulation for a specific month (e.g., Feb 2026):

```bash
pixi run python eval/run_eval.py --data data/labels/XAUUSD/1H/2026-02.parquet --label label_5 --tp 1.5 --sl 1.0
```

After execution, it prints Total Trades, Win Rate, and Risk/Reward parameters to the terminal, and automatically generates visualizations inside the `outputs/reports/` folder. Please read [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) to understand how to read these charts.
