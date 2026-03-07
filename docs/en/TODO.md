# ML_FX - Current Status and Open Work

This document summarizes the repository as it exists today rather than preserving older planning notes.

Legend:
- `[x]` implemented in the repo
- `[/]` partial or placeholder
- `[ ]` not implemented

## 1. Data Collection and QA

- [x] [pipeline/download_data.py](../../pipeline/download_data.py)
  - [x] downloads Dukascopy tick data
  - [x] supports `fx` and `crypto`
  - [x] stores progress in `completed_months.json`
  - [x] supports resume and repair flows
- [x] [pipeline/qa_data.py](../../pipeline/qa_data.py)
  - [x] checks data gaps
  - [x] audits invalid values
  - [x] writes a Markdown QA report

## 2. Data Pipeline

- [x] [pipeline/resample.py](../../pipeline/resample.py)
  - [x] converts tick data into OHLCV
  - [x] supports `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`
- [x] [pipeline/features.py](../../pipeline/features.py)
  - [x] `ICT Killzone` features
  - [x] `Support/Resistance` features
  - [x] `Pivot Points` features
  - [x] common TA features
- [x] [pipeline/labels.py](../../pipeline/labels.py)
  - [x] generates `label_5`, `label_10`, `label_20`
  - [x] uses ATR-based thresholds

## 3. Available Training Backends

- [x] [models/ml_models.py](../../models/ml_models.py)
- [x] [models/lstm.py](../../models/lstm.py)
- [x] [models/transformer.py](../../models/transformer.py)
- [x] [models/cnn_lstm.py](../../models/cnn_lstm.py)
- [x] [models/online_sgd.py](../../models/online_sgd.py)
- [x] [models/stats_baseline.py](../../models/stats_baseline.py)
- [x] [models/neural_forecast.py](../../models/neural_forecast.py)
- [x] [models/bilstm.py](../../models/bilstm.py)

Notes:
- the TUI currently exposes: `mlf`, `lstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`
- [models/bilstm.py](../../models/bilstm.py) exists in the repository but is not currently listed in the TUI backend selector

## 4. Evaluation and Reporting

- [x] [eval/backtest.py](../../eval/backtest.py)
- [x] [eval/run_eval.py](../../eval/run_eval.py)
- [x] [viz/charts.py](../../viz/charts.py)
  - [x] candlestick HTML report
  - [x] equity curve PNG
  - [x] heatmap PNG

Default output locations:
- `outputs/models/`
- `outputs/reports/`

## 5. Operational UI

- [x] [main.py](../../main.py)
  - [x] `Download Data` tab
  - [x] `Pipeline` tab
  - [x] `Train Model` tab
  - [x] `Backtest` tab
- [x] [config.toml](../../config.toml)
  - [x] provides default values for the TUI

## 6. Agent Status

- `agent/` is still a future-facing area
- [pyproject.toml](../../pyproject.toml) still packages `agent`
- current practical state:
  - [/] directory exists
  - [ ] no complete implementation exposed as a main repo feature yet

## 7. Reasonable Next Work

- [ ] align `config.toml` comments with the backends actually exposed in the TUI
- [ ] decide whether `bilstm.py` should be promoted into the TUI
- [ ] clarify the evaluation story between labeled-data backtests and real model prediction outputs
- [ ] document the intended scope of `agent/` before expanding README claims again
- [ ] add benchmark documentation or scripts to compare multiple backends on the same dataset
