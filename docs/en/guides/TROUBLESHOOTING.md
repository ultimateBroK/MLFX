# MLFX - Troubleshooting

This guide collects the most common problems you may hit while installing the environment or running stages in the `mlfx` workflow.

If a stage fails, do not patch random pieces blindly. Check things in the right order: environment → input data → output from the previous stage → caches / stale generated artifacts.

---

## 1. Quick checklist

When a stage fails, check these in order:

1. Did you run `pixi install`?
2. Are you executing the command through `pixi run`?
3. Does the current stage's required input data exist?
4. Did the previous stage write its outputs to the expected directory?
5. Is the workspace being polluted by old caches or stale generated outputs?

This is the fastest way to rule out the most common causes.

---

## 2. `pixi: command not found`

### Common causes

- `Pixi` is not installed
- `Pixi` was installed, but the terminal or IDE was not restarted
- Your shell environment has not reloaded the updated PATH

### Fix

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

If it still does not work:

- Close and reopen the terminal
- Restart the IDE
- Confirm that your current shell session has reloaded its configuration

---

## 3. Missing package or import errors

Example error:

```text
ModuleNotFoundError: No module named 'xgboost'
```

### Common causes

- The environment was not installed completely
- You are using the system Python instead of the project-managed environment
- You ran the command directly instead of going through `pixi run`

### Fix

```bash
pixi install
```

Then verify the environment with a small check:

```bash
pixi run python -c "import polars; print('ok')"
```

If that works, the base environment is available.

---

## 4. Missing files during `pipeline` or `train`

If files are missing from directories such as:

- `data/ohlcv/`
- `data/features/`
- `data/labels/`

the most common reason is that **the workflow was run in the wrong order**.

### Correct order

```text
download -> qa -> pipeline -> train -> evaluate
```

### What to inspect

Check these directories in order:

- `data/raw/{symbol}/`
- `data/ohlcv/{symbol}/{tf}/`
- `data/features/{symbol}/{tf}/`
- `data/labels/{symbol}/{tf}/`

If one link in the chain is missing data, later stages will usually fail as a consequence.

---

## 5. Interrupted downloads

The downloader uses `completed_months.json` so it can resume unfinished work.

### Resume normally

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx
```

### Force a full re-check

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --force
```

### If the downloaded data looks suspicious

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

This helps detect data gaps, damaged months, or abnormal records.

---

## 6. Invalid backend during training

### Backends currently supported

- `mlf`
- `lstm`
- `sgd`
- `stats`

### Quick check

```bash
pixi run mlfx train --help
```

If the backend name you pass is not in the supported list, the CLI will fail.

---

## 7. Out-of-memory or killed processes

### Common signs

- The process stops unexpectedly
- The OS reports low memory
- `pipeline` or `train` gets terminated abruptly

### Ways to reduce load

- Start with a larger timeframe such as `1H`
- Process one symbol at a time
- Reduce the date range for initial experiments
- In custom scripts, prefer `scan_parquet()` for larger datasets
- Avoid running multiple heavy stages at the same time on a weaker machine

### Practical recommendation

If you are only doing a first trial run, use:

- `symbol = XAUUSD`
- `tf = 1H`
- `backend = mlf`

That combination is usually lighter and more stable than the deep learning backends.

---

## 8. Clean caches and stale outputs

Use the standard task:

```bash
pixi run clean-generated
```

### What it clears

Common reproducible workspace state, such as:

- `.cache/`
- `.pixi-cache/`
- `.pytest_cache/`
- `.ruff_cache/`
- `__pycache__/`
- `lightning_logs/`
- Contents of `outputs/models/{symbol}/{tf}/{label}/`
- Contents of `outputs/reports/{symbol}/{tf}/{label}/`

### What it does not remove

- `data/raw/`

This matters because raw data is usually the most expensive part to re-download.

---

## 9. Rebuild intermediate datasets while keeping raw data

If you need to rebuild all intermediate datasets while preserving `data/raw/`, you can do:

```bash
rm -rf data/ohlcv/* data/features/* data/labels/*
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --pivot traditional --anchor daily --atr-mult 0.5
```

### When to use this

Only use it when you are sure you want to regenerate all of:

- OHLCV
- Features
- Labels

### When not to use this

Do not use it if you are only trying to inspect a small failure and do not yet know the cause. Deleting intermediate data can remove useful evidence that would help you diagnose the issue.

