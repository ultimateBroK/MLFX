# MLFX — Feature Reference

This document lists every column produced by `mlfx pipeline` (the `pipeline` stage), their meanings, and the configuration parameters that control them.

---

## 1. OHLCV Base Columns

These columns come from the raw tick data after resampling and are always present.

| Column | Type | Description |
|---|---|---|
| `timestamp` | Datetime (UTC) | Bar open timestamp |
| `open` | Float | Bar open price |
| `high` | Float | Bar high price |
| `low` | Float | Bar low price |
| `close` | Float | Bar close price |
| `volume` | Float | Tick volume for the bar |

> **Note**: OHLCV is derived from the **mid-price** (`(bid + ask) / 2`), not from bid or ask alone.

---

## 2. Momentum Indicators

Controlled by `[features]` in `config.toml`.

| Column | Config key | Default | Description |
|---|---|---|---|
| `rsi_{period}` | `rsi_period` | `14` | Relative Strength Index |
| `macd` | `macd_fast`, `macd_slow` | `12`, `26` | MACD line |
| `macd_signal` | `macd_signal` | `9` | MACD signal line |
| `macd_hist` | — | — | MACD histogram (`macd - macd_signal`) |

---

## 3. Volatility Indicators

| Column | Config key | Default | Description |
|---|---|---|---|
| `atr_{period}` | `atr_period` | `14` | Average True Range |

---

## 4. Moving Averages

| Column | Config key | Default | Description |
|---|---|---|---|
| `ema_20` | `ema_periods` | `[20, 50, 200]` | Exponential moving average (20-bar) |
| `ema_50` | `ema_periods` | `[20, 50, 200]` | Exponential moving average (50-bar) |
| `ema_200` | `ema_periods` | `[20, 50, 200]` | Exponential moving average (200-bar) |

Additional EMA columns are created for each value in `ema_periods`.

---

## 5. Pivot Points

Added by `add_sr_pp_features()`. The pivot method is selected by `--pivot` / `pivot_type` in config.

**Supported methods**: `traditional`, `fibonacci`, `woodie`, `camarilla`, `demark`

| Column pattern | Description |
|---|---|
| `pp` | Central pivot point |
| `r1`, `r2`, `r3`, `r4` | Resistance levels (r4 not present in all methods) |
| `s1`, `s2`, `s3`, `s4` | Support levels (s4 not present in all methods) |
| `pp_dist_{level}` | Raw price distance from close to each pivot level |
| `pp_dist_{level}_atr` | ATR-normalized distance (`pp_dist_{level} / atr_14`) |

Anchoring period (`daily`, `weekly`, `monthly`) is selected by `--anchor` / `pivot_anchor` in config.

---

## 6. ICT Killzones

All timestamps are converted to **Eastern Time (ET / America/New_York)** before computing session flags.

### 6.1 Session Flags

| Column | ET window | Description |
|---|---|---|
| `in_asia` | 20:00 onwards | Asian session (start of New York evening session) |
| `in_london` | 02:00 – 05:00 | London open killzone |
| `in_nyam` | 09:30 – 11:00 | New York AM killzone |
| `in_nylunch` | 12:00 – 13:00 | New York lunch |
| `in_nypm` | 13:30 – 16:00 | New York PM killzone |

### 6.2 Per-Session Derived Columns

For each session name `{kz}` in `[asia, london, nyam, nylunch, nypm]`:

| Column | Description |
|---|---|
| `kz_{kz}_session_id` | Integer counter identifying each contiguous session instance |
| `kz_{kz}_high` | Running session high (cumulative max within the session) |
| `kz_{kz}_low` | Running session low (cumulative min within the session) |
| `kz_{kz}_mid` | Session midpoint `(kz_high + kz_low) / 2` |
| `kz_{kz}_range` | Session range `kz_high - kz_low` |
| `kz_{kz}_avg_range` | Rolling `avg_range_n`-session average of `kz_range` |
| `dist_to_{kz}_high` | `close - kz_high` |
| `dist_to_{kz}_low` | `close - kz_low` |
| `dist_to_{kz}_high_atr` | ATR-normalized `dist_to_{kz}_high` |
| `dist_to_{kz}_low_atr` | ATR-normalized `dist_to_{kz}_low` |

`avg_range_n` is controlled by the `avg_range_n` key in `[features]` (default: `5` sessions).

### 6.3 Day / Week / Month Running Levels

