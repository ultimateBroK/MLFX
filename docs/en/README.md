# ML_FX

`ML_FX` is an MLOps-style research pipeline for market data. Its main stages are:
- downloading historical tick data from Dukascopy
- converting ticks into OHLCV bars across multiple timeframes
- generating technical and ICT-oriented features
- building training labels
- training, evaluating, and reporting model results

The repository is operated in a `Pixi-first` way. Day-to-day commands should be run through `pixi run`.

## Documentation Map

- English:
  - [README.md](README.md)
  - [NOOB_GUIDE.md](NOOB_GUIDE.md)
  - [USAGE_GUIDE.md](USAGE_GUIDE.md)
  - [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md)
  - [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
  - [GLOSSARY.md](GLOSSARY.md)
  - [TODO.md](TODO.md)
- Vietnamese:
  - [README.md](../../README.md)
  - [NOOB_GUIDE.md](../NOOB_GUIDE.md)
  - [USAGE_GUIDE.md](../USAGE_GUIDE.md)
  - [EVALUATION_GUIDE.md](../EVALUATION_GUIDE.md)
  - [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
  - [GLOSSARY.md](../GLOSSARY.md)
  - [TODO.md](../TODO.md)

## Environment Requirements

- Pixi installed locally
- Linux 64-bit is the platform currently pinned in `pyproject.toml`
- Python is managed by Pixi for the supported workflow; no separate `uv` or `venv` flow is required

Install the environment:

```bash
pixi install
```

## Official Entrypoints

- `pixi run mlfx` for the unified CLI
- `pixi run mlfx-tui` for the Textual TUI
- `pixi run test` to run the full test suite
- `pixi run verify` to run the focused smoke/contract checks
- `pixi run clean-generated` to clear common caches and generated artifacts

## Standard Operating Flow

```text
download
  -> qa
  -> pipeline
  -> train
  -> evaluate
  -> serve / batch-predict
  -> drift
```

What each stage does:
- `download`: fetch raw tick data
- `qa`: audit raw data for gaps or anomalies
- `pipeline`: build OHLCV, features, and labels
- `train`: fit the selected backend (with tracking + registry update)
- `evaluate`: run backtests and generate reports
- `serve`: start the FastAPI real-time inference endpoint
- `batch-predict`: run offline predictions and write parquet outputs
- `drift`: compare recent feature distributions vs reference statistics

## Quickstart

Launch the TUI:

```bash
pixi run mlfx-tui
```

Or run the CLI end to end:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx qa --symbol XAUUSD --asset-class fx
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

## Available Training Backends

- `mlf`
- `lstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

For full parameter references and operational examples, see [USAGE_GUIDE.md](USAGE_GUIDE.md).

## Project Layout

```text
ML_FX/
├── mlfx/
│   ├── app/           # CLI and TUI
│   ├── config/        # path policy and config loading
│   ├── ingestion/     # Dukascopy downloader
│   ├── pipeline/      # qa, resampling, feature engineering, labeling
│   ├── features/      # domain-specific feature modules
│   ├── training/      # backend implementations + training orchestration
│   ├── evaluation/    # backtest, reporting, evaluation runner
│   ├── tracking/      # experiment tracking adapters (MLflow/File)
│   ├── registry/      # model registry (JSON-backed)
│   ├── serving/       # FastAPI API + batch inference
│   └── monitoring/    # drift detection + structured logging
├── docs/
├── docs/en/
├── data/
├── outputs/
├── logs/
├── config.toml
└── pyproject.toml
```

## Main Artifacts

- `data/raw/{symbol}/`: raw tick data and download state files
- `data/ohlcv/{symbol}/{tf}/`: resampled parquet files
- `data/features/{symbol}/{tf}/`: feature-enriched datasets
- `data/labels/{symbol}/{tf}/`: labeled datasets
- `outputs/models/{symbol}/{tf}/`: model artifacts, metrics, and training metadata
- `outputs/reports/{symbol}/{tf}/`: HTML and PNG evaluation reports

## Cleanup Policy

- keep `data/raw/` if you want to rebuild the downstream pipeline without downloading again
- `data/ohlcv/`, `data/features/`, `data/labels/`, `outputs/`, `lightning_logs/`, `.pixi-cache/`, and `.cache/` are reproducible artifacts
- use `pixi run clean-generated` when you want to clean common generated state in the workspace

## Recommended Next Reading

- [NOOB_GUIDE.md](NOOB_GUIDE.md) if you are new to the repository
- [USAGE_GUIDE.md](USAGE_GUIDE.md) for command-by-command operation
- [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) for report structure and metric interpretation
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for environment or data issues
