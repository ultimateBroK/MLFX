# MLFX — Feature Reference

This document lists the columns produced by `mlfx pipeline`, explains what each column means, and shows which configuration parameters affect them.

---

## 1. Base OHLCV Columns

These columns are created from raw tick data after resampling into candles and are always present in the output.

| Column | Type | Description |
|---|---|---|
| `timestamp` | Datetime (UTC) | Bar open timestamp |
| `open` | Float | Open price |
| `high` | Float | Highest price |
| `low` | Float | Lowest price |
| `close` | Float | Close price |
| `volume` | Float | Tick volume for the bar |

> **Note:** OHLCV is computed from the **mid-price** (`(bid + ask) / 2`), not from bid or ask alone.

---

## 2. Momentum Indicators

This group is controlled by `[features]` in `config.toml`.

| Column | Config key | Default | Description |
|---|---|---|---|
| `rsi_{period}` | `rsi_period` | `14` | Relative Strength Index (RSI) |
| `macd` | `macd_fast`, `macd_slow` | `12`, `26` | MACD line |
| `macd_signal` | `macd_signal` | `9` | MACD signal line |
| `macd_hist` | — | — | Difference between `macd` and `macd_signal` |

---

## 3. Volatility Indicators

| Column | Config key | Default | Description |
|---|---|---|---|
| `atr_{period}` | `atr_period` | `14` | Average True Range (ATR) |

---

## 4. Exponential Moving Averages (EMA)

| Column | Config key | Default | Description |
|---|---|---|---|
| `ema_20` | `ema_periods` | `[20, 50, 200]` | 20-bar EMA |
| `ema_50` | `ema_periods` | `[20, 50, 200]` | 50-bar EMA |
| `ema_200` | `ema_periods` | `[20, 50, 200]` | 200-bar EMA |

You can add more EMA columns by changing `ema_periods` in the configuration file.

---

## 5. Pivot Levels and Support / Resistance

These columns are added by `add_sr_pp_features()`. The calculation method is selected via `--pivot` or `pivot_type`.

**Supported methods:** `traditional`, `fibonacci`, `woodie`, `classic`, `demark`, `camarilla`

| Column pattern | Description |
|---|---|
| `pp` | Central pivot point |
| `r1`, `r2`, `r3`, `r4` | Resistance levels |
| `s1`, `s2`, `s3`, `s4` | Support levels |
| `pp_dist_{level}` | Raw price distance from `close` to each level |
| `pp_dist_{level}_atr` | Distance normalized by ATR |

The anchoring period is selected via `--anchor` or `pivot_anchor`, with common values:

- `daily`
- `weekly`
- `monthly`

---

## 6. ICT Killzones and Trading Sessions

All timestamps are converted to **U.S. Eastern Time** (`America/New_York`) before session flags are computed.

### 6.1 Session Flags

| Column | ET window | Description |
|---|---|---|
| `in_asia` | from 20:00 onward | Asian session |
| `in_london` | 02:00 – 05:00 | London killzone |
| `in_nyam` | 09:30 – 11:00 | New York AM killzone |
| `in_nylunch` | 12:00 – 13:00 | New York lunch |
| `in_nypm` | 13:30 – 16:00 | New York PM killzone |

### 6.2 Session-Derived Columns

For each session `{kz}` in `[asia, london, nyam, nylunch, nypm]`, the system creates the following columns:

| Column | Description |
|---|---|
| `kz_{kz}_session_id` | Integer counter for each contiguous session instance |
| `kz_{kz}_high` | Running session high |
| `kz_{kz}_low` | Running session low |
| `kz_{kz}_mid` | Midpoint of the session |
| `kz_{kz}_range` | Price range of the session |
| `kz_{kz}_avg_range` | Average range over the last `avg_range_n` sessions |
| `dist_to_{kz}_high` | Distance from `close` to the session high |
| `dist_to_{kz}_low` | Distance from `close` to the session low |
| `dist_to_{kz}_high_atr` | ATR-normalized distance to the session high |
| `dist_to_{kz}_low_atr` | ATR-normalized distance to the session low |

The `avg_range_n` key in `[features]` controls how many sessions are used for the rolling average. Default: `5`.

### 6.3 Day / Week / Month Levels

| Column | Description |
|---|---|
| `d_open` | Open price of the current day |
| `d_high` | Running high of the current day |
| `d_low` | Running low of the current day |
| `w_open` | Open price of the current week |
| `w_high` | Running high of the current week |
| `w_low` | Running low of the current week |
| `m_open` | Open price of the current month |
| `m_high` | Running high of the current month |
| `m_low` | Running low of the current month |
| `pd_high` | Previous day high |
| `pd_low` | Previous day low |
| `pw_high` | Previous week high |
| `pw_low` | Previous week low |
| `pm_high` | Previous month high |
| `pm_low` | Previous month low |

