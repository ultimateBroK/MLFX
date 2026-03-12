# MLFX Quickstart

This document is the **canonical fast-start guide** for running MLFX through the shortest practical path.

If you want to go from **no data** to **your first backtest result**, follow this file.

## When to read this file

Read `QUICKSTART.md` when you want to:

- Try the repository quickly
- Know the exact order of commands to run
- See what each step produces
- Have a short onboarding path before reading the more detailed docs

If you need deeper explanations:

- See [NOOB_GUIDE.md](NOOB_GUIDE.md) to understand **why** each step exists
- See [../guides/USAGE_GUIDE.md](../guides/USAGE_GUIDE.md) for full CLI parameter usage
- See [../guides/EVALUATION_GUIDE.md](../guides/EVALUATION_GUIDE.md) to understand how to read backtest outputs
- See [../guides/TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md) when something fails

---

## Minimum requirements

- `Pixi` installed
- You are in the root directory of the `ML_FX` repository
- Commands are run with `pixi run ...`

Install the environment:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

---

## Standard flow in 4 steps

Minimal flow:

```text
1. Download data      -> download
2. Prepare data       -> pipeline (OHLCV + features + labels)
3. Train a model      -> train
4. Evaluate results   -> evaluate (backtest + reports)
```

---

## Step 1 — Download data

Example for `XAUUSD`:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
```

### What this step does

- Downloads historical tick data from the data source
- Stores raw parquet files under `data/raw/{symbol}/`
- Stores download state so interrupted runs can resume

### Expected output

You should see files such as:

- `data/raw/XAUUSD/YYYY-MM.parquet`
- `data/raw/XAUUSD/completed_months.json`

### If you want to audit raw-data quality

You can also run the quality-check step:

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

This step is not required for the fastest onboarding path, but it is very useful if you suspect missing data or damaged months.

---

## Step 2 — Run the pipeline

Once raw data exists, run the pipeline to build OHLCV, features, and labels:

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
```

### What this step does

- Converts tick data into `OHLCV` bars
- Computes technical and context-aware features
- Generates labels such as `label_5`, `label_10`, and `label_20`

### Expected output

You should see intermediate data under:

- `data/ohlcv/XAUUSD/1H/`
- `data/features/XAUUSD/1H/`
- `data/labels/XAUUSD/1H/`

### Recommendation

If you are just getting started, use the `1H` timeframe because it is:

- Lighter than very small timeframes
- Easier to inspect
- Less resource-intensive

---

## Step 3 — Train a model

Example using the easiest default backend to start with, `mlf`:

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
```

### What this step does

- Loads the labeled dataset
- Selects the training backend
- Trains the model
- Stores artifacts and metadata

### Expected output

You should see outputs under:

- `outputs/models/XAUUSD/1H/`

### Recommended first-run parameters

- `--tf 1H`
- `--label label_10`
- `--backend mlf`

This is a good parameter set for a first trial run.

---

## Step 4 — Evaluate / Backtest

After training finishes, run evaluation:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

### What this step does

- Backtests the trained model
- If no suitable trained model is found, the workflow may fall back to using labels as a baseline
- Generates visual reports and summary metrics

### Expected output

You should see reports under:

- `outputs/reports/XAUUSD/1H/`

Typical files include:

- `*_candlestick.html`
- `*_equity.png`
- `*_heatmap.png`

The CLI will also print summary values such as:

- Total trades
- Win rate
- Profit factor
- Net profit
- Sharpe / Sortino / Calmar
- Ending equity

---

## Full quickstart command set

If you want to copy the entire minimal flow at once:

```bash
pixi install
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

If you want to be more careful with raw data:

```bash
pixi install
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx qa --symbol XAUUSD --asset-class fx
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

---

## What to read next after quickstart

### If you are completely new

Read next:

- [NOOB_GUIDE.md](NOOB_GUIDE.md)

### If you want command-by-command and flag-by-flag usage

Read:

- [../guides/USAGE_GUIDE.md](../guides/USAGE_GUIDE.md)

### If you want to understand what the backtest is measuring

Read:

- [../guides/EVALUATION_GUIDE.md](../guides/EVALUATION_GUIDE.md)

### If you want to understand the data, features, and system design

Read:

- [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
- [../reference/FEATURE_REFERENCE.md](../reference/FEATURE_REFERENCE.md)
- [../reference/GLOSSARY.md](../reference/GLOSSARY.md)

---

## Common issues during quickstart

### `pixi: command not found`

You have not installed `Pixi`, or your shell has not been reloaded yet.

### Training fails because files are missing

This usually means you did not run `download` or `pipeline` first.

### Evaluation does not generate reports

Check:

- Whether parquet files exist under `data/labels/{symbol}/{tf}/`
- Whether a model has been trained
- Whether `label_col` is correct

### Want to clean old outputs

Run:

```bash
pixi run clean-generated
```

This removes caches and generated outputs, but does not touch `data/raw/`.

---

## Canonical beginner flow

This file is the **canonical quickstart** for the English documentation.

Other documents should:

- Link back to this file when a fast-start workflow is needed
- Avoid repeating the full command chain here unless it is genuinely necessary

---

## One-line summary

If you just want to run MLFX for the first time, follow this order:

```text
download -> pipeline -> train -> evaluate
```
