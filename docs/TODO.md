# TODO — ML_FX Development Plan

Detailed development plan, deriving architectures from [cryage-demo](../../../cryage-demo).

**Legend:** `[ ]` Not Started · `[/]` In Progress · `[x]` Completed

---

## Phase 1 — Data Collection ✅

- [x] Download tick XAUUSD from Dukascopy (`download_data.py`)
  - [x] Async aiohttp — 20 concurrent connections
  - [x] Parse `.bi5` binary → Polars DataFrame
  - [x] Save Parquet per month into `data/raw/XAUUSD/`
  - [x] State management via `completed_months.json` (migrated from `.complete`)
  - [x] Auto-detect + repair missing hours

- [x] Data Quality Assurance (`pipeline/qa_data.py`)
  - [x] Detect significant gaps and unexpected missing hours
  - [x] Identify NaN values, negative prices, and negative spread outliers
  - [x] Generate automated Markdown Quality Report (`{symbol}_Data_Quality_Report.md`)

---

## Phase 2 — Feature Engineering ✅

- [x] **ICT Killzone** — `indicators/killzone.py`
  - [x] `add_session_flags()` — 5 boolean session flags
  - [x] `compute_killzone_pivots()` — session High/Low/Mid/Range via cum_max/min
  - [x] `compute_killzone_avg_range()` — rolling N-session avg range
  - [x] `compute_dwm_levels()` — Day/Week/Month open + prev H/L
  - [x] `add_killzone_features()` — aggregated pipeline

- [x] **Support/Resistance + Pivot Points** — `indicators/sr_pp.py`
  - [x] `detect_sr_patterns()` — pattern r/r2/s/s2 with de-duplication
  - [x] `compute_sr_zones()` — zone tracking + role reversal
  - [x] `compute_pivot_points()` — 6 types × 5 anchor TF via asof_join
  - [x] `add_sr_pp_features()` — aggregated pipeline

---

## Phase 3 — ETL Pipeline ✅

- [x] **Resample tick → OHLCV** — `pipeline/resample.py`
  - [x] Mid price: `(ask + bid) / 2`
  - [x] Support TF: `1m`, `5m`, `15m`, `1H`, `4H`, `1D`
  - [x] Handle gaps (weekend, market close) — `detect_gaps()`
  - [x] Save to `data/ohlcv/{symbol}/{tf}/`

- [x] **Feature pipeline** — `pipeline/features.py`
  - [x] Call `add_killzone_features()` + `add_sr_pp_features()`
  - [x] Add TA-Lib: RSI(14), MACD, ATR(14), EMA(20/50/200)
  - [x] Add **Order Blocks** — `add_order_blocks()`
  - [x] Add **Fair Value Gaps** — `add_fair_value_gaps()`
  - [x] Normalize + scale features — ATR-normalized distances
  - [x] Save to `data/features/{symbol}/{tf}/`

> **Learned from cryage-demo**: separate `indicator_calculation.py` and `ohlcv_ingestion.py` into distinct pipelines.

---

## Phase 4 — Labeling & Training ✅

- [x] **Labeling** — `pipeline/labels.py`
  - [x] Target: price direction after N candles (N = 5, 10, 20)
  - [x] Classes: LONG (+1), SHORT (−1), NEUTRAL (0)
  - [x] ATR-based threshold to avoid label noise
  - [x] Class balance check + stratified split

- [x] **Baseline — KNN** — `models/knn.py`
  - [x] TimeSeriesSplit cross-validation
  - [x] Save model + metrics

- [x] **XGBoost / LightGBM** — `models/gradient_boost.py`
  - [x] Feature importance + SHAP values
  - [x] Optuna hyperparameter tuning

- [x] **LSTM** — `models/lstm.py`
  - [x] Sequence length 50–200 bars
  - [x] PyTorch — LSTM → Dropout → Dense

---

## Phase 5 — Evaluation & Visualization ✅

- [x] **Backtesting** — `eval/backtest.py`
  - [x] Walk-forward validation
  - [x] Metrics: Sharpe, max drawdown, win rate, R:R

- [x] **Visualization** — `viz/charts.py`
  - [x] Candlestick chart + S/R overlay + killzone (Plotly)
  - [x] LONG/SHORT/NEUTRAL signal markers
  - [x] Equity curve + drawdown (Matplotlib)
  - [x] Feature importance heatmap (Seaborn)

