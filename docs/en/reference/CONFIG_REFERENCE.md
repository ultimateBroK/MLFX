# MLFX Configuration Reference

Complete reference for `config.toml` settings and CLI flags.

---

## Overview

MLFX uses a two-layer configuration system:

1. **`config.toml`** — project-wide defaults (optional but recommended)
2. **CLI flags** — override defaults per command

The CLI reads `config.toml` from the project root automatically. Any CLI argument overrides the corresponding config value.

---

## Config Sections

### `[download]` — Data Ingestion

| Key | Type | Default | CLI Override | Description |
|-----|------|---------|--------------|-------------|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Instrument symbol to download |
| `asset_class` | string | `"fx"` | `--asset-class` | Asset class: `"fx"`, `"crypto"` |
| `start_year` | integer | `2015` | `--start-year` | Start year for download |
| `start_month` | integer | `1` | `--start-month` | Start month (1-12) |
| `end_year` | integer | current year | `--end-year` | End year (optional) |
| `end_month` | integer | current month | `--end-month` | End month (optional) |
| `concurrency` | integer | `20` | `--concurrency` | Parallel download workers |

**Example:**
```toml
[download]
symbol = "XAUUSD"
asset_class = "fx"
start_year = 2015
start_month = 1
concurrency = 20
```

---

### `[pipeline]` — Feature Pipeline

| Key | Type | Default | CLI Override | Description |
|-----|------|---------|--------------|-------------|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Symbol to process |
| `timeframe` | string | `"1H"` | `--tf` | Target timeframe(s) |
| `pivot_type` | string | `"traditional"` | `--pivot` | Pivot calculation method |
| `pivot_anchor` | string | `"daily"` | `--anchor` | Pivot anchor timeframe |
| `atr_period` | integer | `14` | `--atr-period` | ATR calculation window |
| `atr_mult` | float | `0.5` | `--atr-mult` | ATR multiplier for labels |

**Pivot types:** `traditional`, `fibonacci`, `woodie`, `classic`, `demark`, `camarilla`

**Pivot anchors:** `daily`, `weekly`, `monthly`

**Timeframes:** `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`

**Example:**
```toml
[pipeline]
symbol = "XAUUSD"
timeframe = "1H"
pivot_type = "traditional"
pivot_anchor = "daily"
```

---

### `[train]` — Training Configuration

| Key | Type | Default | CLI Override | Description |
|-----|------|---------|--------------|-------------|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Symbol to train on |
| `timeframe` | string | `"1H"` | `--tf` | Timeframe |
| `label_col` | string | `"label_10"` | `--label` | Target label column |
| `backend` | string | `"mlf"` | `--backend` | Training backend |
| `n_trials` | integer | `30` | `--n-trials` | Optuna trials (MLForecast only) |
| `n_splits` | integer | `5` | `--n-splits` | Cross-validation folds |

**Backends:** `mlf`, `lstm`, `bilstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`

**Labels:** `label_5`, `label_10`, `label_20`

**Example:**
```toml
[train]
symbol = "XAUUSD"
timeframe = "1H"
label_col = "label_10"
backend = "mlf"
n_trials = 15
n_splits = 5
```

---

### `[features]` — Technical Indicators

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `rsi_period` | integer | `14` | RSI calculation window |
| `atr_period` | integer | `14` | ATR calculation window |
| `ema_periods` | list | `[20, 50, 200]` | EMA periods to compute |
| `macd_fast` | integer | `12` | MACD fast EMA period |
| `macd_slow` | integer | `26` | MACD slow EMA period |
| `macd_signal` | integer | `9` | MACD signal period |
| `avg_range_n` | integer | `5` | Rolling window for killzone avg range |

**Example:**
```toml
[features]
rsi_period = 14
atr_period = 14
ema_periods = [20, 50, 200]
macd_fast = 12
macd_slow = 26
macd_signal = 9
avg_range_n = 5
```

---

### `[backtest]` — Evaluation Settings

| Key | Type | Default | CLI Override | Description |
|-----|------|---------|--------------|-------------|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Symbol to evaluate |
| `timeframe` | string | `"1H"` | `--tf` | Timeframe |
| `label_col` | string | `"label_10"` | `--label` | Signal column |
| `tp_r` | float | `1.5` | `--tp` | Take-profit in R-multiples |
| `sl_r` | float | `1.0` | `--sl` | Stop-loss in R-multiples |
| `initial_capital` | float | `10000.0` | `--capital` | Starting capital |
| `risk_pct` | float | `1.0` | `--risk` | Risk per trade (%) |
| `commission` | float | `0.1` | `--commission` | Commission per trade |
| `slippage` | float | `0.0` | `--slippage` | Slippage simulation |

