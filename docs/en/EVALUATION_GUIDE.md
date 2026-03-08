# MLFX - Evaluation Guide

This guide explains how to run `mlfx evaluate`, interpret its metrics, and understand the artifacts it generates.

## 1. Input Data

Evaluation reads all labeled parquet files under:

```text
data/labels/{symbol}/{tf}/*.parquet
```

The input dataset should include at least:
- `timestamp`
- OHLC columns such as `open`, `high`, `low`, `close`
- the default ATR column `atr_14`
- the signal column passed through `--label`

Typical signal columns:
- `label_5`
- `label_10`
- `label_20`

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

Argument summary:
- `--symbol`: instrument identifier
- `--tf`: timeframe being evaluated
- `--label`: signal column used for entries
- `--capital`: initial capital for converting `R` into dollars
- `--risk`: percent of capital risked per trade
- `--commission`: commission cost per trade
- `--tp`: take-profit in `R`
- `--sl`: stop-loss in `R`
- `--slippage`: simulated slippage cost

## 3. Report Naming Convention

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

## 4. Generated Artifacts

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

## 5. Core Metrics

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

Quick interpretation:
- `Total Trades`: number of simulated trades
- `Win Rate (%)`: percentage of profitable trades; do not use it in isolation
- `Profit Factor`: gross profit divided by gross loss; values above `1` are the minimum sign of profitability
- `Net Profit (R)`: normalized profit, useful for comparing configurations fairly
- `Net Profit ($)`: dollar-equivalent result after capital and risk assumptions
- `Sharpe Ratio`: mean return relative to overall volatility
- `Sortino Ratio`: similar to Sharpe, but penalizes downside volatility only
- `Calmar Ratio`: total return relative to maximum drawdown
- `Final Capital ($)`: ending capital after simulated trading costs and outcomes

## 6. Reading Each Report

### 6.1 Candlestick HTML

Shows:
- price candles
- LONG/SHORT entry markers
- an RSI panel when `rsi_14` is present

Use it to:
- visually inspect whether entries are sensible
- spot clustered or suspicious signals

### 6.2 Equity Curve PNG

Shows:
- cumulative profit in `R`
- drawdown in the lower panel

Use it to:
- judge smoothness of performance
- compare multiple configurations beyond raw win rate

### 6.3 Heatmap PNG

Summarizes average performance by:
- UTC hour
- weekday

Use it to decide whether session filters or time filters are worth testing.

## 7. Common Failure Modes

Evaluation often fails or returns empty results when:
- there are no parquet files in `data/labels/{symbol}/{tf}/`
- the `--label` column does not exist
- the `atr_14` column does not exist
- the dataset is too small to produce meaningful trades
- the signal column never emits `1` or `-1`

## 8. Post-Run Verification Checklist

After a run, confirm:
- the CLI printed summary metrics
- `outputs/reports/{symbol}/{tf}/` contains three new artifacts
- the generated filenames match the expected prefix
- trade count is large enough to support interpretation

## 9. Minimal Python Example

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
generate_full_report("XAUUSD", "1H", df, trades, "label_10_R15", Path("outputs/reports/XAUUSD/1H"))
```