---

## Phase 6 — AI Agent (Agno 6-Step) 📋

> **Architecture learned from cryage-demo** — 6-step Agno implementation:

### Step 1 — LLM Provider
- [ ] `agent/agent.py` — use `LMStudio(id=model_id)` as local LLM
  - [ ] Fallback to OpenAI if LMStudio is unavailable

### Step 2 — ReasoningTools
- [ ] Add `ReasoningTools(add_instructions=True)` to agent
  - [ ] Reduce hallucination, step-by-step reasoning for agent

### Step 3 — Knowledge + ChromaDB (RAG)
- [ ] `agent/knowledge.py` — build `Knowledge` object
  - [ ] ChromaDB collection `"ml_fx_patterns"` — store signal history + outcomes
  - [ ] PatternService writes, agent reads via `search_knowledge_base`

### Step 4 — Toolkit (Tools)
- [ ] `agent/toolkit.py` — subclass `agno.tools.Toolkit`

  **Killzone tools** (using `indicator.killzone`):
  - [ ] `get_killzone_status()` — calls `add_session_flags()`, returns current session
    - Output: `{in_asia, in_london, in_nyam, in_nylunch, in_nypm}` + active session name
  - [ ] `get_killzone_levels(symbol, timeframe)` — calls `compute_killzone_pivots()`
    - Output: `kz_{name}_high/low/mid/range` for each session
  - [ ] `get_killzone_avg_range(symbol, timeframe, n=5)` — calls `compute_killzone_avg_range()`
    - Output: `kz_{name}_avg_range` — average range of N sessions
  - [ ] `get_dwm_levels(symbol)` — calls `compute_dwm_levels()`
    - Output: `d_open/high/low`, `w_open/high/low`, `m_open/high/low`, `pd_high/low`, `pw_high/low`, `pm_high/low`

  **S/R + Pivot tools** (using `indicator.sr_pp`):
  - [ ] `get_sr_zones(symbol, timeframe)` — calls `detect_sr_patterns()` + `compute_sr_zones()`
    - Output: `nearest_resist_high/low`, `nearest_support_high/low`, `in_resist_zone`, `in_support_zone`, `sr_role_reversal`
  - [ ] `get_pivot_levels(symbol, timeframe, pivot_type="traditional", anchor="daily")` — calls `compute_pivot_points()`
    - Output: `pp_p`, `pp_r1..r5`, `pp_s1..s5`, `pp_dist_to_p/r1/s1`, `pp_above_p`
  - [ ] `get_sr_patterns(symbol, timeframe)` — calls `detect_sr_patterns()`
    - Output: `sr_resist_1bar`, `sr_resist_2bar`, `sr_support_1bar`, `sr_support_2bar`

  **ML + data tools**:
  - [ ] `get_ohlcv(symbol, timeframe, limit=200)` — load + resample from Parquet
  - [ ] `get_ml_signal(symbol, timeframe)` — run full feature pipeline + trained model
    - Output: `{action: LONG/SHORT/NEUTRAL, confidence: 0–100, features_snapshot}`

### Step 5 — LearningMachine (Self-learning)
- [ ] `agent/learning.py` — build `LearningMachine`
  - [ ] ChromaDB collection `"ml_fx_learnings"` (separated from patterns)
  - [ ] `LearningMode.AGENTIC` — agent decides what to learn
  - [ ] Agent learns from the results of previous signals

### Step 6 — Skills (Domain Knowledge)

