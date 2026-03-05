# ML_FX Evaluation Guide

This document explains how to read the Backtest results and performance analysis charts (Visualization) of the ML_FX project.

The Evaluation system (located in the `eval/` and `viz/` folders) provides a detailed look at how the Machine Learning model would perform if trading real markets. We do not use purely theoretical "accuracy" of Machine Learning; instead, we transform these into a **Walk-forward Simulation using R-multiples**.

---

## 1. Understanding Trading Metrics

The report will output a Metrics dictionary like this:
`Metrics: {'total_trades': 139, 'win_rate': 73.38, 'total_r': 118.0, 'max_drawdown_r': 3.0, 'profit_factor': 4.37}`

What the numbers mean:
*   **total_trades**: Total number of simulated trades.
*   **win_rate (%)**: The percentage of trades that hit Take Profit (TP) before Stop Loss (SL). However, win rate isn't everything if the R:R isn't good.
*   **total_r (Cumulative R-multiple)**: Instead of calculating in USD dollars, we calculate in R (Risk). If each trade risks 1% of your account (1R = 1%), a total profit of `118.0` means you made 118% profit on your account. This metric is independent of account size.
*   **max_drawdown_r**: The continuous maximum losing streak in R. A drawdown of `3.0` means your account's maximum decline at any given time was 3R (or 3% if risk is 1%) from an equity peak. This is the most crucial risk metric.
*   **profit_factor**: The ratio of *Gross Profit / Gross Loss*. Anything above 1.0 is profitable. A level of `2.0+` for Prop Firm evaluation rules is very high, a level of `4.37` as above is extremely ideal.

---

## 2. How to Read Performance Charts

The system generates 3 visual report files in the `reports/` directory.

### 2.1 Interactive Candlestick Chart (`candlestick.html`)
Open this file with your web browser. It leverages smooth Plotly interactiveness.
- **Candle Chart**: Traditional OHLCV.
- **RSI / Indicator**: Sub-indicators located in the bottom Panel.
- **Markers**:
  - 🔼 **Green Triangle**: Model executed a LONG trade.
  - 🔽 **Red/Pink Triangle**: Model executed a SHORT trade.
> *Tip*: Zoom heavily into areas with markers to examine the price action conditions behind the model's trades. Did it sell at an S/R peak? Did it buy when RSI was oversold?

### 2.2 Equity & Drawdown Curve (`*_equity.png`)
Open this image file for a long-term overview.
- **Top Panel (Yellow)**: The `Cumulative R` equity curve. An ideal curve rises linearly from the bottom left corner to the top right corner. If the line goes sideways for too long, the strategy has hit a Sideway cycle.
- **Bottom Panel (Red)**: Under-water curve (Drawdown). Shows the magnitude of decline compared to the nearest peak. If the red areas touch deep levels like `-10R` or lower, your strategy has high account blowout risks without tight capital management (like lowering Risk to 0.5%).

### 2.3 Session Performance Heatmap (`*_heatmap.png`)
This is a critical tool for refining strategy according to **ICT Killzones** style.
- **Y-Axis (Vertical)**: UTC hour frame (0 to 23).
- **X-Axis (Horizontal)**: Day of the week (Mon → Fri).
- **Colors**: Green (Profit), Red (Loss), Yellow/Light (Breakeven).
> *Usage*: If you notice that from 13:00 UTC to 16:00 UTC (Corresponding to the New York Killzone) shows thick green shades, filter the AI Bot to only trade during this timeframe and advise it to skip risky Asian/London sessions.

---

## 3. How to Run Simulation After Model Training

After the ML model has finished training (for example, KNN in `models/knn.py`) and generated predictions inside `predictions.parquet`. Or even directly from raw historical labels:

```bash
# Run Python CLI
cd /home/ultimatebrok/Downloads/ML_FX
pixi run python -c "
import polars as pl
from eval.backtest import simulate_trades, compute_metrics
from viz.charts import generate_full_report
from pathlib import Path

# Read data with Labels (or predictions)
df = pl.read_parquet('data/labels/XAUUSD/1H/2026-02.parquet')

# Configure R:R = 1.5 (TP 1.5R, SL 1.0R)
trades = simulate_trades(df, signal_col='label_5', tp_r=1.5, sl_r=1.0)
metrics = compute_metrics(trades)

print('Metrics:', metrics)

# Generate reports in /reports/ directory
generate_full_report('XAUUSD', '1H', df, trades, 'label_5_R15', Path('reports'))
"
```
