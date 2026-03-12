# MLFX Configuration Reference

This document is the complete reference for `config.toml` and the corresponding CLI flags in MLFX.

---

## Related Documentation

- [English Docs Hub](../README.md)
- [Quickstart](../getting-started/QUICKSTART.md)
- [Configuration and Usage Guide](../guides/USAGE_GUIDE.md)
- [Evaluation Guide](../guides/EVALUATION_GUIDE.md)
- [Architecture](../architecture/ARCHITECTURE.md)
- [Feature Reference](FEATURE_REFERENCE.md)

---

## 1. Overview

MLFX uses a two-layer configuration model:

1. **`config.toml`** — where project-wide default values are declared
2. **CLI flags** — used to override those defaults for a specific run

The CLI automatically reads `config.toml` from the project root. If you pass a parameter directly on the command line, that value **takes precedence** over the value in the config file.

---

## 2. Sections in `config.toml`

## 2.1. `[download]` — Input data download

| Key | Type | Default | Corresponding CLI flag | Description |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Instrument symbol to download |
| `asset_class` | string | `"fx"` | `--asset-class` | Asset class: `"fx"`, `"crypto"` |
| `start_year` | integer | `2015` | `--start-year` | Start year for download |
| `start_month` | integer | `1` | `--start-month` | Start month (`1-12`) |
| `end_year` | integer | current year | `--end-year` | End year for download |
| `end_month` | integer | current month | `--end-month` | End month for download |
| `concurrency` | integer | `20` | `--concurrency` | Number of parallel download workers |

### Example

```/dev/null/config-reference-download.toml#L1-7
[download]
symbol = "XAUUSD"
asset_class = "fx"
start_year = 2015
start_month = 1
end_year = 2025
concurrency = 20
```

---

## 2.2. `[pipeline]` — Data processing, features, and labels

| Key | Type | Default | Corresponding CLI flag | Description |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Instrument symbol to process |
| `timeframe` | string | `"1H"` | `--tf` | Target timeframe |
| `pivot_type` | string | `"traditional"` | `--pivot` | Pivot-point calculation method |
| `pivot_anchor` | string | `"daily"` | `--anchor` | Pivot anchor period |
| `atr_period` | integer | `14` | `--atr-period` | ATR calculation window |
| `atr_mult` | float | `0.5` | `--atr-mult` | ATR multiplier used during label generation |

### Supported pivot methods

- `traditional`
- `fibonacci`
- `woodie`
- `classic`
- `demark`
- `camarilla`

### Supported anchor periods

- `daily`
- `weekly`
- `monthly`

### Common timeframes

- `1m`
- `5m`
- `15m`
- `30m`
- `1H`
- `2H`
- `4H`
- `1D`

### Example

```/dev/null/config-reference-pipeline.toml#L1-6
[pipeline]
symbol = "XAUUSD"
timeframe = "1H"
pivot_type = "traditional"
pivot_anchor = "daily"
atr_mult = 0.5
```

---

## 2.3. `[train]` — Training configuration

| Key | Type | Default | Corresponding CLI flag | Description |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Instrument symbol used for training |
| `timeframe` | string | `"1H"` | `--tf` | Training timeframe |
| `label_col` | string | `"label_10"` | `--label` | Target label column |
| `backend` | string | `"mlf"` | `--backend` | Training backend |
| `n_trials` | integer | `30` | `--n-trials` | Number of hyperparameter trials, mainly for `mlf` |
| `n_splits` | integer | `5` | `--n-splits` | Number of cross-validation folds |

### Supported backends

- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

### Supported labels

- `label_5`
- `label_10`
- `label_20`

### Example

```/dev/null/config-reference-train.toml#L1-7
[train]
symbol = "XAUUSD"
timeframe = "1H"
label_col = "label_10"
backend = "mlf"
n_trials = 15
n_splits = 5
```

---