- [ ] `agent/skills/ict-analysis/SKILL.md`

  **ICT Killzone** (from `killzone.py`):
  - Prioritize signals inside killzone: `in_london=True` or `in_nyam=True`
  - Killzone pivot: use `kz_{name}_high/low` as key S/R — wait for retest before entering
  - `kz_{name}_avg_range`: if `kz_range < avg_range * 0.5` → session not fully open, wait
  - DWM levels: `pd_high/low` (PDH/PDL) are core ICT key levels; `pw_high/low` for weekly bias
  - Outside killzone and signal not very strong (confidence < 85%) → HOLD

  **S/R + Pivot** (from `sr_pp.py`):
  - Pattern `sr_resist_1bar / sr_support_1bar`: confirms earlier than 2-bar
  - `sr_role_reversal = +1`: resistance became support → look for BUY when pulling back to zone
  - `sr_role_reversal = -1`: support became resistance → look for SELL when pushing up
  - `in_resist_zone / in_support_zone`: price is in zone → high entry risk, wait for breakout
  - `dist_to_nearest_resist/support`: the smaller, the closer to the test level
  - Pivot P: daily neutral threshold; `pp_above_p=True` → bullish bias
  - R1/S1: standard TP1 targets; R2/S2: aggressive TP2 targets
  - Camarilla R3/S3: strong reversal — if price reaches here → use as tight SL

  **Confidence scoring**:
  - 1 conformance layer → 30–45% → HOLD
  - 2 layers + active killzone → 55–65% → weak signal
  - 3+ layers + killzone + S/R confluence → 70–85% → strong signal
  - All layers (momentum + trend + structure + context) → 85–95% → very strong

- [ ] `agent/skills/risk-management/SKILL.md`
  - Max risk: 1% portfolio / trade; no more than 3 simultaneous open positions
  - SL BUY: below `nearest_support_low` or `pp_s1`, max 3% from entry
  - SL SELL: above `nearest_resist_high` or `pp_r1`, max 3% from entry
  - TP1 BUY: `pp_r1`; TP2: `pp_r2`; minimum R:R of 1:2
  - TP1 SELL: `pp_s1`; TP2: `pp_s2`; minimum R:R of 1:2
  - Position size by confidence: 60–69% → 0.5%; 70–79% → 0.75%; 80%+ → 1%
  - Red flags → skip trade: outside killzone (mandatory rule unless confidence > 85%),
    `in_resist_zone / in_support_zone = True`, conflicting MTF (1H vs 4H)

### Decision Engine
- [ ] `agent/decision_engine.py` — safety gate
  - [ ] **LLM mode**: `agent.run(prompt, output_schema=TradingDecision)` — Agno validates
  - [ ] **Heuristic mode**: rule-based fallback when LLM is unavailable
  - [ ] Dataclass `Decision(action, pair, confidence, stop_loss, take_profit, source)`
  - [ ] `should_execute(decision)` — gate: confidence ≥ 60% and action ≠ HOLD
  - [ ] `SqliteDb("ml_fx_sessions.db")` — store chat history

### System Prompt
- [ ] Analyze 4 layers (learned from cryage):
  1. **Momentum** — RSI, MACD, Stochastic
  2. **Trend** — EMA alignment, killzone highs/lows
  3. **Structure** — S/R zones, Pivot P/R1/S1
  4. **Context** — killzone session, MTF confluence
- [ ] Confidence gate: < 60% → HOLD regardless of signals

---

## Phase 7 — Expansion 📋

- [ ] Multi-symbol: EURUSD, GBPUSD, BTCUSD, ETHUSD
- [ ] Multi-timeframe confluence: MTF signal alignment
- [ ] Auto-retraining pipeline (monthly trigger)
- [ ] Monitoring dashboard (Plotly Dash)
- [ ] Paper trading integration

---

## Target Directory Architecture

```
ML_FX/
├── indicators/          # Feature engineering (done ✅)
│   ├── killzone.py
│   ├── sr_pp.py
│   └── __init__.py
├── pipeline/           # ETL + labeling
│   ├── download_data.py
│   ├── qa_data.py      # Quality assurance reporter
│   ├── resample.py
│   ├── features.py
│   └── labels.py
├── models/             # ML models
│   ├── knn.py
│   ├── gradient_boost.py
│   └── lstm.py
├── eval/               # Backtesting & Reports
│   ├── run_eval.py
│   └── backtest.py
├── viz/                # Visualization
│   └── charts.py
├── agent/              # Agno agent (cryage pattern)
│   ├── agent.py        # create_agent() — 6 steps
│   ├── toolkit.py      # FXToolkit(Toolkit)
│   ├── decision_engine.py
│   ├── knowledge.py
│   ├── learning.py
│   └── skills/
│       ├── ict-analysis/SKILL.md
│       └── risk-management/SKILL.md
├── outputs/            # Generated assets
│   ├── reports/        # Backtest reports, heatmaps
│   └── models/         # Saved model .joblib, .pt, .json files, SHAP plots
├── data/
│   ├── raw/            # Tick Parquet ✅
│   │   ├── XAUUSD/     
│   │   └── BTCUSD/     
│   ├── ohlcv/          # Resampled OHLCV
│   ├── features/       # Feature DataFrames
│   └── labels/         # Labeled datasets
└── docs/               # Documentation system 
    ├── NOOB_GUIDE.md          
    ├── USAGE_GUIDE.md         
    ├── TROUBLESHOOTING.md     
    ├── GLOSSARY.md            
    └── TODO.md         # This file
```

