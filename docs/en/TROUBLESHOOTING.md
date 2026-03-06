# ML_FX - Troubleshooting

This guide covers the most common environment and pipeline issues.

## 1. `pixi: command not found`

Common causes:
- Pixi is not installed
- Pixi was installed but the terminal was not restarted

Fix:
1. install Pixi using `USAGE_GUIDE.md`
2. restart your terminal or IDE
3. run:

```bash
pixi install
```

## 2. Missing package errors

Example:

```text
ModuleNotFoundError: No module named 'xgboost'
```

Cause:
- the environment has not been fully synchronized

Fix:

```bash
pixi install
```

## 3. Missing files during feature generation, labeling, or training

Examples:
- files missing in `data/ohlcv/`
- files missing in `data/features/`
- files missing in `data/labels/`

Cause:
- the pipeline was run out of order

Correct order:

```text
download -> qa -> resample -> features -> labels -> train -> backtest
```

If training fails, inspect these directories in order:
- `data/raw/{symbol}/`
- `data/ohlcv/{symbol}/{tf}/`
- `data/features/{symbol}/{tf}/`
- `data/labels/{symbol}/{tf}/`

## 4. Out-of-memory or killed processes

Cause:
- too much tick data is being loaded at once

Fix:
- start with a larger timeframe such as `1H`
- process one symbol at a time
- if you write custom analysis scripts, prefer `scan_parquet()` over `read_parquet()` for large datasets

## 5. Interrupted downloads

`pipeline/download_data.py` can resume using `completed_months.json`.

In most cases, simply rerun:

```bash
pixi run python pipeline/download_data.py --symbol XAUUSD --asset-class fx
```

If you want to force a full re-check of completed months:

```bash
pixi run python pipeline/download_data.py --symbol XAUUSD --asset-class fx --force-repair
```

## 6. Clean reset of generated data

If you want to regenerate OHLCV, features, or labels while keeping raw data:

```bash
rm -rf data/ohlcv/* data/features/* data/labels/*
```

Then rerun:

```bash
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H
pixi run python pipeline/features.py --symbol XAUUSD --tf 1H
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H
```

## 7. Backtest does not generate reports

Check:
- whether the path passed to `--data` exists
- whether the `--label` column exists in the parquet file
- whether the output directory is writable

Example:

```bash
pixi run python eval/run_eval.py \
  --data data/labels/XAUUSD/1H/2024-01.parquet \
  --symbol XAUUSD \
  --tf 1H \
  --label label_10 \
  --outdir outputs/reports
```
