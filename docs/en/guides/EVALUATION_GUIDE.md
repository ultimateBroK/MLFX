# MLFX - Evaluation Guide

This guide explains how to run `mlfx evaluate`, how to read the evaluation metrics, and how to understand the artifacts generated after each run.

## Related Documentation

- [English Docs Hub](../README.md)
- [Quickstart](../getting-started/QUICKSTART.md)
- [Usage Guide](USAGE_GUIDE.md)
- [Feature Reference](../reference/FEATURE_REFERENCE.md)
- [Configuration Reference](../reference/CONFIG_REFERENCE.md)
- [Troubleshooting](TROUBLESHOOTING.md)

---

## 1. Input Data

The evaluation step reads all labeled data under:

```text
data/labels/{symbol}/{tf}/*.parquet
```

The minimum input dataset should include:

- a `timestamp` column
- price columns such as `open`, `high`, `low`, `close`
- the ATR column, by default `atr_14`
- the signal column passed through `--label`

Typical signal columns:

- `label_5`
- `label_10`
- `label_20`

---

## 2. Running a Backtest

```bash
pixi run mlfx evaluate \
  --symbol XAUUSD \
  --tf 1H \
  --label label_10 \
  --capital 10000 \
  --risk 1.0 \
  --commission 0.1 \
  --tp 1.5 \
  --sl 1.0 \
  --slippage 0.0
```

### 2.1 Trade Execution Rules

For each bar where a signal is present, the simulator will:

1. Open a position at the **next bar's open price**
2. Check subsequent bars for take-profit or stop-loss hits
3. If neither TP nor SL is reached within **10 bars** (`horizon_limit`), the trade is force-closed on the 10th bar

Take-profit and stop-loss are expressed in **R** units — multiples of the initial risk distance, derived from `atr_14`.

### 2.2 Label-to-Trade-Signal Mapping

Ordinal label values are mapped to trading signals as follows:

| Label | Signal | Meaning |
|---|---|---|
| `2` | LONG | Strong bullish |
| `1` | LONG | Bullish |
| `0` | Skip | No trade |
| `-1` | SHORT | Bearish |
| `-2` | SHORT | Strong bearish |

> **Note:** Labels `1` and `2` currently both produce the same LONG trade. The confidence level (`±2` versus `±1`) does not currently change position sizing in the implementation.

### 2.3 Argument Meaning

- `--symbol`: instrument identifier
- `--tf`: timeframe to evaluate
- `--label`: signal column used for entries
- `--capital`: initial capital, used to convert `R` into money
- `--risk`: percentage of capital risked per trade
- `--commission`: commission cost per trade
- `--tp`: take-profit in `R`
- `--sl`: stop-loss in `R`
- `--slippage`: simulated slippage
- `--use-labels`: backtest labels directly, skipping model predictions

---

## 3. Two Evaluation Modes: Model vs Labels

### 3.1 Default Mode

By default, `mlfx evaluate` uses the **best registered model** to generate predictions, then backtests those predictions.

If no suitable trained model exists, the workflow falls back to using the **labels** as a reference baseline.

### 3.2 Backtesting the Labels Directly

If you want to evaluate the original labels directly, add `--use-labels`:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --use-labels --tp 1.5 --sl 1.0
```

### 3.3 Backtesting a Model

If `--use-labels` is not passed, the system will try to:

1. Read `outputs/models/registry.json`
2. Select the best model based on the registered metric
3. Run inference over the full dataset
4. Backtest those model predictions

Example:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

### 3.4 Baseline Comparison Workflow

A sensible way to test whether the model actually adds value is:

```bash
# Step 1: Baseline — evaluate labels directly
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --use-labels --tp 1.5 --sl 1.0

# Step 2: Train a model
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf

# Step 3: Evaluate the model
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

You can then compare:

- equity curves
- profit factor
- Sharpe ratio
- net profit in `R`
- stability of results

---

## 4. Report Naming Convention

The runner builds `out_name` using:

```text
{label_col}_R{int(tp_r * 10)}
```

Then the reporting layer builds the full prefix as:

```text
{symbol}_{tf}_{out_name}
```

Example with:

- `symbol = XAUUSD`
- `tf = 1H`
- `label = label_10`
- `tp = 1.5`

produces the prefix:

```text
XAUUSD_1H_label_10_R15
```

---

## 5. Generated Artifacts

Each run typically generates 3 outputs in `outputs/reports/{symbol}/{tf}/`:

- `{prefix}_candlestick.html`
- `{prefix}_equity.png`
- `{prefix}_heatmap.png`

Example:

```text
outputs/reports/XAUUSD/1H/XAUUSD_1H_label_10_R15_candlestick.html
outputs/reports/XAUUSD/1H/XAUUSD_1H_label_10_R15_equity.png
outputs/reports/XAUUSD/1H/XAUUSD_1H_label_10_R15_heatmap.png
```