---

## Technical Notes

| Component       | Decision              | Reason                                   |
| --------------- | --------------------- | ---------------------------------------- |
| DataFrame       | **Polars**            | 10–100× faster than Pandas               |
| Serialization   | **Parquet** (PyArrow) | Columnar, compressed                     |
| Agent framework | **Agno**              | Native LMStudio, Skills, LearningMachine |
| LLM             | **LM Studio** (local) | Free, offline, OpenAI compatible         |
| Vector DB       | **ChromaDB**          | Native integration with Agno Knowledge   |
| Session DB      | **SQLiteDb**          | Store agent chat history                 |
| Env manager     | **Pixi**              | conda-forge + pypi hybrid                |

---

## 🧭 Skill Usage Guide by Phase

> At the start of each phase, the AI agent reads the corresponding skills before generating code.
> Reference syntax: `@skill:<skill-name>` → read `SKILL.md` + related resources.

---

### Phase 1 — Data Collection ✅  
> _Phase completed. Skills used for maintenance or pipeline expansion._

| Skill                      | Resource to read      | Apply to                                       |
| -------------------------- | --------------------- | ---------------------------------------------- |
| `@skill:aiohttp-async`     | `aiohttp-playbook.md` | Fix/expand `download_data.py`                  |
| `@skill:aiohttp-async`     | `combined-usecase.md` | Add new data source (retry pattern, semaphore) |
| `@skill:polars-dataframes` | `pyarrow-playbook.md` | Write Parquet by month, schema enforcement     |

**Checklist when using skills:**
- [ ] Read `aiohttp-playbook.md` → "Bounded Concurrency" section to calibrate `MAX_CONC`
- [ ] Read `pyarrow-playbook.md` → "Writing Partitioned Parquet" section to maintain schema consistency

---

### Phase 2 — Feature Engineering ✅  
> _Phase completed. Skills used when adding new indicators._

| Skill                      | Resource to read      | Apply to                                         |
| -------------------------- | --------------------- | ------------------------------------------------ |
| `@skill:polars-dataframes` | `polars-playbook.md`  | Write `with_columns`, rolling, join in indicator |
| `@skill:talib-indicators`  | `talib-playbook.md`   | Add candlestick pattern detection                |
| `@skill:talib-indicators`  | `combined-usecase.md` | Build feature vector from multi-indicator        |

**Checklist when using skills:**
- [ ] Read `polars-playbook.md` → "Expressions Over Python Loops" → **do not use `.apply()`**
- [ ] Read `talib-playbook.md` → "Lookback Alignment" → handle NaN before joining with OHLCV frame

---

### Phase 3 — ETL Pipeline 📋 ← **UP NEXT**

| Skill                       | Resource to read      | Apply to                                        |
| --------------------------- | --------------------- | ----------------------------------------------- |
| `@skill:polars-dataframes`  | `polars-playbook.md`  | `pipeline/resample.py` — `group_by_dynamic()`   |
| `@skill:polars-dataframes`  | `pyarrow-playbook.md` | Write OHLCV to `data/ohlcv/{symbol}/{tf}/`      |
| `@skill:polars-dataframes`  | `combined-usecase.md` | End-to-end: tick → OHLCV → validate → save      |
| `@skill:talib-indicators`   | `talib-playbook.md`   | `pipeline/features.py` — RSI, MACD, ATR, EMA    |
| `@skill:questdb-timeseries` | `questdb-playbook.md` | Save features to QuestDB instead of raw Parquet |

**Reading order of skills for Phase 3 implementation:**
```
1. polars-dataframes/resources/combined-usecase.md    ← overall blueprint
2. polars-dataframes/resources/polars-playbook.md     ← resample.py
3. polars-dataframes/resources/pyarrow-playbook.md    ← write partitioned Parquet
4. talib-indicators/resources/talib-playbook.md       ← features.py
5. talib-indicators/resources/combined-usecase.md     ← full feature matrix
```