## 2.4. `[features]` — Feature-engineering configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `rsi_period` | integer | `14` | RSI calculation window |
| `atr_period` | integer | `14` | ATR calculation window |
| `ema_periods` | list | `[20, 50, 200]` | EMA periods to generate |
| `macd_fast` | integer | `12` | MACD fast EMA period |
| `macd_slow` | integer | `26` | MACD slow EMA period |
| `macd_signal` | integer | `9` | MACD signal-line period |
| `avg_range_n` | integer | `5` | Number of sessions used for killzone average range |

### Example

```/dev/null/config-reference-features.toml#L1-8
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

## 2.5. `[backtest]` — Evaluation and trade simulation

| Key | Type | Default | Corresponding CLI flag | Description |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Instrument symbol to evaluate |
| `timeframe` | string | `"1H"` | `--tf` | Backtest timeframe |
| `label_col` | string | `"label_10"` | `--label` | Signal column used for backtesting |
| `tp_r` | float | `1.5` | `--tp` | Take-profit in `R` |
| `sl_r` | float | `1.0` | `--sl` | Stop-loss in `R` |
| `initial_capital` | float | `10000.0` | `--capital` | Initial capital |
| `risk_pct` | float | `1.0` | `--risk` | Percentage of capital risked per trade |
| `commission` | float | `0.1` | `--commission` | Commission cost per trade |
| `slippage` | float | `0.0` | `--slippage` | Simulated slippage |

### Example

```/dev/null/config-reference-backtest.toml#L1-9
[backtest]
symbol = "XAUUSD"
timeframe = "1H"
label_col = "label_10"
tp_r = 1.5
sl_r = 1.0
initial_capital = 10000.0
risk_pct = 1.0
commission = 0.1
slippage = 0.0
```

---

## 3. Complete `config.toml` example

```/dev/null/config-reference-full.toml#L1-38
# MLFX Configuration
# This file is read automatically by the `mlfx` CLI.
# Adjust these defaults to match your workflow.

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
atr_period   = 14
atr_mult     = 0.5

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
slippage        = 0.0
```

---

## 4. CLI flag reference

## 4.1. Shared flags

The main commands support:

| Flag | Description |
|---|---|
| `--help` | Show command help |
| `--version` | Show the current version |

---

## 4.2. `download`

| Flag | Default | Description |
|---|---|---|
| `--symbol` | from config | Instrument symbol |
| `--asset-class` | from config | Asset class |
| `--start-year` | from config | Start year |
| `--start-month` | from config | Start month |
| `--end-year` | current year | End year |
| `--end-month` | current month | End month |
| `--concurrency` | from config | Number of parallel workers |
| `--force` | `false` | Re-download existing months |
| `--skip-current-month` | `false` | Skip current-month checking |

---

## 4.3. `pipeline`

| Flag | Default | Description |
|---|---|---|
| `--symbol` | from config | Symbol to process |
| `--tf` | from config | Timeframe, can accept multiple values |
| `--pivot` | from config | Pivot calculation method |
| `--anchor` | from config | Pivot anchor period |
| `--atr-period` | from config | ATR period |
| `--atr-mult` | from config | ATR multiplier used for labels |
| `--force` | `false` | Overwrite existing files |
| `--skip-resample` | `false` | Skip OHLCV generation |
| `--skip-features` | `false` | Skip feature engineering |
| `--skip-labels` | `false` | Skip label generation |

---

## 4.4. `train`

| Flag | Default | Description |
|---|---|---|
| `--symbol` | from config | Symbol to train on |
| `--tf` | from config | Timeframe |
| `--label` | from config | Label column |
| `--backend` | from config | Training backend |
| `--n-trials` | from config | Number of hyperparameter trials |
| `--n-splits` | from config | Number of cross-validation folds |
| `--force` | `false` | Retrain even if artifacts already exist |

---

## 4.5. `evaluate`

| Flag | Default | Description |
|---|---|---|
| `--symbol` | from config | Symbol to evaluate |
| `--tf` | from config | Timeframe |
| `--label` | from config | Signal column |
| `--capital` | from config | Initial capital |
| `--risk` | from config | Risk percentage per trade |
| `--commission` | from config | Commission per trade |
| `--tp` | from config | Take-profit in `R` |
| `--sl` | from config | Stop-loss in `R` |
| `--slippage` | from config | Simulated slippage |
| `--use-labels` | `false` | Backtest labels directly, skipping the model |

---

## 4.6. `serve`

| Flag | Default | Description |
|---|---|---|
| `--port` | `8000` | Port used by the inference API |

---

## 4.7. `batch-predict`

| Flag | Default | Description |
|---|---|---|
| `--symbol` | from config | Symbol to predict |
| `--tf` | from config | Timeframe |
| `--label` | from config | Label column associated with the model |

---

## 4.8. `drift`

| Flag | Default | Description |
|---|---|---|
| `--symbol` | from config | Symbol to inspect for drift |
| `--tf` | from config | Timeframe |
| `--threshold-ks` | `0.1` | KS-test threshold |
| `--threshold-psi` | `0.2` | PSI threshold |

---

## 4.9. `models`

| Flag | Default | Description |
|---|---|---|
| `--symbol` | none | Filter by symbol |
| `--tf` | none | Filter by timeframe |

---

## 5. Configuration precedence

Priority order from highest to lowest:

1. Values passed directly on the command line
2. Values in `config.toml`
3. Built-in program defaults

Example:

- In `config.toml`, `timeframe = "1H"`
- But you run:
  - `pixi run mlfx pipeline --symbol XAUUSD --tf 4H`

Then the effective timeframe used at runtime will be `4H`.

---

## 6. Things to remember when changing configuration

### 6.1. When should you edit the file?

Edit `config.toml` when:

- you repeat the same workflow frequently
- you want to define sensible defaults for yourself or your team
- you want to reduce the length of commands you must type

### 6.2. When should you override on the CLI?

Override with CLI flags when:

- you are running a quick experiment
- you want to compare multiple variants
- you are debugging and want explicit control over the values in use

### 6.3. Common mistakes

- Forgetting that CLI values override file-based values
- Editing `config.toml` but not actually running the command you think you are testing
- Using the wrong `label_col`
- Using the wrong `timeframe`
- Picking a backend that does not match the goal of the experiment

---

## 7. Recommended starter configuration

If you are just getting started, this is a safe and easy set of values:

- `symbol = "XAUUSD"`
- `timeframe = "1H"`
- `label_col = "label_10"`
- `backend = "mlf"`
- `pivot_type = "traditional"`
- `pivot_anchor = "daily"`
- `tp_r = 1.5`
- `sl_r = 1.0`

Why:

- `XAUUSD` is the most familiar dataset in the current repository
- `1H` is lighter than very small timeframes
- `mlf` is the most practical backend to start with
- `label_10` is a reasonable middle-ground target for a first run

---

## 8. Configuration examples by goal

### 8.1. Fast first run

```/dev/null/config-reference-starter.toml#L1-9
[download]
symbol = "XAUUSD"
asset_class = "fx"
start_year = 2024

[pipeline]
timeframe = "1H"

[train]
backend = "mlf"
label_col = "label_10"
```

### 8.2. Multi-model comparison

```/dev/null/config-reference-benchmark.toml#L1-8
[train]
symbol = "XAUUSD"
timeframe = "1H"
label_col = "label_10"
backend = "mlf"
n_trials = 15
n_splits = 5
```

### 8.3. Larger timeframe experiments

```/dev/null/config-reference-higher-tf.toml#L1-4
[pipeline]
symbol = "XAUUSD"
timeframe = "4H"
```

---

## 9. Post-change checklist

After changing `config.toml`, check:

- whether the values were placed in the correct section
- whether key names are spelled correctly
- whether value types are correct
- if needed, run:
  - `pixi run mlfx --help`
  - `pixi run mlfx pipeline --help`
- if you suspect the config is not being applied as expected, pass the value explicitly on the CLI and compare

---

## 10. See Also

- [Quickstart](../getting-started/QUICKSTART.md)
- [Configuration and Usage Guide](../guides/USAGE_GUIDE.md)
- [Evaluation Guide](../guides/EVALUATION_GUIDE.md)
- [Feature Reference](FEATURE_REFERENCE.md)
- [Architecture](../architecture/ARCHITECTURE.md)
