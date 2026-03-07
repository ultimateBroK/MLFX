# ML_FX - Troubleshooting

This guide covers common environment and operational issues for the `mlfx` workflow.

## 1. Quick Diagnostic Checklist

When a stage fails, check in this order:
1. whether `pixi install` has been run
2. whether the command is being executed through `pixi run`
3. whether the current stage has its required input data
4. whether the previous stage produced its expected output
5. whether old caches or generated artifacts are polluting the workspace

## 2. `pixi: command not found`

Common causes:
- Pixi is not installed
- Pixi was installed but the terminal or IDE was not restarted

Fix:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

## 3. Missing package or import errors

Example:

```text
ModuleNotFoundError: No module named 'xgboost'
```

Fix:

```bash
pixi install
```

If it still fails:
- confirm you are running commands with `pixi run`
- try `pixi run python -c "import polars"` to verify the environment

## 4. Missing files during pipeline or training

If files are missing from `data/ohlcv/`, `data/features/`, or `data/labels/`, the workflow was usually run out of order.

Correct order:

```text
download -> qa -> pipeline -> train -> evaluate
```

Inspect these directories in order:
- `data/raw/{symbol}/`
- `data/ohlcv/{symbol}/{tf}/`
- `data/features/{symbol}/{tf}/`
- `data/labels/{symbol}/{tf}/`

## 5. Interrupted downloads

The downloader resumes from `completed_months.json`.

Rerun:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx
```

Force a full re-check:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --force
```

If the downloaded data looks suspicious, follow up with:

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

## 6. Invalid backend during training

The CLI currently supports:
- `mlf`
- `lstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

Check quickly with:

```bash
pixi run mlfx train --help
```

## 7. Out-of-memory or killed processes

Suggestions:
- start with a larger timeframe such as `1H`
- process one symbol at a time
- reduce the time range for initial experiments
- prefer `scan_parquet()` over `read_parquet()` in custom scripts

## 8. Clean caches and old outputs

Use the standard task:

```bash
pixi run clean-generated
```

This clears reproducible workspace state such as:
- `.cache/`
- `.pixi-cache/`
- `.pytest_cache/`
- `.ruff_cache/`
- `__pycache__/`
- `lightning_logs/`
- contents of `outputs/models/{symbol}/{tf}/`
- contents of `outputs/reports/{symbol}/{tf}/`

It does not remove `data/raw/`.

## 9. Rebuild intermediate datasets while keeping raw data

If you need to rebuild intermediate datasets:

```bash
rm -rf data/ohlcv/* data/features/* data/labels/*
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --pivot traditional --anchor daily --atr-mult 0.5
```

Use this only when you explicitly want a full intermediate rebuild.

## 10. Backtest does not generate reports

Check:
- whether `data/labels/{symbol}/{tf}/` contains parquet files
- whether the `--label` column exists
- whether the `atr_14` column exists
- whether `outputs/reports/{symbol}/{tf}/` is writable

Valid example:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

Notes:
- the CLI does not currently expose an `--outdir` option
- reports are written to `outputs/reports/{symbol}/{tf}/` by default

## 11. Verify the repo after config or docs changes

Run:

```bash
pixi run verify
```

This is useful after:
- changing Pixi configuration
- updating docs or entrypoints
- cleaning caches and outputs, then checking the main workflow still behaves correctly