**Files to create:**
- `pipeline/resample.py` → use `group_by_dynamic()` from polars-playbook
- `pipeline/features.py` → use `add_ta_column()` pattern from talib-playbook

---

### Phase 4 — Labeling & Training 📋

| Skill                      | Resource to read      | Apply to                                           |
| -------------------------- | --------------------- | -------------------------------------------------- |
| `@skill:polars-dataframes` | `polars-playbook.md`  | `pipeline/labels.py` — shift/lead to create target |
| `@skill:talib-indicators`  | `combined-usecase.md` | Use feature matrix as input for KNN/XGBoost        |
| `@skill:pytest-ml-fx`      | `pytest-playbook.md`  | Test labeling with parametrize edge cases          |
| `@skill:financial-charts`  | `seaborn-playbook.md` | Visualize class balance, feature correlation       |

**Reading order of skills for Phase 4 implementation:**
```
1. talib-indicators/resources/combined-usecase.md     ← understand feature matrix input
2. polars-dataframes/resources/polars-playbook.md     ← shift() to create label N-bar ahead
3. pytest-ml-fx/resources/pytest-playbook.md          ← test labels + model outputs
4. financial-charts/resources/seaborn-playbook.md     ← plot_indicator_correlation()
```

**Pattern labeling with Polars:**
```python
# In pipeline/labels.py
df = df.with_columns([
    pl.col("close").shift(-N).alias(f"close_ahead_{N}"),
]).with_columns([
    pl.when(pl.col(f"close_ahead_{N}") > pl.col("close") * (1 + atr_threshold))
      .then(pl.lit(1))   # LONG
      .when(pl.col(f"close_ahead_{N}") < pl.col("close") * (1 - atr_threshold))
      .then(pl.lit(-1))  # SHORT
      .otherwise(pl.lit(0))  # NEUTRAL
      .alias(f"label_{N}")
])
```

---

### Phase 5 — Evaluation & Visualization 📋

| Skill                       | Resource to read         | Apply to                                             |
| --------------------------- | ------------------------ | ---------------------------------------------------- |
| `@skill:financial-charts`   | `plotly-playbook.md`     | `viz/charts.py` — candlestick + S/R + signal markers |
| `@skill:financial-charts`   | `matplotlib-playbook.md` | Equity curve + drawdown panel                        |
| `@skill:financial-charts`   | `seaborn-playbook.md`    | Session heatmap, return distribution                 |
| `@skill:financial-charts`   | `combined-usecase.md`    | **Full backtest report in 1 script**                 |
| `@skill:questdb-timeseries` | `combined-usecase.md`    | Query walk-forward windows from QuestDB              |

**Reading order of skills for Phase 5 implementation:**
```
1. financial-charts/resources/combined-usecase.md     ← full backtest report template
2. financial-charts/resources/plotly-playbook.md      ← add_sr_overlays(), shade_killzones()
3. financial-charts/resources/matplotlib-playbook.md  ← plot_equity_curve()
4. financial-charts/resources/seaborn-playbook.md     ← plot_session_heatmap()
```

**Files to create:**
- `viz/charts.py` → copy pattern from `financial-charts/combined-usecase.md`
- `eval/backtest.py` → query from QuestDB (see `questdb-playbook.md` → "ASOF JOIN")

---

### Phase 6 — AI Agent (Agno 6-Step) 📋

> The most critical phase — each step corresponds to one or more skills.

#### Step 1 — LLM Provider (`agent/agent.py`)

| Skill                    | Resource to read       | Apply to                                  |
| ------------------------ | ---------------------- | ----------------------------------------- |
| `@skill:openai-lmstudio` | `lmstudio-playbook.md` | Config `LMStudio(id=model_id)` local      |
| `@skill:openai-lmstudio` | `openai-playbook.md`   | Fallback OpenAI async client              |
| `@skill:openai-lmstudio` | `combined-usecase.md`  | **Provider router** — route by complexity |

```
Read: openai-lmstudio/resources/combined-usecase.md → copy `routed_chat()` function
```

#### Step 2 — ReasoningTools

> `ReasoningTools` is Agno built-in — see `agno-playbook.md` section "Agent Setup".
```
Read: agno-agent/resources/agno-playbook.md → section "Agent Setup"
```