---

## 10. Backtest does not generate reports

### Check these first

- Does `data/labels/{symbol}/{tf}/` contain parquet files?
- Does the column passed via `--label` exist?
- Does the `atr_14` column exist?
- Is `outputs/reports/{symbol}/{tf}/{label}/` writable?

### Valid example

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

### Important notes

- The CLI currently does **not** expose an `--outdir` flag
- Reports are written by default to:
  - baseline labels: `outputs/reports/{symbol}/{tf}/{label}/labels/R{tp*10}/`
  - model backtests: `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/`

If the command completes but no new files appear, inspect the labeled data and signal column first.

---

## 11. Need to verify the repo is still in a healthy state

Run:

```bash
pixi run verify
```

This is useful when you have just:

- Changed Pixi configuration
- Edited documentation or CLI entrypoints
- Cleaned caches or stale outputs
- Want to confirm that the main workflow still works

---

## 12. Drift keeps alerting but you do not want to change the model yet

If drift warnings appear at low levels and do not yet justify action, you can relax the thresholds:

```bash
pixi run mlfx drift --symbol XAUUSD --tf 1H --threshold-ks 0.2 --threshold-psi 0.3
```

### Default thresholds

- `--threshold-ks 0.1`
- `--threshold-psi 0.2`

### When relaxing thresholds makes sense

- When you only want to reduce alert noise
- When the data moves naturally but has not clearly degraded quality
- When you are still monitoring experiments rather than operating in a production-like environment

Do not relax thresholds just to “make alerts disappear” if you do not understand the source of the drift.

---

## 13. Running multiple timeframes at once

The `pipeline` command supports multiple `--tf` values in one call:

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H 4H 1D
```

Timeframes are processed sequentially within that invocation.

### When to use this

- When you want to generate multiple datasets at once
- When you are preparing for multi-timeframe benchmarking

### When not to use this

- When the machine is weak
- When you are still debugging the pipeline on a single timeframe

During troubleshooting, running one timeframe at a time is usually easier to reason about.

---

## 14. Where `benchmark` saves its report

After `benchmark` finishes, the JSON summary is written automatically to:

```text
outputs/reports/{symbol}/{tf}/{label}/benchmark/benchmark_{timestamp}.json
```

Example:

```text
outputs/reports/XAUUSD/1H/label_10/benchmark/benchmark_20260101_120000.json
```

If you do not see that file, check:

- Whether the benchmark command actually completed
- Whether `outputs/reports/{symbol}/{tf}/{label}/benchmark/` exists
- Whether there was a write failure or permission issue

---

## 15. When to suspect the problem is in the data, not the code

Suspect the data when you see signs such as:

- Missing months in raw data
- Trade count equals `0` after backtesting
- A label column exists but never produces meaningful entry signals
- Reports are generated but the results look extremely abnormal
- Multiple stages succeed, but the final metrics look unreasonable

In those cases, go back and inspect:

1. `download`
2. `qa`
3. `pipeline`

Do not jump to the conclusion that the model is the primary problem.

---

## 16. When to suspect configuration instead of code

Suspect configuration when:

- Commands run, but the results are not what you expected
- The wrong `label` is being used
- The wrong `tf` is being used
- The wrong `symbol` is being used
- The selected backend does not match your goal
- `tp` / `sl` thresholds are highly unusual
- `config.toml` values differ from what you think the workflow is using

The safest way to debug this is to pass the critical values explicitly on the command line.

---

## 17. Safest debugging path for new users

If you are not sure where the problem is, go back to the simplest path:

```bash
pixi install
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --use-labels --tp 1.5 --sl 1.0
```

Why this path is safe:

- It does not depend on training yet
- It makes it easier to separate data issues from model issues
- It still gives you a first concrete result to inspect

Once this works, add `train` afterward.

---

## 18. What to read next

- [Quickstart](../getting-started/QUICKSTART.md) — fastest runnable path
- [Beginner Guide](../getting-started/NOOB_GUIDE.md) — overall workflow understanding
- [Usage Guide](USAGE_GUIDE.md) — command-by-command operation
- [Evaluation Guide](EVALUATION_GUIDE.md) — how to read evaluation outputs
- [Configuration Reference](../reference/CONFIG_REFERENCE.md) — configuration lookup
- [Architecture](../architecture/ARCHITECTURE.md) — system design
