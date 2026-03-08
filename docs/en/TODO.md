# MLFX - Current Status and Next Work

This document summarizes the main capabilities already available and the most sensible next steps.

Legend:
- `[x]` ready to use
- `[ ]` recommended next work

## 1. Current Capabilities

- [x] unified CLI `mlfx`
- [x] TUI `mlfx-tui`
- [x] data downloader in `mlfx.ingestion`
- [x] QA, resampling, feature engineering, and labeling in `mlfx.pipeline`
- [x] trainable backends in `mlfx.training`
- [x] backtesting and reporting in `mlfx.evaluation`
- [x] runtime packaging through `mlfx`
- [x] Pixi-based developer and operator workflow

## 2. Available Backends

- [x] `mlf`
- [x] `lstm`
- [x] `transformer`
- [x] `cnn_lstm`
- [x] `sgd`
- [x] `stats`
- [x] `neuralforecast`
- [x] `bilstm`

## 3. Recommended Next Steps

- [ ] add a unified benchmark flow to compare backends on the same dataset
- [ ] expand end-to-end train/evaluate coverage on smaller fixture datasets
- [ ] consider exporting summary metrics or report summaries for monitoring workflows

## 4. How to Prioritize

- if the goal is model comparison, prioritize a unified benchmark flow
- if the goal is operational reliability, prioritize end-to-end tests and summary metric exports
- if the goal is experimentation breadth, consider exposing `bilstm`