| Column | Description |
|---|---|
| `d_open` | Today's opening price (ET calendar day) |
| `d_high` | Today's running high |
| `d_low` | Today's running low |
| `w_open` | This week's opening price |
| `w_high` | This week's running high |
| `w_low` | This week's running low |
| `m_open` | This month's opening price |
| `m_high` | This month's running high |
| `m_low` | This month's running low |
| `pd_high` | Previous calendar day high |
| `pd_low` | Previous calendar day low |
| `pw_high` | Previous week high |
| `pw_low` | Previous week low |
| `pm_high` | Previous month high |
| `pm_low` | Previous month low |

---

## 7. Order Blocks (ICT)

Order blocks identify institutional candles that precede strong moves.

**Detection logic**:
1. Compute a 5-bar rolling average candle body size (`avg_body`)
2. A candle is a "big" candle when `body > avg_body × 1.5`
3. A **bullish order block** is: a bearish candle immediately followed by a big bullish candle
4. A **bearish order block** is: a bullish candle immediately followed by a big bearish candle

| Column | Type | Description |
|---|---|---|
| `ob_bullish` | Boolean | This bar is a bullish OB candle |
| `ob_bearish` | Boolean | This bar is a bearish OB candle |
| `ob_bull_high` | Float | Most recent bullish OB high (forward-filled) |
| `ob_bull_low` | Float | Most recent bullish OB low (forward-filled) |
| `ob_bear_high` | Float | Most recent bearish OB high (forward-filled) |
| `ob_bear_low` | Float | Most recent bearish OB low (forward-filled) |
| `price_in_bull_ob` | Boolean | Close is between `ob_bull_low` and `ob_bull_high` |
| `price_in_bear_ob` | Boolean | Close is between `ob_bear_low` and `ob_bear_high` |

---

## 8. Fair Value Gaps (FVG)

FVGs are price imbalances identified by a 3-bar gap pattern.

**Detection logic**:
- A **bullish FVG** exists when the current bar's `low` is higher than the bar 2 periods ago's `high` (gap up)
- A **bearish FVG** exists when the current bar's `high` is lower than the bar 2 periods ago's `low` (gap down)

| Column | Type | Description |
|---|---|---|
| `fvg_bullish` | Boolean | This bar creates a bullish FVG |
| `fvg_bearish` | Boolean | This bar creates a bearish FVG |
| `fvg_bull_top` | Float | Top of the most recent bullish FVG (forward-filled) |
| `fvg_bull_bot` | Float | Bottom of the most recent bullish FVG (forward-filled) |
| `fvg_bear_top` | Float | Top of the most recent bearish FVG (forward-filled) |
| `fvg_bear_bot` | Float | Bottom of the most recent bearish FVG (forward-filled) |
| `price_in_bull_fvg` | Boolean | Close is within the bullish FVG zone |
| `price_in_bear_fvg` | Boolean | Close is within the bearish FVG zone |

---

## 9. Label Columns

Labels are added by the labeling stage (`mlfx pipeline` includes labels unless `--skip-labels` is used).

**Horizons**: `5`, `10`, `20` bars ahead.

**Threshold**: `atr_mult × atr_14` (default `atr_mult=0.5`, so threshold = `0.5 × ATR_14`)

| Label value | Meaning |
|---|---|
| `2` | Close `+horizon` is more than `2 × threshold` above current close (strong bullish) |
| `1` | Close `+horizon` is between `threshold` and `2 × threshold` above (bullish) |
| `0` | Close `+horizon` is within `±threshold` of current close (neutral / no trade) |
| `-1` | Close `+horizon` is between `threshold` and `2 × threshold` below (bearish) |
| `-2` | Close `+horizon` is more than `2 × threshold` below current close (strong bearish) |
| `null` | The forward bar does not exist (last `horizon` rows of each file) |

| Column | Horizon | Description |
|---|---|---|
| `label_5` | 5 bars | Short-horizon directional label |
| `label_10` | 10 bars | Medium-horizon directional label (recommended default) |
| `label_20` | 20 bars | Long-horizon directional label |

`atr_mult` is controlled by `--atr-mult` in the CLI and `atr_mult` in `[pipeline]` config.

---

## 10. Summary: Column Count

A typical run with default settings produces approximately **90+ columns** per bar. This includes:

- 6 OHLCV base columns
- 4 momentum (rsi, macd ×3)
- 1 ATR
- 3 EMA
- ~15 pivot columns (method-dependent)
- 5 session flags + 10×5 per-session derived columns
- 9 DWM level columns
- 8 order block columns
- 8 FVG columns
- 3 label columns (added last)

The exact count varies by pivot method and the `ema_periods` setting.
