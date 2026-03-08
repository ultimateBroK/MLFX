# MLFX - Beginner Guide

If you are new to the repository, start here. The goal is to understand where data flows, why stage order matters, and how to get started safely with `Pixi`.

## 1. What this project does

MLFX is a market-data research pipeline that:
- downloads historical tick data
- converts ticks into OHLCV bars
- builds technical and ICT-oriented features
- generates future-direction labels
- trains models
- backtests and reports results

It is a research and evaluation environment, not a finished live-trading bot.

## 2. High-level pipeline

```text
Tick data
  -> QA
  -> OHLCV
  -> Features
  -> Labels
  -> Train
  -> Backtest
```

In the codebase, these stages live in:
- `mlfx.ingestion`
- `mlfx.pipeline`
- `mlfx.training`
- `mlfx.evaluation`

## 3. Why the order matters

### Tick -> QA

After downloading, audit raw data for gaps, damaged months, and obvious anomalies before moving on.

### Tick -> OHLCV

Tick data is dense. Resampling converts it into bars such as `1m`, `5m`, and `1H`, which are easier to process.

### OHLCV -> Features

Feature engineering adds context such as:
- ICT session features
- support/resistance
- pivot points
- RSI, MACD, ATR, EMA

### Features -> Labels

Labels such as `label_5`, `label_10`, and `label_20` define the supervised target.

### Labels -> Train

The CLI/TUI currently exposes these backends:
- `mlf`
- `lstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

### Train -> Backtest

Backtesting consumes a label column as a signal source and generates:
- candlestick HTML
- equity curve PNG
- heatmap PNG

## 4. Fastest way to start

If you just want to try the project:

```bash
pixi install
pixi run mlfx-tui
```

Or use the CLI:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx qa --symbol XAUUSD --asset-class fx
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

## 5. What you should see after each step

- after `download`: parquet files under `data/raw/{symbol}/`
- after `qa`: a markdown quality report under `data/raw/{symbol}/`
- after `pipeline`: parquet files under `data/ohlcv/`, `data/features/`, and `data/labels/`
- after `train`: artifacts under `outputs/models/{symbol}/{tf}/`
- after `evaluate`: HTML and PNG files under `outputs/reports/{symbol}/{tf}/`

## 6. Things to remember

- if training fails because files are missing, you usually skipped `mlfx pipeline`
- `outputs/models/{symbol}/{tf}/` stores model artifacts and metrics
- `outputs/reports/{symbol}/{tf}/` stores backtest reports
- `pixi run clean-generated` removes common caches and old outputs without touching `data/raw/`

## 7. What to read next

- [USAGE_GUIDE.md](USAGE_GUIDE.md): command-by-command usage
- [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md): how to read backtest outputs
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md): environment and data issues
- [GLOSSARY.md](GLOSSARY.md): common terms
