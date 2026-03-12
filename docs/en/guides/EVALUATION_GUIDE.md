# MLFX - Evaluation Guide

This guide explains how to run `mlfx evaluate`, interpret its metrics, and understand the artifacts it generates.

## Related Documentation

- [English Docs Hub](../README.md)
- [Quickstart](../getting-started/QUICKSTART.md)
- [Usage Guide](USAGE_GUIDE.md)
- [Feature Reference](../reference/FEATURE_REFERENCE.md)
- [Configuration Reference](../reference/CONFIG_REFERENCE.md)
- [Troubleshooting](TROUBLESHOOTING.md)

## 1. Input Data

Evaluation reads all labeled parquet files under:

```text
data/labels/{symbol}/{tf}/*.parquet
```

The input dataset should include at least:
- `timestamp`
- OHLC columns such as `open`, `high`, `low`, `close`
- The default ATR column `atr_14`
- The signal column passed through `--label`

Typical signal columns:
- `label_5`
- `label_10`
- `label_20`

---

## 2. Run a Backtest

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

For each bar where a signal is present, the simulator:

1. Opens a position at the **next bar's open** price
2. Checks subsequent bars for TP or SL breach
3. If neither TP nor SL is hit within **10 bars** (`horizon_limit`), the trade is force-exited at the 10th bar

The TP and SL are expressed in **R** (multiples of the initial risk distance, derived from `atr_14`).

### 2.2 Label-to-Signal Mapping

Ordinal label values map to trading signals as follows:

| Label | Signal | Meaning |
|---|---|---|
| `2` | LONG | Strong bullish |
| `1` | LONG | Bullish |
| `0` | Skip | No trade |
| `-1` | SHORT | Bearish |
| `-2` | SHORT | Strong bearish |

> **Note**: Labels `1` and `2` both produce the same LONG trade; the confidence level (`±2` vs `±1`) does not affect position sizing in the current implementation.

### 2.3 Argument Summary

- `--symbol`: instrument identifier
- `--tf`: timeframe being evaluated
- `--label`: signal column used for entries
- `--capital`: initial capital for converting `R` into dollars
- `--risk`: percent of capital risked per trade
- `--commission`: commission cost per trade
- `--tp`: take-profit in `R`
- `--sl`: stop-loss in `R`
- `--slippage`: simulated slippage cost
- `--use-labels`: backtest raw labels instead of model predictions

---

## 3. Model Backtest Mode vs Label Backtest Mode

By default, `mlfx evaluate` uses the best registered model to generate predictions, then backtests those predictions.

If no suitable trained model is available, evaluation falls back to the raw labels.

### 3.1 Backtest Raw Labels

To backtest the labels directly, use `--use-labels`:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --use-labels --tp 1.5 --sl 1.0
```

This is useful as a baseline because it evaluates the signal quality of the labels themselves without model inference.

### 3.2 Backtest the Best Registered Model

Default behavior:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

The model backtest:
- Loads `outputs/models/registry.json`
- Selects the entry with the highest `best_cv_f1_macro`
- Runs inference over the full dataset
- Backtests the resulting predictions

### 3.3 Recommended Comparison Workflow

A practical way to assess model value:

```bash
# Step 1: Baseline — backtest the raw labels
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --use-labels --tp 1.5 --sl 1.0

# Step 2: Train a model
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf

# Step 3: Model backtest — use the trained model's predictions
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

Compare the equity curves and metrics from both runs. A model adds value if it improves trading-oriented metrics such as Profit Factor, Sharpe Ratio, and Net Profit (R) versus the baseline.

---

## 4. Report Naming Convention

The runner builds `out_name` as:

```text
{label_col}_R{int(tp_r * 10)}
```

The reporting layer then builds the full prefix as:

```text
{symbol}_{tf}_{out_name}
```

Example with:
- `symbol = XAUUSD`
- `tf = 1H`
- `label = label_10`
- `tp = 1.5`

produces:

```text
XAUUSD_1H_label_10_R15
```

---

## 5. Generated Artifacts

Each run typically writes three artifacts into `outputs/reports/{symbol}/{tf}/`:

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

## 6. Core Metrics

Typical summary output includes:

- `Total Trades`
- `Win Rate (%)`
- `Profit Factor`
- `Net Profit (R)`
- `Net Profit ($)`
- `Sharpe Ratio`
- `Sortino Ratio`
- `Calmar Ratio`
- `Final Capital ($)`

### Quick Interpretation

- `Total Trades`: number of simulated trades
- `Win Rate (%)`: percentage of profitable trades; do not use it in isolation
- `Profit Factor`: gross profit divided by gross loss; values above `1` are the minimum sign of profitability
- `Net Profit (R)`: normalized profit, useful for comparing configurations fairly
- `Net Profit ($)`: dollar-equivalent result after capital and risk assumptions
- `Sharpe Ratio`: mean return relative to overall volatility
- `Sortino Ratio`: similar to Sharpe, but penalizes downside volatility only
- `Calmar Ratio`: total net profit (in **R**) divided by maximum drawdown (in **R**); values above `1` are positive. Both numerator and denominator are expressed in R-units, not dollar amounts
- `Final Capital ($)`: ending capital after simulated trading costs and outcomes

---

## 7. Reading Each Report

### 7.1 Candlestick HTML

Shows:

- Price candles
- LONG/SHORT entry markers
- An RSI panel when `rsi_14` is present

Use it to:

- Visually inspect whether entries are sensible
- Spot clustered or suspicious signals

### 7.2 Equity Curve PNG

Shows:

- Cumulative profit in `R`
- Drawdown in the lower panel

Use it to:

- Judge smoothness of performance
- Compare multiple configurations beyond raw win rate

### 7.3 Heatmap PNG

Summarizes average performance by:

- UTC hour
- Weekday

Use it to decide whether session filters or time filters are worth testing.

---

## 8. Common Failure Modes

Evaluation often fails or returns empty results when:

- There are no parquet files in `data/labels/{symbol}/{tf}/`
- The `--label` column does not exist
- The `atr_14` column does not exist
- The dataset is too small to produce meaningful trades
- The signal column never emits `1` or `-1`

---

## 9. Post-Run Verification Checklist

After a run, confirm:

- The CLI printed summary metrics
- `outputs/reports/{symbol}/{tf}/` contains three new artifacts
- The generated filenames match the expected prefix
- Trade count is large enough to support interpretation

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
metrics = compute_metrics(trades, initial_capital=10000.0, risk_pct=1.0)
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

## 11. Practical Interpretation Tips

When comparing runs, avoid relying on a single metric.

A stronger evaluation workflow looks at:

- Profit Factor
- Net Profit (R)
- Sharpe Ratio
- Sortino Ratio
- Calmar Ratio
- Total Trades
- Trade clustering or timing patterns in the candlestick and heatmap reports

A model with a good training score but weak backtest metrics may still be operationally poor.

Similarly, a very high win rate with weak Profit Factor can still indicate a weak strategy.

---

## 12. See Also

- [Quickstart](../getting-started/QUICKSTART.md)
- [Usage Guide](USAGE_GUIDE.md)
- [Feature Reference](../reference/FEATURE_REFERENCE.md)
- [Configuration Reference](../reference/CONFIG_REFERENCE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [English Docs Hub](../README.md)
