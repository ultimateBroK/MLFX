# ML_FX — ICT-Based Price Prediction System

> Building a Machine Learning model to predict price movements for **Forex**, **Commodities**, and **Crypto** based on technical signals from **ICT Killzone**, **Support/Resistance**, and **Pivot Points**.

---

## 🌎 Languages
- **English**: You are reading the English documentation. All English docs are located in `/docs/en/`.
- **Vietnamese (Tiếng Việt)**: Vui lòng xem bản dịch tiếng Việt tại `/README.md` và trong thư mục `/docs/`.

---

## Overview

ML_FX is an end-to-end financial price analysis and prediction system, combining:
- **Polars** (replacing Pandas) for high-speed tick data processing
- **Machine Learning** to predict price direction
- **AI Agent (Agno)** to generate automated trading signals

### Supported Markets

| Asset Class     | Examples                                  |
| --------------- | ----------------------------------------- |
| **Forex**       | EURUSD, GBPUSD, USDJPY, XAUUSD            |
| **Commodities** | Gold (XAU), Silver (XAG), Crude Oil (WTI) |
| **Crypto**      | BTC, ETH, SOL                             |

---

## Project Structure
> 📚 **Documentation for Beginners**: If you want to run the Bot yourself or don't understand Machine Learning/Trading. Please read:
> - [System Anatomy & Bot Principles](docs/NOOB_GUIDE.md)
> - [Setup Guide & Command Cheatsheet](docs/USAGE_GUIDE.md)
> - [Glossary](docs/GLOSSARY.md)
> - [Troubleshooting](docs/TROUBLESHOOTING.md)

```text
ML_FX/
│
├── indicators/                          # Phase 2 ✅ — Feature Engineering
│   ├── __init__.py                     # Public API: add_killzone_features, add_sr_pp_features
│   ├── killzone.py                     # ICT Killzone: 5 sessions, pivot H/L, DWM levels, avg range
│   └── sr_pp.py                        # S/R patterns (r/r2/s/s2), role reversal, 6 Pivot Point types
│
├── pipeline/                           # Phase 1 & 3 ✅ — ETL Pipeline
│   ├── download_data.py                # Script to fetch Universal Dukascopy data (FX, Crypto)
│   ├── qa_data.py                      # Quality assurance script to check tick data missing hours
│   ├── resample.py                     # Tick → OHLCV (1m/5m/15m/30m/1H/2H/4H/1D), mid price
│   ├── features.py                     # killzone + sr_pp + TA-Lib + Order Blocks + FVG
│   └── labels.py                       # LONG/SHORT/NEUTRAL labeling (ATR-based threshold)
│
├── models/                             # Phase 4 ✅ — ML Models
│   ├── knn.py                          # KNN baseline — TimeSeriesSplit CV
│   ├── gradient_boost.py               # XGBoost/LightGBM — SHAP + Optuna tuning
│   └── lstm.py                         # LSTM (PyTorch) — sequence 50–200 bars
│
├── eval/                               # Phase 5 ✅ — Evaluation
│   ├── backtest.py                     # Walk-forward, Sharpe, drawdown, win rate, R:R
│   └── run_eval.py                     # Script to aggregate reports and run backtest
│
├── viz/                                # Phase 5 ✅ — Visualization
│   └── charts.py                       # Plotly candles + S/R overlay, Matplotlib equity curve
│
├── agent/                              # Phase 6 📋 — AI Agent (Agno 6-step)
│   ├── agent.py                        # create_agent(): LMStudio + ReasoningTools + DB
│   ├── toolkit.py                      # FXToolkit(Toolkit): get_killzone_status/levels/sr/pivot/ml_signal
│   ├── decision_engine.py              # Decision dataclass, LLM mode + heuristic fallback
│   ├── knowledge.py                    # ChromaDB "ml_fx_patterns" — RAG signal history
│   ├── learning.py                     # LearningMachine "ml_fx_learnings" — agent self-learning
│   └── skills/
│       ├── ict-analysis/
│       │   └── SKILL.md               # Killzone rules, S/R role reversal, confidence scoring
│       └── risk-management/
│           └── SKILL.md               # SL/TP vs pp_s1/r1, position size vs confidence
│
├── outputs/                            # Auto-generated outputs directory
│   ├── reports/                        # Backtest reports, Heatmaps, Equity curves
│   └── models/                         # Saved ML models (.json, .joblib), SHAP plots
│
├── data/
│   ├── raw/                            # Phase 1 ✅ — Tick Parquet from Dukascopy
│   │   ├── XAUUSD/                    
│   │   │   ├── 2015-01.parquet
│   │   │   ├── ...
│   │   │   └── completed_months.json  # Download status + missing hours
│   │   └── BTCUSD/                    # Example Crypto fetch
│   ├── ohlcv/                         # Phase 3 — Resampled OHLCV (per symbol/tf)
│   ├── features/                      # Phase 3 — Feature DataFrames (per symbol/tf)
│   └── labels/                        # Phase 3 — Labeled data (LONG/SHORT/NEUTRAL)
│
├── docs/                               # Project documentation
│   ├── NOOB_GUIDE.md                  # Detailed principle guide
│   ├── USAGE_GUIDE.md                 # How to run commands
│   ├── TROUBLESHOOTING.md             # How to fix errors
│   ├── GLOSSARY.md                    # Glossary of terms
│   └── TODO.md                        # Detailed 7-phase plan
│
├── main.py                             # 🖥 TUI (Textual) — 4 tabs: Download | Pipeline | Train | Backtest
├── main.tcss                           # Textual CSS layout for TUI
├── config.toml                         # Quickstart defaults (pre-fills all TUI forms)
└── pyproject.toml                      # Pixi workspace (Polars, TA-Lib, Agno, ChromaDB…)
```

