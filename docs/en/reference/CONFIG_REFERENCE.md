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

```toml
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
| `tf` | string | `"1H"` | `--tf` | Target timeframe |
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

```toml
[pipeline]
symbol = "XAUUSD"
tf = "1H"
pivot_type = "traditional"
pivot_anchor = "daily"
atr_mult = 0.5
```

---

## 2.3. `[train]` — Training configuration

| Key | Type | Default | Corresponding CLI flag | Description |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Instrument symbol used for training |
| `tf` | string | `"1H"` | `--tf` | Training timeframe |
| `label` | string | `"label_10"` | `--label` | Target label column |
| `backend` | string | `"mlf"` | `--backend` | Training backend |
| `n_trials` | integer | `30` | `--n-trials` | Number of hyperparameter trials, mainly for `mlf` |
| `n_splits` | integer | `5` | `--n-splits` | Number of cross-validation folds |
| `random_seed` | integer | `42` | — | Random seed for reproducibility |
| `train_start` | string | `null` | `--train-start` | Inclusive training start date (YYYYMMDD format) |
| `train_end` | string | `null` | `--train-end` | Inclusive training end date (YYYYMMDD format) |
| `force` | boolean | `false` | `--force` | Force retrain even if model exists |

### Supported backends

- `mlf`
- `lstm`
- `sgd`
- `stats`

### Supported labels

- `label_5`
- `label_10`
- `label_20`

### Example

```toml
[train]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
backend = "mlf"
n_trials = 15
n_splits = 5
train_start = "20240101"
train_end = "20241231"
```

---

## 2.4. `[benchmark]` — Multi-backend comparison

| Key | Type | Default | Corresponding CLI flag | Description |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Instrument symbol |
| `tf` | string | `"1H"` | `--tf` | Timeframe |
| `label` | string | `"label_10"` | `--label` | Target label column |
| `backends` | list | `["mlf", "sgd", "stats"]` | `--backends` | List of backends to compare |
| `n_trials` | integer | `5` | `--n-trials` | Number of hyperparameter trials per backend |
| `n_splits` | integer | `3` | `--n-splits` | Number of cross-validation folds |
| `train_start` | string | `null` | `--train-start` | Inclusive training start date (YYYYMMDD format) |
| `train_end` | string | `null` | `--train-end` | Inclusive training end date (YYYYMMDD format) |
| `force` | boolean | `false` | `--force` | Force retrain all backends |

### Example

```toml
[benchmark]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
backends = ["mlf", "lstm", "sgd", "stats"]
n_trials = 10
n_splits = 5
```

---

## 2.5. `[features]` — Feature-engineering configuration

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

## 2.6. `[qa]` — Quality assurance audit

| Key | Type | Default | Corresponding CLI flag | Description |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Instrument symbol to audit |
| `asset_class` | string | `"fx"` | `--asset-class` | Asset class: `"fx"`, `"crypto"` |

### Example

```toml
[qa]
symbol = "XAUUSD"
asset_class = "fx"
```

---

## 2.7. `[serve]` — FastAPI inference server

| Key | Type | Default | Corresponding CLI flag | Description |
|---|---|---|---|---|
| `host` | string | `"0.0.0.0"` | `--host` | Bind address for the API server |
| `port` | integer | `8000` | `--port` | Port for the API server |
| `reload` | boolean | `false` | `--reload` | Enable auto-reload for development |

### Example

```toml
[serve]
host = "0.0.0.0"
port = 8000
reload = false
```

---

## 2.8. `[batch_predict]` — Batch inference configuration

| Key | Type | Default | Corresponding CLI flag | Description |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Instrument symbol |
| `tf` | string | `"1H"` | `--tf` | Timeframe |
| `label` | string | `"label_10"` | `--label` | Label column associated with the model |

### Example

```toml
[batch_predict]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
```

---

## 2.9. `[drift]` — Feature drift detection

| Key | Type | Default | Corresponding CLI flag | Description |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Instrument symbol |
| `tf` | string | `"1H"` | `--tf` | Timeframe |
| `label` | string | `"label_10"` | `--label` | Label column |
| `threshold_ks` | float | `0.1` | `--threshold-ks` | Kolmogorov-Smirnov test threshold |
| `threshold_psi` | float | `0.2` | `--threshold-psi` | Population Stability Index threshold |
| `min_samples` | integer | `30` | `--min-samples` | Minimum samples per feature for drift tests |

### Example

```toml
[drift]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
threshold_ks = 0.1
threshold_psi = 0.2
min_samples = 30
```

---

## 2.10. `[backtest]` — Evaluation and trade simulation

| Key | Type | Default | Corresponding CLI flag | Description |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Instrument symbol to evaluate |
| `tf` | string | `"1H"` | `--tf` | Backtest timeframe |
| `label` | string | `"label_10"` | `--label` | Signal column used for backtesting |
| `tp_r` | float | `1.5` | `--tp` | Take-profit in `R` |
| `sl_r` | float | `1.0` | `--sl` | Stop-loss in `R` |
| `initial_capital` | float | `10000.0` | `--capital` | Initial capital |
| `risk_pct` | float | `1.0` | `--risk` | Percentage of capital risked per trade |
| `commission` | float | `0.1` | `--commission` | Commission cost per trade |
| `slippage` | float | `0.0` | `--slippage` | Simulated slippage |
| `eval_start` | string | `null` | `--eval-start` | Inclusive evaluation start date (YYYYMMDD format) |
| `eval_end` | string | `null` | `--eval-end` | Inclusive evaluation end date (YYYYMMDD format) |
| `use_labels` | boolean | `false` | `--use-labels` | Backtest labels directly, skip model |

### Example

```toml
[backtest]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
tp_r = 1.5
sl_r = 1.0
initial_capital = 10000.0
risk_pct = 1.0
commission = 0.1
slippage = 0.0
eval_start = "20250101"
eval_end = "20250331"
```

---

## 2.11. `[profiles]` — Workflow profiles

Workflow profiles allow you to define preset configurations for train, evaluate, and benchmark commands. Each profile can contain subsections for each command type.

### Profile structure

```toml
[profiles.{name}.train]      # Training presets
[profiles.{name}.evaluate]   # Evaluation presets
[profiles.{name}.benchmark]  # Benchmark presets
```

### Profile train section

| Key | Type | Description |
|---|---|---|
| `symbol` | string | Instrument symbol |
| `tf` | string | Timeframe |
| `label` | string | Target label column |
| `backend` | string | Training backend |
| `n_trials` | integer | Number of hyperparameter trials |
| `n_splits` | integer | Number of cross-validation folds |
| `train_start` | string | Training start date (YYYYMMDD) |
| `train_end` | string | Training end date (YYYYMMDD) |

### Profile evaluate section

| Key | Type | Description |
|---|---|---|
| `symbol` | string | Instrument symbol |
| `tf` | string | Timeframe |
| `label` | string | Signal column |
| `tp_r` | float | Take-profit in R |
| `sl_r` | float | Stop-loss in R |
| `initial_capital` | float | Initial capital |
| `risk_pct` | float | Risk percentage per trade |
| `commission` | float | Commission per trade |
| `slippage` | float | Simulated slippage |
| `eval_start` | string | Evaluation start date (YYYYMMDD) |
| `eval_end` | string | Evaluation end date (YYYYMMDD) |

### Profile benchmark section

| Key | Type | Description |
|---|---|---|
| `symbol` | string | Instrument symbol |
| `tf` | string | Timeframe |
| `label` | string | Target label column |
| `backends` | list | List of backends to compare |
| `n_trials` | integer | Trials per backend |
| `n_splits` | integer | Cross-validation folds |
| `train_start` | string | Training start date (YYYYMMDD) |
| `train_end` | string | Training end date (YYYYMMDD) |

### Example

```toml
[profiles.research.train]
symbol      = "XAUUSD"
tf          = "1H"
label       = "label_10"
backend     = "mlf"
train_start = "20240101"
train_end   = "20241231"
n_trials    = 5
n_splits    = 3