---

## 6. Important Metrics

The summary output usually includes:

- `Total Trades`
- `Win Rate (%)`
- `Profit Factor`
- `Net Profit (R)`
- `Net Profit ($)`
- `Sharpe Ratio`
- `Sortino Ratio`
- `Calmar Ratio`
- `Final Capital ($)`

### 6.1 Quick Interpretation

- `Total Trades`: total number of simulated trades
- `Win Rate (%)`: percentage of profitable trades; do not use it by itself
- `Profit Factor`: total gross profit divided by total gross loss; usually `> 1` is the minimum useful sign
- `Net Profit (R)`: normalized profit; very useful for fair comparison across configurations
- `Net Profit ($)`: profit converted to money using `capital` and `risk`
- `Sharpe Ratio`: average return relative to total volatility
- `Sortino Ratio`: similar to Sharpe, but penalizes downside volatility only
- `Calmar Ratio`: net profit divided by maximum drawdown
- `Final Capital ($)`: ending capital after all trade outcomes and costs are applied

### 6.2 Notes for Reading Metrics

- Do not use `Win Rate` alone to decide whether a strategy is good or bad
- `Profit Factor`, `Net Profit (R)`, and `Sharpe / Sortino` are often more useful when comparing configurations
- Very low trade counts can make metrics look attractive while still having weak statistical meaning
- When possible, always compare the model against the label baseline

---

## 7. How to Read Each Report Type

### 7.1 Candlestick HTML Report

Shows:

- price movement
- LONG / SHORT entry markers
- an RSI panel if the dataset includes `rsi_14`

Useful for:

- checking whether entries look sensible
- seeing whether signals cluster strangely in a short segment
- confirming whether the strategy enters at reasonable times

### 7.2 Equity Curve PNG

Shows:

- cumulative profit in `R`
- drawdown in the lower panel

Useful for:

- seeing the rhythm of capital growth
- comparing the “smoothness” of different configurations
- deciding whether profit comes from a stable series of trades or only a few lucky ones

### 7.3 Heatmap PNG

Shows average performance by:

- UTC hour
- weekday

Useful for:

- deciding whether time filters or session filters are worth testing
- identifying unusually strong or weak time windows

---

## 8. Common Failure Modes

Evaluation often fails or returns empty results when:

- there are no parquet files in `data/labels/{symbol}/{tf}/`
- the column passed through `--label` does not exist
- the `atr_14` column does not exist
- the dataset is too small, so there are effectively no meaningful trades
- the signal column never emits meaningful LONG or SHORT signals

### 8.1 Common Failure Signs

- the CLI does not print the summary metrics table
- no new files appear in `outputs/reports/{symbol}/{tf}/`
- the trade count is extremely low or `0`
- generated filenames do not match the expected prefix

---

## 9. Post-Run Checklist

After evaluation finishes, you should verify:

- whether the CLI printed summary metrics
- whether `outputs/reports/{symbol}/{tf}/` contains 3 new artifacts
- whether the filenames match the expected prefix
- whether the trade count is large enough to support interpretation, rather than being only a tiny sample
- if you are evaluating a model, whether that model actually exists in the registry

---

## 10. Minimal Python Example

```python
from pathlib import Path

import polars as pl

from mlfx.evaluation.backtest import compute_metrics, simulate_trades
from mlfx.evaluation.reporting import generate_full_report

df = pl.read_parquet("data/labels/XAUUSD/1H/2024-01.parquet")

trades = simulate_trades(
    df,
    signal_col="label_10",
    tp_r=1.5,
    sl_r=1.0,
    commission=0.1,
    slippage=0.0,
)

metrics = compute_metrics(
    trades,
    initial_capital=10000.0,
    risk_pct=1.0,
)

print(metrics)

generate_full_report(
    "XAUUSD",
    "1H",
    df,
    trades,
    "label_10_R15",
    Path("outputs/reports/XAUUSD/1H"),
)
```

---

## 11. Suggested Reading Order for Results

If you are just starting, read the outputs in this order:

1. `Total Trades`
2. `Profit Factor`
3. `Net Profit (R)`
4. `Sharpe Ratio`
5. the equity curve
6. the heatmap
7. the candlestick HTML report

Why this order:

- the top-level metrics tell you whether the configuration is worth inspecting further
- the equity curve shows the quality of capital progression
- the heatmap suggests time-based strategy improvements
- the candlestick report helps you visually inspect entry timing

---

## 12. See Also

- [Quickstart](../getting-started/QUICKSTART.md)
- [Usage Guide](USAGE_GUIDE.md)
- [Feature Reference](../reference/FEATURE_REFERENCE.md)
- [Configuration Reference](../reference/CONFIG_REFERENCE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
