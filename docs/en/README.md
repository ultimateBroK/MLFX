# ML_FX

ML_FX is a market data and price-direction research project built around tick ingestion, technical feature pipelines, multiple forecasting backends, and backtest reporting.

The repository currently covers:
- downloading tick data from Dukascopy
- resampling tick data into OHLCV bars
- building features from `ICT Killzone`, `Support/Resistance`, `Pivot Points`, and TA indicators
- generating `label_5`, `label_10`, and `label_20`
- training several model backends from the TUI or CLI
- running backtests and saving reports to `outputs/reports`

## Documentation Map

- English:
  - `docs/en/README.md`
  - `docs/en/NOOB_GUIDE.md`
  - `docs/en/USAGE_GUIDE.md`
  - `docs/en/EVALUATION_GUIDE.md`
  - `docs/en/TROUBLESHOOTING.md`
  - `docs/en/GLOSSARY.md`
  - `docs/en/TODO.md`
- Vietnamese:
  - `README.md`
  - `docs/NOOB_GUIDE.md`
  - `docs/USAGE_GUIDE.md`
  - `docs/EVALUATION_GUIDE.md`
  - `docs/TROUBLESHOOTING.md`
  - `docs/GLOSSARY.md`
  - `docs/TODO.md`

## Current Workflow

```text
download_data.py
  -> resample.py
  -> features.py
  -> labels.py
  -> train backend
  -> eval/run_eval.py
  -> outputs/reports
```

Main data pipeline:
- `pipeline/download_data.py`: writes raw tick data to `data/raw/{symbol}/`
- `pipeline/resample.py`: writes OHLCV data to `data/ohlcv/{symbol}/{tf}/`
- `pipeline/features.py`: writes feature datasets to `data/features/{symbol}/{tf}/`
- `pipeline/labels.py`: writes labeled datasets to `data/labels/{symbol}/{tf}/`

Training backends currently available in the TUI:
- `mlf` -> `models/ml_models.py`
- `lstm` -> `models/lstm.py`
- `transformer` -> `models/transformer.py`
- `cnn_lstm` -> `models/cnn_lstm.py`
- `sgd` -> `models/online_sgd.py`
- `stats` -> `models/stats_baseline.py`
- `neuralforecast` -> `models/neural_forecast.py`

The `agent/` directory is still a planned area and should not be treated as a complete production feature yet.

## Project Layout

```text
ML_FX/
├── indicators/        # ICT, S/R, and Pivot feature engineering
├── pipeline/          # Download, resample, features, labels, QA
├── models/            # Training backends in active use
├── eval/              # Backtest and evaluation entrypoints
├── viz/               # Chart and report generation
├── docs/              # Vietnamese documentation
├── docs/en/           # English documentation
├── data/              # Raw, OHLCV, features, labels
├── outputs/           # Saved models and generated reports
├── main.py            # TUI with Download, Pipeline, Train, Backtest tabs
├── config.toml        # Default values loaded by the TUI
└── pyproject.toml     # Package metadata and dependencies
```

## Quickstart

The practical way to run the project is through `Pixi`. `pyproject.toml` declares `requires-python >= 3.11`, while the Pixi environment is currently pinned to Python `3.13`.

```bash
pixi install
pixi run python main.py
```

TUI shortcuts:
- `q`: quit
- `d`: toggle dark/light mode

Main tabs:
- `Download Data`: fetch Dukascopy tick data
- `Pipeline`: run resample, features, and labels
- `Train Model`: choose a backend and train
- `Backtest`: run evaluation on labeled datasets

## CLI Example

```bash
pixi run python pipeline/download_data.py --symbol XAUUSD --start-year 2024
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H
pixi run python pipeline/features.py --symbol XAUUSD --tf 1H
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H
pixi run python models/ml_models.py --symbol XAUUSD --tf 1H --label label_10
pixi run python eval/run_eval.py --data data/labels/XAUUSD/1H/2024-01.parquet --symbol XAUUSD --tf 1H --label label_10
```

For full parameter reference and backend-specific commands, see `docs/en/USAGE_GUIDE.md`.

## Outputs

- Models: `outputs/models/{symbol}/{tf}/`
- Reports: `outputs/reports/`
- Intermediate datasets:
  - `data/raw/`
  - `data/ohlcv/`
  - `data/features/`
  - `data/labels/`

## Notes

- This file is the English landing page.
- Detailed operational guides live in `docs/en/`.
- The Vietnamese entry point is `README.md`.