[profiles.research.evaluate]
symbol          = "XAUUSD"
tf              = "1H"
label           = "label_10"
eval_start      = "20250101"
eval_end        = "20250331"
tp_r            = 1.5
sl_r            = 1.0
initial_capital = 10000.0
risk_pct        = 1.0
commission      = 0.1
slippage        = 0.0

[profiles.research.benchmark]
symbol      = "XAUUSD"
tf          = "1H"
label       = "label_10"
backends    = ["mlf", "sgd", "stats"]
train_start = "20240101"
train_end   = "20241231"
n_trials    = 5
n_splits    = 3

[profiles.benchmark_fast.benchmark]
symbol      = "XAUUSD"
tf          = "1H"
label       = "label_10"
backends    = ["mlf", "sgd", "stats"]
train_start = "20230101"
train_end   = "20241231"
n_trials    = 5
n_splits    = 3
```

### Using profiles

```bash
# Train using a profile
pixi run mlfx train --profile research

# Evaluate using a profile
pixi run mlfx evaluate --profile research

# Benchmark using a profile
pixi run mlfx benchmark --profile benchmark_fast

# Run train + evaluate from a profile
pixi run mlfx run-profile --profile research
```

---

## 3. Complete `config.toml` example

```toml
# MLFX Configuration
# This file is read automatically by the `mlfx` CLI.
# Adjust these defaults to match your workflow.