---

## Indicators — Input Signal Sources

### 1. ICT Killzone — `indicators/killzone.py`

Translated from the Pine Script **ICT Killzone** indicator.

#### `killzone.py` — Main API

Monitors and draws **Killzones** — the highest liquidity timeframes of the day:

| Killzone     | Time (ET)     | Characteristics                              |
| ------------ | ------------- | -------------------------------------------- |
| **Asia**     | 20:00 – 00:00 | Low liquidity, creates range for the new day |
| **London**   | 02:00 – 05:00 | Strong breakouts, often sets daily high/low  |
| **NY AM**    | 09:30 – 11:00 | Macro events, liquidity sweep                |
| **NY Lunch** | 12:00 – 13:00 | Low liquidity, avoid trading                 |
| **NY PM**    | 13:30 – 16:00 | Late day reversals                           |

**Additional Features:**
- **Killzone Pivots**: High/Low of each session, extended until broken
- **DWM Levels**: Target/running Open, High, Low for Day, Week, Month
- **Opening Prices**: True Day Open (00:00), 06:00, 10:00, 14:00 lines
- **Timestamp verticals**: Marks important time milestones

**Extracted ML Features:**
```text
in_{asia,london,nyam,nylunch,nypm}    # Killzone session flag
kz_{name}_high / _low / _mid          # Pivot for each session
kz_{name}_range / _avg_range          # Range and N-session moving average
kz_{name}_session_id                  # Session sequence number
dist_to_{name}_high / _low            # close − pivot level
d_open / d_high / d_low               # Day open, running high/low
w_open / w_high / w_low               # Week open, running high/low
m_open / m_high / m_low               # Month open, running high/low
pd_high / pd_low                      # Previous Day High/Low (PDH/PDL)
pw_high / pw_low                      # Previous Week High/Low
pm_high / pm_low                      # Previous Month High/Low
```

---

### 2. Support/Resistance & Pivot Points — `indicators/sr_pp.py`

Translated from the Pine Script **SR + PP** indicator.

#### A. Support/Resistance Boxes (Dynamic S/R)

Detects S/R zones based on **price patterns**, categorized as:

| Pattern      | Condition                                  | Type       |
| ------------ | ------------------------------------------ | ---------- |
| `r` (1-bar)  | Strong bearish candle breaks below low[2]  | Resistance |
| `r2` (2-bar) | Double bearish candle breaks 2-bar low     | Resistance |
| `s` (1-bar)  | Strong bullish candle breaks above high[2] | Support    |
| `s2` (2-bar) | Double bullish candle breaks 2-bar high    | Support    |

**Role Reversal**: when price breaks resistance → it becomes support, and vice versa.

#### B. Pivot Points (Multi-Timeframe)

