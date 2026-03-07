# ML_FX - Beginner Guide

If you are new to the repository, read this before running commands. The goal is to understand what the project does, how data moves through the system, and why the pipeline must be run in order.

## 1. What this project does

ML_FX is a research pipeline for price data:
- download historical tick data
- resample it into OHLCV bars
- build technical features
- generate future-direction labels
- train models
- backtest on labeled datasets

It is not a finished live-trading bot.

## 2. High-level pipeline

```text
Tick data
  -> OHLCV
  -> Features
  -> Labels
  -> Train
  -> Backtest
```

Each stage maps to a file group:
- [pipeline/download_data.py](../../pipeline/download_data.py)
- [pipeline/resample.py](../../pipeline/resample.py)
- [pipeline/features.py](../../pipeline/features.py)
- [pipeline/labels.py](../../pipeline/labels.py)
- [models/](../../models/) (all `*.py` files)
- [eval/run_eval.py](../../eval/run_eval.py)

## 3. Why the order matters

### 3.1 Tick -> OHLCV

Tick data is dense and noisy. [pipeline/resample.py](../../pipeline/resample.py) converts ticks into bars such as `1m`, `5m`, and `1H`, which makes later processing manageable.

### 3.2 OHLCV -> Features

[pipeline/features.py](../../pipeline/features.py) adds context to each bar, for example:
- session state from `ICT Killzone`
- `Support/Resistance` levels
- `Pivot Points`
- common indicators such as RSI, MACD, ATR, and EMA

Without features, the model only sees raw price values and has much less structure to learn from.

### 3.3 Features -> Labels

[pipeline/labels.py](../../pipeline/labels.py) creates labels such as `label_5`, `label_10`, and `label_20`. Each label describes the future direction after a given look-ahead horizon.

This is what turns the problem into supervised learning.

### 3.4 Labels -> Train

Files under `models/` read labeled data and train the selected backend. The repository currently includes several backends:
- [models/ml_models.py](../../models/ml_models.py)
- [models/lstm.py](../../models/lstm.py)
- [models/transformer.py](../../models/transformer.py)
- [models/cnn_lstm.py](../../models/cnn_lstm.py)
- [models/online_sgd.py](../../models/online_sgd.py)
- [models/stats_baseline.py](../../models/stats_baseline.py)
- [models/neural_forecast.py](../../models/neural_forecast.py)

### 3.5 Train -> Backtest

[eval/run_eval.py](../../eval/run_eval.py) and [eval/backtest.py](../../eval/backtest.py) simulate trades from a signal column, while [viz/charts.py](../../viz/charts.py) writes:
- candlestick HTML
- equity curve PNG
- heatmap PNG

## 4. Fastest way to start

If you only want to try the repo quickly:

```bash
pixi install
pixi run python main.py
```

Inside the TUI, follow this order:
1. `Download Data`
2. `Pipeline`
3. `Train Model`
4. `Backtest`

If you prefer CLI commands, open [USAGE_GUIDE.md](USAGE_GUIDE.md).

## 5. Things to remember

- if training fails because files are missing, you usually skipped [pipeline/features.py](../../pipeline/features.py) or [pipeline/labels.py](../../pipeline/labels.py)
- `outputs/models/` stores model artifacts and metrics
- `outputs/reports/` stores backtest reports
- `agent/` is not yet a complete end-user feature

## 6. What to read next

- [USAGE_GUIDE.md](USAGE_GUIDE.md): command-by-command usage
- [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md): how to read backtest outputs
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md): environment and data issues
- [GLOSSARY.md](GLOSSARY.md): common terms