**Example:**
```toml
[backtest]
symbol = "XAUUSD"
timeframe = "1H"
label_col = "label_10"
tp_r = 1.5
sl_r = 1.0
initial_capital = 10000.0
risk_pct = 1.0
commission = 0.1
```

---

## Complete Example

```toml
# MLFX Configuration
# This file is read by the `mlfx` CLI.
# Edit these defaults to match your workflow.

[download]
symbol      = "XAUUSD"
asset_class = "fx"
start_year  = 2015
start_month = 1
concurrency = 20

[pipeline]
symbol       = "XAUUSD"
timeframe    = "1H"
pivot_type   = "traditional"
pivot_anchor = "daily"

[train]
symbol     = "XAUUSD"
timeframe  = "1H"
label_col  = "label_10"
backend    = "mlf"
n_trials   = 15
n_splits   = 5

[features]
rsi_period  = 14
atr_period  = 14
ema_periods = [20, 50, 200]
macd_fast   = 12
macd_slow   = 26
macd_signal = 9
avg_range_n = 5

[backtest]
symbol          = "XAUUSD"
timeframe       = "1H"
label_col       = "label_10"
tp_r            = 1.5
sl_r            = 1.0
initial_capital = 10000.0
risk_pct        = 1.0
commission      = 0.1
```

---

## CLI Flag Reference

### Global Flags

All commands support:

| Flag | Description |
|------|-------------|
| `--help` | Show command help |
| `--version` | Show version |

### `download` Command

| Flag | Default | Description |
|------|---------|-------------|
| `--symbol` | from config | Instrument symbol |
| `--asset-class` | from config | Asset class |
| `--start-year` | from config | Start year |
| `--start-month` | from config | Start month |
| `--end-year` | current year | End year |
| `--end-month` | current month | End month |
| `--concurrency` | from config | Parallel workers |
| `--force` | false | Re-download existing months |
| `--skip-current-month` | false | Skip current month check |

### `pipeline` Command

| Flag | Default | Description |
|------|---------|-------------|
| `--symbol` | from config | Symbol to process |
| `--tf` | from config | Timeframe(s), space-separated |
| `--pivot` | from config | Pivot type |
| `--anchor` | from config | Pivot anchor |
| `--atr-period` | from config | ATR period |
| `--atr-mult` | from config | ATR multiplier for labels |
| `--force` | false | Overwrite existing files |
| `--skip-resample` | false | Skip OHLCV generation |
| `--skip-features` | false | Skip feature engineering |
| `--skip-labels` | false | Skip label generation |

### `train` Command

| Flag | Default | Description |
|------|---------|-------------|
| `--symbol` | from config | Symbol to train |
| `--tf` | from config | Timeframe |
| `--label` | from config | Label column |
| `--backend` | from config | Training backend |
| `--n-trials` | from config | Optuna trials |
| `--n-splits` | from config | CV folds |
| `--force` | false | Retrain even if model exists |

### `evaluate` Command

| Flag | Default | Description |
|------|---------|-------------|
| `--symbol` | from config | Symbol to evaluate |
| `--tf` | from config | Timeframe |
| `--label` | from config | Label column |
| `--tp` | from config | Take-profit (R) |
| `--sl` | from config | Stop-loss (R) |
| `--capital` | from config | Initial capital |
| `--risk` | from config | Risk per trade (%) |
| `--commission` | from config | Commission |
| `--slippage` | from config | Slippage |
| `--use-labels` | false | Backtest labels instead of model |

### `serve` Command

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8000` | Listen port |
| `--reload` | false | Hot-reload (dev only) |

### `drift` Command

| Flag | Default | Description |
|------|---------|-------------|
| `--symbol` | from config | Symbol to check |
| `--tf` | from config | Timeframe |
| `--threshold-ks` | `0.1` | KS test threshold |
| `--threshold-psi` | `0.2` | PSI threshold |

---

## Configuration Precedence

Values are resolved in this order (highest priority first):

1. CLI flags (explicit)
2. Environment variables (if supported)
3. `config.toml` values
4. Built-in defaults

---

## Tips

- Keep `config.toml` in version control with sensible defaults
- Use CLI flags for one-off experiments
- Multiple timeframes: `pixi run mlfx pipeline --tf 1H 4H 1D`
- View effective config: `pixi run mlfx <command> --help` shows defaults