| Type            | Formula / Characteristics          |
| --------------- | ---------------------------------- |
| **Traditional** | P = (H+L+C)/3 — most common        |
| **Fibonacci**   | Uses ratios 0.236, 0.382, 0.618    |
| **Woodie**      | Emphasizes closing price           |
| **Classic**     | Classic pivot                      |
| **DM**          | DeMark — only 3 levels (P, R1, S1) |
| **Camarilla**   | 9 intraday distribution levels     |

Timeframe anchor: Auto / Daily / Weekly / Monthly / Quarterly / Yearly — up to **200 historical pivot sets**.

**Extracted ML Features:**
```text
sr_resist_1bar / sr_resist_2bar        # Resistance pattern 1-bar / 2-bar
sr_support_1bar / sr_support_2bar      # Support pattern 1-bar / 2-bar
nearest_resist_high / _low             # Upper/lower bounds of nearest active resistance
nearest_support_high / _low            # Upper/lower bounds of nearest active support
in_resist_zone / in_support_zone       # Price is within S/R zone
dist_to_nearest_resist / _support      # close − nearest zone boundary
sr_role_reversal                       # 0 = neutral, +1 = resist→support, -1 = support→resist
pp_p / pp_r1..r5 / pp_s1..s5           # Pivot level values
pp_dist_to_p / pp_dist_to_r1 / _s1     # close − Pivot level
pp_above_p                             # Price above or below Pivot P
```

---

## Usage — Python Indicators

```python
import polars as pl
from indicators import add_killzone_features, add_sr_pp_features

# Load tick data resampled to 1H
df = pl.read_parquet("data/raw/XAUUSD/2024-01.parquet")

# Resample to 1H OHLCV
ohlcv = (
    df.sort("timestamp")
      .group_by_dynamic("timestamp", every="1h")
      .agg(
          pl.col("bid").first().alias("open"),
          pl.col("bid").max().alias("high"),
          pl.col("bid").min().alias("low"),
          pl.col("bid").last().alias("close"),
      )
)

# Add ICT Killzone features
ohlcv = add_killzone_features(ohlcv, avg_range_n=5)

# Add S/R + Pivot Point features
ohlcv = add_sr_pp_features(ohlcv, pivot_type="traditional", anchor="daily")

print(ohlcv.columns)
```

---

## Data — Collection and Storage

### `download_data.py` — XAUUSD Tick Data

Script to fetch historical **tick (bid/ask)** data from **Dukascopy** (since 2015):

| Parameter      | Value                                                 |
| -------------- | ----------------------------------------------------- |
| Symbol         | `XAUUSD`                                              |
| Source         | `datafeed.dukascopy.com`                              |
| Raw Format     | `.bi5` (LZMA-compressed binary)                       |
| Storage Format | **Parquet** (Polars, by month)                        |
| Storage Path   | `data/raw/XAUUSD/`                                    |
| Schema         | `timestamp`, `ask`, `bid`, `ask_volume`, `bid_volume` |

**Script features:**
- **Async download** (`aiohttp`) — 20 concurrent connections, optimized speed
- **State management** via `completed_months.json` — skips downloaded months
- **Auto-repair** — detects and fetches missing hours in a month
- **Migration** — converts legacy `.complete` format to new JSON
- **Retry logic** — exponential backoff on timeouts/rate-limits
- Skips Saturdays and Sundays before 21:00 UTC (when gold market is closed)

```bash
# Download all XAUUSD data
pixi run python pipeline/download_data.py
```

---

## ML Pipeline

```text
Fetch ticks     →  ETL & Resample   →  Feature Engineering   →  Labeling
(Dukascopy/bi5)    (Polars/Parquet)    (ICT + S/R + PP)         (LONG/SHORT/NEUTRAL)
      ↓
  Training          →  Backtesting    →  Model Registry   →  AI Agent (Agno)
(XGBoost/LSTM/KNN)    (Equity curve)     (Best model)         (Realtime signal)
```

### Labeling

- **Target**: Price direction after `N` candles (N = 5, 10, 20)
- **Classes**: `LONG (1)`, `SHORT (−1)`, `NEUTRAL (0)`
- Threshold defined by **ATR-based logic**

### Models

| Model                  | Used for                               |
| ---------------------- | -------------------------------------- |
| **KNN**                | Baseline, filtering killzone signals   |
| **XGBoost / LightGBM** | Feature-based classification (tabular) |
| **LSTM**               | Short-term time series prediction      |
| **Transformer**        | Multi-timeframe attention              |

---

## Built With

### Data & Processing