---

## 7. ICT Order Blocks

Order blocks are used to identify structural price zones that often appear before strong moves.

### Detection Logic

1. Compute the average body size over the last 5 candles (`avg_body`)
2. A candle is considered “large” if `body > avg_body × 1.5`
3. A **bullish order block** is: a bearish candle immediately followed by a large bullish candle
4. A **bearish order block** is: a bullish candle immediately followed by a large bearish candle

| Column | Type | Description |
|---|---|---|
| `ob_bullish` | Boolean | This candle is a bullish order block |
| `ob_bearish` | Boolean | This candle is a bearish order block |
| `ob_bull_high` | Float | High of the most recent bullish order block |
| `ob_bull_low` | Float | Low of the most recent bullish order block |
| `ob_bear_high` | Float | High of the most recent bearish order block |
| `ob_bear_low` | Float | Low of the most recent bearish order block |
| `price_in_bull_ob` | Boolean | `close` is inside the bullish order-block zone |
| `price_in_bear_ob` | Boolean | `close` is inside the bearish order-block zone |

---

## 8. Fair Value Gap (FVG)

An FVG is a price imbalance identified by a 3-candle pattern.

### Detection Logic

- **Bullish FVG**: the current bar’s `low` is higher than the `high` of the bar 2 periods ago
- **Bearish FVG**: the current bar’s `high` is lower than the `low` of the bar 2 periods ago

| Column | Type | Description |
|---|---|---|
| `fvg_bullish` | Boolean | This candle creates a bullish FVG |
| `fvg_bearish` | Boolean | This candle creates a bearish FVG |
| `fvg_bull_top` | Float | Top of the most recent bullish FVG |
| `fvg_bull_bot` | Float | Bottom of the most recent bullish FVG |
| `fvg_bear_top` | Float | Top of the most recent bearish FVG |
| `fvg_bear_bot` | Float | Bottom of the most recent bearish FVG |
| `price_in_bull_fvg` | Boolean | `close` is inside the bullish FVG zone |
| `price_in_bear_fvg` | Boolean | `close` is inside the bearish FVG zone |

---

## 9. Label Columns

Labels are added by the labeling stage in the pipeline, unless `--skip-labels` is used.

### Look-ahead horizons

- `5`
- `10`
- `20`

### Label threshold

The threshold is calculated as:

- `atr_mult × atr_14`

Default `atr_mult = 0.5`, so the threshold is `0.5 × ATR_14`.

| Label value | Meaning |
|---|---|
| `2` | Close after `horizon` bars is more than `2 × threshold` above the current close |
| `1` | Close after `horizon` bars is between `threshold` and `2 × threshold` above the current close |
| `0` | Close after `horizon` bars stays within `±threshold` |
| `-1` | Close after `horizon` bars is between `threshold` and `2 × threshold` below the current close |
| `-2` | Close after `horizon` bars is more than `2 × threshold` below the current close |
| `null` | Not enough future data exists to build the label |

| Column | Horizon | Description |
|---|---|---|
| `label_5` | 5 bars | Short-horizon directional label |
| `label_10` | 10 bars | Medium-horizon directional label |
| `label_20` | 20 bars | Long-horizon directional label |

The `atr_mult` key is controlled by `--atr-mult` in the CLI and `atr_mult` in the `[pipeline]` section of the config.

---

## 10. Summary of Column Count

A run with default settings typically produces **90+ columns** per candle, including:

- 6 base OHLCV columns
- 4 momentum-indicator columns
- 1 ATR column
- 3 EMA columns
- roughly 15 pivot-related columns (depending on method)
- 5 session flags and many session-derived columns
- 9 day / week / month level columns
- 8 order-block columns
- 8 FVG columns
- 3 label columns

The exact number of columns depends on:

- the chosen pivot method
- the `ema_periods` list
- which feature groups are enabled in the pipeline

---

## 11. How to Use This Document

Use this reference when you need to answer questions such as:

- Which stage creates this column?
- What does this column mean?
- Which config key affects this column?
- If I want to change how this column is created, where should I look?

If you want more detail:

- For how to run the pipeline: see `USAGE_GUIDE.md`
- For system design: see `ARCHITECTURE.md`
- For terminology: see `GLOSSARY.md`
- For model evaluation: see `EVALUATION_GUIDE.md`