[download]
symbol             = "XAUUSD"
asset_class        = "fx"
start_year         = 2015
start_month        = 1
concurrency        = 20
force              = true
skip_current_month = false

[pipeline]
symbol        = "XAUUSD"
tf            = ["1H"]
pivot_type    = "traditional"
pivot_anchor  = "daily"
atr_mult      = 0.5
force         = true
skip_resample = false
skip_features = false
skip_labels   = false

[train]
symbol      = "XAUUSD"
tf          = "1H"
label       = "label_10"
backend     = "mlf"
n_trials    = 30
n_splits    = 5
random_seed = 42
force       = false

[benchmark]
symbol   = "XAUUSD"
tf       = "1H"
label    = "label_10"
backends = ["mlf", "sgd", "stats"]
n_trials = 5
n_splits = 3
force    = false

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
tf              = "1H"
label           = "label_10"
tp_r            = 1.5
sl_r            = 1.0
initial_capital = 10000.0
risk_pct        = 1.0
commission      = 0.1
slippage        = 0.0
use_labels      = false

[qa]
symbol      = "XAUUSD"
asset_class = "fx"

[serve]
host   = "0.0.0.0"
port   = 8000
reload = false

[batch_predict]
symbol = "XAUUSD"
tf     = "1H"
label  = "label_10"

[drift]
symbol       = "XAUUSD"
tf           = "1H"
label        = "label_10"
threshold_ks = 0.1
threshold_psi = 0.2
min_samples  = 30

# Workflow profiles
[profiles.research.train]
symbol      = "XAUUSD"
tf          = "1H"
label       = "label_10"
backend     = "mlf"
train_start = "20240101"
train_end   = "20241231"
n_trials    = 5
n_splits    = 3

[profiles.research.evaluate]
symbol          = "XAUUSD"
tf              = "1H"
label           = "label_10"
eval_start      = "20250101"
eval_end        = "20250331"
tp_r            = 1.5
sl_r            = 1.0
initial_capital = 10000.0
risk_pct        = 1.0
commission      = 0.1
slippage        = 0.0

[profiles.research.benchmark]
symbol      = "XAUUSD"
tf          = "1H"
label       = "label_10"
backends    = ["mlf", "sgd", "stats"]
train_start = "20240101"
train_end   = "20241231"
n_trials    = 5
n_splits    = 3
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
| `--train-start` | from config | Inclusive training start date (YYYYMMDD) |
| `--train-end` | from config | Inclusive training end date (YYYYMMDD) |
| `--profile` | none | Load train defaults from a named profile |
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
| `--eval-start` | from config | Inclusive evaluation start date (YYYYMMDD) |
| `--eval-end` | from config | Inclusive evaluation end date (YYYYMMDD) |
| `--profile` | none | Load evaluation defaults from a named profile |
| `--use-labels` | `false` | Backtest labels directly, skipping the model |

---

## 4.6. `benchmark`

| Flag | Default | Description |
|---|---|---|
| `--symbol` | from config | Symbol to benchmark |
| `--tf` | from config | Timeframe |
| `--label` | from config | Label column |
| `--backends` | from config | List of backends to compare |
| `--n-trials` | from config | Number of hyperparameter trials per backend |
| `--n-splits` | from config | Number of cross-validation folds |
| `--train-start` | from config | Inclusive training start date (YYYYMMDD) |
| `--train-end` | from config | Inclusive training end date (YYYYMMDD) |
| `--profile` | none | Load benchmark defaults from a named profile |
| `--force` | `false` | Force retrain all backends |

