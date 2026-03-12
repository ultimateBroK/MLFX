# MLFX - Current Status and Next Work

This document summarizes the main capabilities already available and the most sensible next steps.

Legend:
- `[x]` ready to use
- `[ ]` recommended next work

## 1. Current Capabilities

- [x] unified CLI `mlfx`
- [x] data downloader in `mlfx.ingestion`
- [x] QA, resampling, feature engineering, and labeling in `mlfx.pipeline`
- [x] trainable backends in `mlfx.training`
- [x] backtesting and reporting in `mlfx.evaluation`
- [x] runtime packaging through `mlfx`
- [x] Pixi-based developer and operator workflow

## 2. Available Backends

- [x] `mlf`
- [x] `lstm`
- [x] `bilstm`
- [x] `transformer`
- [x] `cnn_lstm`
- [x] `sgd`
- [x] `stats`
- [x] `neuralforecast`

## 3. Recommended Next Steps

- [x] `bilstm` exposed through CLI via `--backend bilstm`
- [x] unified benchmark flow added (`mlfx benchmark`)
- [x] end-to-end train/evaluate coverage added (`test_training_e2e.py`)
- [x] summary metrics export added (`metrics_log.jsonl`)

## 4. How to Prioritize

- if the goal is model comparison: use `mlfx benchmark --backends mlf bilstm lstm`; consider standardizing cross-backend metrics
- if the goal is operational reliability: expand test coverage with smaller fixture datasets
- if the goal is experimentation breadth: add new backend architectures (e.g. attention-based) or a live data adapter
- if the goal is production readiness: refactor the serving layer, add retry logic and circuit breakers