#### Step 3 — Knowledge + ChromaDB (`agent/knowledge.py`)

| Skill                    | Resource to read       | Apply to                                             |
| ------------------------ | ---------------------- | ---------------------------------------------------- |
| `@skill:chromadb-vector` | `chromadb-playbook.md` | Setup persistent client, collection `ml_fx_patterns` |
| `@skill:chromadb-vector` | `combined-usecase.md`  | Store signal + retrieve similar historical setups    |

```
Read: chromadb-vector/resources/chromadb-playbook.md → "Collection Management" + "Storing Trade Signals"
Read: chromadb-vector/resources/combined-usecase.md  → blueprint PatternService
```

#### Step 4 — Toolkit (`agent/toolkit.py`)

| Skill                       | Resource to read      | Apply to                                                   |
| --------------------------- | --------------------- | ---------------------------------------------------------- |
| `@skill:agno-agent`         | `agno-playbook.md`    | `@tool` decorator, async tool pattern, error handling      |
| `@skill:agno-agent`         | `combined-usecase.md` | **Full toolkit example** with killzone + S/R + OHLCV tools |
| `@skill:questdb-timeseries` | `questdb-playbook.md` | `get_ohlcv()` tool — query QuestDB → Polars                |
| `@skill:talib-indicators`   | `combined-usecase.md` | `get_ml_signal()` — feature pipeline within tool           |

```
Order:
1. agno-agent/resources/combined-usecase.md      ← blueprint entire toolkit
2. agno-agent/resources/agno-playbook.md         ← @tool pattern + error handling
3. questdb-timeseries/resources/questdb-playbook.md ← get_ohlcv() implementation
4. talib-indicators/resources/combined-usecase.md   ← get_ml_signal() feature matrix
```

#### Step 5 — LearningMachine (`agent/learning.py`)

| Skill                    | Resource to read       | Apply to                                       |
| ------------------------ | ---------------------- | ---------------------------------------------- |
| `@skill:chromadb-vector` | `chromadb-playbook.md` | Separate `ml_fx_learnings` collection          |
| `@skill:chromadb-vector` | `combined-usecase.md`  | `update_signal_outcome()` — after trade closes |

```
Read: chromadb-vector/resources/chromadb-playbook.md → "Updating an Existing Signal (Add Outcome)"
```

#### Step 6 — Skills (`agent/skills/`)

> `SKILL.md` files in `agent/skills/` have been defined in Phase 2 and the TODO above.
> See specific contents in TODO Phase 6 → Step 6 → ICT + Risk Management sections.

---

### Phase 7 — Expansion 📋

| Skill                      | Resource to read      | Apply to                                  |
| -------------------------- | --------------------- | ----------------------------------------- |
| `@skill:polars-dataframes` | `polars-playbook.md`  | Multi-symbol: add EURUSD, BTCUSD pipeline |
| `@skill:aiohttp-async`     | `aiohttp-playbook.md` | Download data for new symbols             |
| `@skill:financial-charts`  | `plotly-playbook.md`  | Monitoring dashboard (Plotly Dash base)   |
| `@skill:pytest-ml-fx`      | `combined-usecase.md` | Extend test suite for multi-symbol        |

---

## 📋 Skill Quick Reference

> Quick lookup table: task → required skill.

| Task                  | Main Skill           | Priority Resource      |
| --------------------- | -------------------- | ---------------------- |
| Read/write Parquet    | `polars-dataframes`  | `pyarrow-playbook.md`  |
| Resample tick → OHLCV | `polars-dataframes`  | `polars-playbook.md`   |
| Download Dukascopy    | `aiohttp-async`      | `aiohttp-playbook.md`  |
| Calculate RSI/MACD... | `talib-indicators`   | `talib-playbook.md`    |
| Save/query QuestDB    | `questdb-timeseries` | `questdb-playbook.md`  |
| Build agent + tools   | `agno-agent`         | `combined-usecase.md`  |
| Vector memory         | `chromadb-vector`    | `chromadb-playbook.md` |
| LLM provider          | `openai-lmstudio`    | `combined-usecase.md`  |
| Chart / dashboard     | `financial-charts`   | `combined-usecase.md`  |
| Write tests           | `pytest-ml-fx`       | `pytest-playbook.md`   |