| Library                                  | Purpose                             | Notes                              |
| ---------------------------------------- | ----------------------------------- | ---------------------------------- |
| **[Polars](https://pola.rs/)**           | DataFrame, ETL, feature engineering | Replaces Pandas — 10–100x faster   |
| **[PyArrow](https://arrow.apache.org/)** | Parquet I/O                         | Columnar format, great compression |
| **[TA-Lib](https://ta-lib.org/)**        | RSI, EMA, ATR, indicators           | C-based, extremely fast            |
| **[aiohttp](https://docs.aiohttp.org/)** | Async HTTP download                 | 20 concurrent connections          |
| **[QuestDB](https://questdb.io/)**       | Time-series database                | Ultra-fast tick data queries       |

### Visualization

| Library                  | Purpose                                            |
| ------------------------ | -------------------------------------------------- |
| **Plotly**               | Interactive candlesticks, S/R & killzone overlays  |
| **Matplotlib / Seaborn** | Feature importance, equity curve, confusion matrix |

### AI Agent

| Library                                      | Purpose                                                                                |
| -------------------------------------------- | -------------------------------------------------------------------------------------- |
| **[Agno](https://github.com/agno-agi/agno)** | Agent framework — 6-step: LMStudio, ReasoningTools, Knowledge, LearningMachine, Skills |
| **[LM Studio](https://lmstudio.ai/)**        | Local LLM (free, offline, OpenAI-compatible)                                           |
| **[ChromaDB](https://www.trychroma.com/)**   | Vector store — RAG patterns + agent learnings                                          |
| **SqliteDb** (agno)                          | Store session-based chat history                                                       |

---

## Installation

```bash
# Manage environments with Pixi (recommended)
pixi install

# Download XAUUSD data from 2015 to present (Default)
pixi run python pipeline/download_data.py

# Or download Crypto
# pixi run python pipeline/download_data.py --symbol BTCUSD --asset-class crypto
```

**Requirements**: Python ≥ 3.13, Pixi

---

## 🚀 Quickstart 5 minutes with Textual Interface

ML_FX features an interactive Terminal User Interface (TUI) built with [Textual](https://textual.textualize.io/).  
Instead of typing long commands, you can just click tabs, fill out forms, and press a button — log output streams directly to your screen.

### Running the TUI

```bash
# Install environment (first time)
pixi install

# Launch the interface
pixi run python main.py
```

> **Shortcuts:** `q` — quit &nbsp;|&nbsp; `d` — toggle dark/light mode

### Default Configuration (`config.toml`)

On startup, `main.py` reads the root `config.toml` file to automatically pre-fill the forms.  
Edit this file to change your default symbol, timeframe, or hyperparameters:

```toml
[download]
symbol      = "XAUUSD"
start_year  = 2015

[pipeline]
timeframe   = "1H"

[train]
backend   = "xgb"
n_trials  = 30
```

### The Complete Workflow (4 Steps)

| Step | Tab                 | Function                                                |
| ---- | ------------------- | ------------------------------------------------------- |
| 1️⃣    | **📥 Download Data** | Download tick data from Dukascopy, choose symbol + year |
| 2️⃣    | **🔄 Pipeline**      | Resample → Feature engineering → Labeling               |
| 3️⃣    | **🧠 Train Model**   | Select backend (XGBoost/LightGBM), run Optuna tuning    |
| 4️⃣    | **📊 Backtest**      | Run walk-forward backtest, view Sharpe / Drawdown       |

All steps run in a background thread — ensuring the UI never freezes while tasks are executing.

---

## Roadmap

- [x] Phase 1: Universal tick data collection (`pipeline/download_data.py`)
- [x] Phase 2: Signal embedding (ICT Killzone, Support/Resistance + Pivot Points)
- [x] Phase 3: ETL & Feature Engineering Pipeline (Resample OHLCV, 130+ features)
- [x] Phase 4: Labeling + Machine Learning Training (KNN, XGBoost, LSTM)
- [x] Phase 5: Backtesting Engine (Risk:Reward simulation) & Reporting (Plotly, Matplotlib)
- [ ] Phase 6: AI Agent (Agno 6-step) — Chatbot leveraging model signals
- [ ] Phase 7: Expansion to Forex + Crypto

---

## Author

**Hieu Nguyen** — [@ultimateBroK](https://github.com/ultimateBroK)  
Contact: hieuteo03@gmail.com