---

## 4.7. `serve`

| Flag | Default | Description |
|---|---|---|
| `--host` | from config | Bind address for the API server |
| `--port` | from config | Port used by the inference API |
| `--reload` | from config | Enable auto-reload for development |

---

## 4.8. `batch-predict`

| Flag | Default | Description |
|---|---|---|
| `--symbol` | from config | Symbol to predict |
| `--tf` | from config | Timeframe |
| `--label` | from config | Label column associated with the model |

---

## 4.9. `drift`

| Flag | Default | Description |
|---|---|---|
| `--symbol` | from config | Symbol to inspect for drift |
| `--tf` | from config | Timeframe |
| `--label` | from config | Label column |
| `--threshold-ks` | from config | KS-test threshold |
| `--threshold-psi` | from config | PSI threshold |
| `--min-samples` | from config | Minimum samples per feature for drift tests |

---

## 4.10. `drift-retrain`

| Flag | Default | Description |
|---|---|---|
| `--symbol` | from config | Symbol |
| `--tf` | from config | Timeframe |
| `--label` | from config | Label column |
| `--backend` | from config | Training backend |
| `--n-trials` | from config | Number of hyperparameter trials |
| `--n-splits` | from config | Number of cross-validation folds |
| `--train-start` | from config | Inclusive training start date (YYYYMMDD) |
| `--train-end` | from config | Inclusive training end date (YYYYMMDD) |
| `--profile` | none | Load train defaults from a named profile |
| `--force` | `false` | Force retrain if drift is detected |
| `--threshold-ks` | from config | KS-test threshold |
| `--threshold-psi` | from config | PSI threshold |
| `--min-samples` | from config | Minimum samples per feature for drift tests |

---

## 4.11. `models`

| Flag | Default | Description |
|---|---|---|
| `--symbol` | none | Filter by symbol |
| `--tf` | none | Filter by timeframe |
| `--backend` | none | Filter by backend |

---

## 4.12. `profiles`

| Flag | Default | Description |
|---|---|---|
| `--profile` | none | Show details for a specific profile |

---

## 4.13. `run-profile`

| Flag | Default | Description |
|---|---|---|
| `--profile` | required | Workflow profile name to execute |
| `--skip-train` | `false` | Skip the training step |
| `--skip-evaluate` | `false` | Skip the evaluation step |
| `--skip-benchmark` | `false` | Skip the benchmark step |
| `--json` | `false` | Print a JSON summary of the run |

---

## 4.14. `run-all`

| Flag | Default | Description |
|---|---|---|
| `--profile` | none | Use a workflow profile for train/evaluate/benchmark defaults |
| `--skip-download` | `false` | Skip download stage |
| `--skip-qa` | `false` | Skip QA stage |
| `--skip-pipeline` | `false` | Skip pipeline stage |
| `--skip-train` | `false` | Skip train stage |
| `--skip-evaluate` | `false` | Skip evaluate stage |
| `--skip-benchmark` | `false` | Skip benchmark stage |
| `--skip-serve` | `false` | Skip serve placeholder stage |
| `--skip-batch` | `false` | Skip batch prediction stage |
| `--skip-drift-retrain` | `false` | Skip drift detection and retraining stages |
| `--continue-on-error` | `false` | Continue remaining stages after an error |
| `--json` | `false` | Print a JSON summary of run-all stage outputs |

---

## 5. Configuration precedence

Priority order from highest to lowest:

1. Values passed directly on the command line
2. Values in `config.toml`
3. Built-in program defaults

Example:

- In `config.toml`, `tf = "1H"`
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
- Using the wrong `label`
- Using the wrong `tf`
- Picking a backend that does not match the goal of the experiment

---

## 7. Recommended starter configuration

If you are just getting started, this is a safe and easy set of values:

- `symbol = "XAUUSD"`
- `tf = "1H"`
- `label = "label_10"`
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

```toml
[download]
symbol = "XAUUSD"
asset_class = "fx"
start_year = 2024

[pipeline]
tf = "1H"

[train]
backend = "mlf"
label = "label_10"
```

### 8.2. Multi-model comparison

```toml
[train]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
backend = "mlf"
n_trials = 15
n_splits = 5
```

### 8.3. Larger timeframe experiments

```toml
[pipeline]
symbol = "XAUUSD"
tf = "4H"
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
