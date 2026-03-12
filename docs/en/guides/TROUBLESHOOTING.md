# MLFX - Troubleshooting

This guide covers common environment and operational issues for the `mlfx` workflow.

## 1. Quick Diagnostic Checklist

When a stage fails, check in this order:
1. Whether `pixi install` has been run
2. Whether the command is being executed through `pixi run`
3. Whether the current stage has its required input data
4. Whether the previous stage produced its expected output
5. Whether old caches or generated artifacts are polluting the workspace

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
- Confirm you are running commands with `pixi run`
- Try `pixi run python -c "import polars"` to verify the environment

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
- `bilstm`
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
- Start with a larger timeframe such as `1H`
- Process one symbol at a time
- Reduce the time range for initial experiments
- Prefer `scan_parquet()` over `read_parquet()` in custom scripts

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
- Contents of `outputs/models/{symbol}/{tf}/`
- Contents of `outputs/reports/{symbol}/{tf}/`

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
- Whether `data/labels/{symbol}/{tf}/` contains parquet files
- Whether the `--label` column exists
- Whether the `atr_14` column exists
- Whether `outputs/reports/{symbol}/{tf}/` is writable

Valid example:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

Notes:
- The CLI does not currently expose an `--outdir` option
- Reports are written to `outputs/reports/{symbol}/{tf}/` by default

## 11. Verify the repo after config or docs changes

Run:

```bash
pixi run verify
```

This is useful after:
- Changing Pixi configuration
- Updating docs or entrypoints
- Cleaning caches and outputs, then checking the main workflow still behaves correctly

## 12. Drift keeps alerting but you do not want to retrain

If drift appears at consistently low levels that do not warrant retraining, relax the thresholds:

```bash
pixi run mlfx drift --symbol XAUUSD --tf 1H --threshold-ks 0.2 --threshold-psi 0.3
```

Defaults: `--threshold-ks 0.1` and `--threshold-psi 0.2`.

## 13. Running multiple timeframes in one command

The `pipeline` subcommand accepts multiple `--tf` values in a single call:

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H 4H 1D
```

Timeframes are processed sequentially within the same invocation.

## 14. Where does `benchmark` save its report?

After completion, a JSON summary is saved automatically to:

```text
outputs/reports/{symbol}/{tf}/benchmark_{timestamp}.json
```

Example: `outputs/reports/XAUUSD/1H/benchmark_20260101_120000.json`
