# MLFX - Beginner Guide

If you are new to this repository, read this file first.  
The goal of this guide is to help you understand:

- What this project is for
- How data moves through the system
- Why the stages must run in the correct order
- What outputs you should expect after each step
- How to get started safely with `Pixi`

MLFX is a **research, training, and model evaluation environment** for market data. It is **not** a finished live-trading bot.

---

## 1. What this project is for

MLFX is a machine learning pipeline for market data. Its basic workflow is:

- Download historical tick data
- Convert that data into OHLCV
- Build technical and context-aware features
- Generate labels for forecasting tasks
- Train models
- Run evaluation and export reports

In short: MLFX helps you go from **raw price data** to **comparable backtest results** in one consistent workflow.

---

## 2. High-level system flow

```text
1. Download data      → download
2. Prepare data       → pipeline
3. Train model        → train
4. Evaluate results   → evaluate
```

In simpler terms:

- `download` fetches historical price data
- `pipeline` builds candles, features, and labels
- `train` trains a model
- `evaluate` runs a backtest and generates reports

After `evaluate`, the CLI prints summary metrics and paths to the generated report files.

By default:

- If a matching trained model exists, the system evaluates the **model**
- If no matching model exists, the system can evaluate the **labels** as an initial reference baseline

The corresponding code areas live in:

- `mlfx.ingestion`
- `mlfx.pipeline`
- `mlfx.training`
- `mlfx.evaluation`

---

## 3. Why the order matters

Many new users want to jump straight to training. That usually leads to errors or misleading results. Each MLFX stage exists for a clear reason.

### From tick data to quality checks

After downloading, you should inspect raw data to detect:

- Data gaps
- Damaged months
- Abnormal records
- Incomplete downloads

This helps prevent training on broken or misleading inputs without realizing it.

### From tick data to OHLCV

Tick data is extremely dense and usually not practical to use directly for most models.  
So the system resamples it into candle bars such as:

- `1m`
- `5m`
- `15m`
- `1H`

OHLCV is more compact, easier to reason about, and better suited for later stages.

### From OHLCV to features

Once candle bars exist, the system adds context through features such as:

- RSI
- MACD
- ATR
- EMA
- Pivot points
- Support/resistance zones
- Session features
- ICT-style contextual features

In other words, instead of giving the model only raw price structure, you give it price data **plus processed context**.

### From features to labels

Columns such as:

- `label_5`
- `label_10`
- `label_20`

turn the dataset into a supervised learning problem.  
Without labels, the model does not know what target it is supposed to learn.

### From labels to training

Only after the data is ready should you move to training. The CLI currently supports these backends:

- `mlf`
- `lstm`
- `sgd`
- `stats`

Each backend is a different way to learn from the same prepared dataset.

### From training to evaluation

The `evaluate` step does more than just print a few numbers. It is where you check:

- Whether the model produces usable signals
- How the backtest behaves
- What the simulated profit looks like
- Whether the risk and stability are acceptable

In short: If you have not evaluated the result, you cannot conclude that the model is useful.

---

## 4. The right way to get started

If you want the shortest runnable workflow, read:

- [QUICKSTART.md](QUICKSTART.md)

That file is the **canonical fast-start guide**.  
This file is the **beginner guide**, which means it focuses on helping you understand:

- What the project does
- What the stage order means
- Why each step matters
- What you should inspect after each stage

If you are new to the repository, the most sensible reading order is:

1. Read this file
2. Run the workflow from `QUICKSTART.md`
3. Only then move on to the more detailed usage docs

---

## 5. What you should see after each step

When you are learning a new repository, the best way to avoid confusion is to check for “success signals” after each stage.

### After `download`
You should see:

- Parquet files under `data/raw/{symbol}/`
- `completed_months.json`

Example:
- `data/raw/XAUUSD/YYYY-MM.parquet`
- `data/raw/XAUUSD/completed_months.json`

### After `qa`
You should see:

- A data quality report under `data/raw/{symbol}/`

### After `pipeline`
You should see data generated in these areas:

- `data/ohlcv/`
- `data/features/`
- `data/labels/`

This confirms that the raw data has passed through the required transformation stages.

### After `train`
You should see model artifacts under:

- `outputs/models/{symbol}/{tf}/{label}/`

This location will typically contain:
- A saved model for the selected label
- Metadata
- Training metrics

### After `evaluate`
You should see reports under:

- `outputs/reports/{symbol}/{tf}/{label}/labels/R{tp*10}/`
- `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/`

Typical outputs include:
- Candlestick HTML report
- Equity curve chart
- Session or time-based heatmap

---

## 6. Important things to remember

When you first start using MLFX, keep these simple rules in mind:

- If training fails because files are missing, the usual reason is that you **did not run `pipeline` yet**
- If evaluation has nothing useful to read, check whether you already have:
  - Labeled data
  - A trained model
  - The correct label column name
- `outputs/models/{symbol}/{tf}/{label}/` stores model artifacts for a specific label
- `outputs/reports/{symbol}/{tf}/{label}/...` stores evaluation reports grouped by label, mode, and risk
- `pixi run clean-generated` removes caches and generated outputs **without touching raw data**

---

## 7. When should you use the quality-check step?

Many new users ask: “Do I really need to run `qa` immediately?”

The answer is:

- **not strictly required** if you are only doing a quick first trial
- **recommended** when:
  - You suspect the raw data may be broken
  - You want to validate data reliability before training
  - You are doing serious research and want to reduce input-side risk early

So for new users:

- You may skip `qa` during the very first run
- But you should know the stage exists and use it when needed

---

## 8. A comfortable learning path through the repo

If you do not want to feel overwhelmed, follow this order:

### Step 1 — Understand the big idea
Read this file to understand:
- What the project does
- How data moves
- Why stage order matters

### Step 2 — Run one complete workflow
Read and follow:
- [QUICKSTART.md](QUICKSTART.md)

### Step 3 — Learn CLI operation in detail
Read:
- [../guides/USAGE_GUIDE.md](../guides/USAGE_GUIDE.md)

### Step 4 — Learn how to read results
Read:
- [../guides/EVALUATION_GUIDE.md](../guides/EVALUATION_GUIDE.md)

### Step 5 — When something goes wrong
Read:
- [../guides/TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md)

### Step 6 — When you want deeper understanding
Read:
- [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
- [../reference/GLOSSARY.md](../reference/GLOSSARY.md)
- [../reference/FEATURE_REFERENCE.md](../reference/FEATURE_REFERENCE.md)

---

## 9. Short summary

If you only remember one thing, remember this:

MLFX is not a place where you run a random command and expect correct results immediately.  
It is an ordered workflow, and each stage prepares the next one.

The safest default order is:

```text
download → pipeline → train → evaluate
```

If you want to be more careful with raw data, insert this step:

```text
download → qa → pipeline → train → evaluate
```

---

## 10. What to read next

- [QUICKSTART.md](QUICKSTART.md) — fastest runnable workflow
- [../guides/USAGE_GUIDE.md](../guides/USAGE_GUIDE.md) — command-by-command usage
- [../guides/EVALUATION_GUIDE.md](../guides/EVALUATION_GUIDE.md) — how to read backtest results
- [../guides/TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md) — environment and data issue handling
- [../reference/GLOSSARY.md](../reference/GLOSSARY.md) — common terms
- [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) — system architecture
