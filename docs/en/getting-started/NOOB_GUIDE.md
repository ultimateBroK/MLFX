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
- Support/resistance
- Pivot points
- RSI, MACD, ATR, EMA

### Features -> Labels

Labels such as `label_5`, `label_10`, and `label_20` define the supervised target.

### Labels -> Train

The CLI currently exposes these backends:
- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

### Train -> Backtest

Backtesting consumes a label column as a signal source and generates:
- Candlestick HTML
- Equity curve PNG
- Heatmap PNG

## 4. Fastest way to start

For the canonical fast-start workflow, read:
- [QUICKSTART.md](QUICKSTART.md)

Use that document when you want the shortest runnable path from environment setup to first backtest output.

This guide stays focused on:
- What the project does
- Why stage order matters
- What artifacts you should expect after each stage

## 5. What you should see after each step

- After `download`: parquet files under `data/raw/{symbol}/`
- After `qa`: a markdown quality report under `data/raw/{symbol}/`
- After `pipeline`: parquet files under `data/ohlcv/`, `data/features/`, and `data/labels/`
- After `train`: artifacts under `outputs/models/{symbol}/{tf}/`
- After `evaluate`: HTML and PNG files under `outputs/reports/{symbol}/{tf}/`

## 6. Things to remember

- If training fails because files are missing, you usually skipped `mlfx pipeline`
- `outputs/models/{symbol}/{tf}/` stores model artifacts and metrics
- `outputs/reports/{symbol}/{tf}/` stores backtest reports
- `pixi run clean-generated` removes common caches and old outputs without touching `data/raw/`

## 7. What to read next

- [QUICKSTART.md](QUICKSTART.md): canonical fast-start workflow
- [../guides/USAGE_GUIDE.md](../guides/USAGE_GUIDE.md): command-by-command usage
- [../guides/EVALUATION_GUIDE.md](../guides/EVALUATION_GUIDE.md): how to read backtest outputs
- [../guides/TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md): environment and data issues
- [../reference/GLOSSARY.md](../reference/GLOSSARY.md): common terms
