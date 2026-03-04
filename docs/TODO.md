# TODO — ML_FX Development Plan

Kế hoạch phát triển chi tiết, học hỏi từ kiến trúc [cryage-demo](../../../cryage-demo).

**Legend:** `[ ]` chưa làm · `[/]` đang làm · `[x]` hoàn thành

---

## Phase 1 — Data Collection ✅

- [x] Download tick XAUUSD từ Dukascopy (`download_gold.py`)
  - [x] Async aiohttp — 20 concurrent connections
  - [x] Parse `.bi5` binary → Polars DataFrame
  - [x] Lưu Parquet theo tháng vào `data/raw/XAUUSD/`
  - [x] State management qua `completed_months.json` (migrate từ `.complete`)
  - [x] Tự động detect + repair missing hours

---

## Phase 2 — Feature Engineering ✅

- [x] **ICT Killzone** — `indicators/killzone.py`
  - [x] `add_session_flags()` — 5 boolean session flags
  - [x] `compute_killzone_pivots()` — session High/Low/Mid/Range via cum_max/min
  - [x] `compute_killzone_avg_range()` — rolling N-session avg range
  - [x] `compute_dwm_levels()` — Day/Week/Month open + prev H/L
  - [x] `add_killzone_features()` — pipeline tổng hợp

- [x] **Support/Resistance + Pivot Points** — `indicators/sr_pp.py`
  - [x] `detect_sr_patterns()` — pattern r/r2/s/s2 với de-duplicate
  - [x] `compute_sr_zones()` — zone tracking + role reversal
  - [x] `compute_pivot_points()` — 6 types × 5 anchor TF với asof_join
  - [x] `add_sr_pp_features()` — pipeline tổng hợp

---

## Phase 3 — ETL Pipeline ✅

- [x] **Resample tick → OHLCV** — `pipeline/resample.py`
  - [x] Mid price: `(ask + bid) / 2`
  - [x] Hỗ trợ TF: `1m`, `5m`, `15m`, `1H`, `4H`, `1D`
  - [x] Xử lý gaps (weekend, market close) — `detect_gaps()`
  - [x] Lưu vào `data/ohlcv/{symbol}/{tf}/`

- [x] **Feature pipeline** — `pipeline/features.py`
  - [x] Gọi `add_killzone_features()` + `add_sr_pp_features()`
  - [x] Thêm TA-Lib: RSI(14), MACD, ATR(14), EMA(20/50/200)
  - [x] Thêm **Order Blocks** — `add_order_blocks()`
  - [x] Thêm **Fair Value Gaps** — `add_fair_value_gaps()`
  - [x] Normalize + scale features — ATR-normalized distances
  - [x] Lưu vào `data/features/{symbol}/{tf}/`

> **Học từ cryage-demo**: tách `indicator_calculation.py` và `ohlcv_ingestion.py` thành pipeline riêng biệt.

---

## Phase 4 — Labeling & Training ✅

- [x] **Labeling** — `pipeline/labels.py`
  - [x] Target: hướng giá sau N nến (N = 5, 10, 20)
  - [x] Classes: LONG (+1), SHORT (−1), NEUTRAL (0)
  - [x] ATR-based threshold để tránh label noise
  - [x] Class balance check + stratified split

- [x] **Baseline — KNN** — `models/knn.py`
  - [x] TimeSeriesSplit cross-validation
  - [x] Lưu model + metrics

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
  - [x] Biểu đồ nến + overlay S/R + killzone (Plotly)
  - [x] Signal markers LONG/SHORT/NEUTRAL
  - [x] Equity curve + drawdown (Matplotlib)
  - [x] Feature importance heatmap (Seaborn)

---

## Phase 6 — AI Agent (Agno 6-Step) 📋

> **Kiến trúc học từ cryage-demo** — 6 bước triển khai Agno:

### Step 1 — LLM Provider
- [ ] `agent/agent.py` — dùng `LMStudio(id=model_id)` làm LLM local
  - [ ] Fallback sang OpenAI nếu LMStudio không có

### Step 2 — ReasoningTools
- [ ] Thêm `ReasoningTools(add_instructions=True)` vào agent
  - [ ] Giảm hallucination, agent suy luận từng bước

### Step 3 — Knowledge + ChromaDB (RAG)
- [ ] `agent/knowledge.py` — build `Knowledge` object
  - [ ] ChromaDB collection `"ml_fx_patterns"` — lưu lịch sử tín hiệu + kết quả
  - [ ] PatternService ghi, agent đọc qua `search_knowledge_base`

### Step 4 — Toolkit (Tools)
- [ ] `agent/toolkit.py` — subclass `agno.tools.Toolkit`

  **Killzone tools** (dùng `indicator.killzone`):
  - [ ] `get_killzone_status()` — gọi `add_session_flags()`, trả về session hiện tại
    - Output: `{in_asia, in_london, in_nyam, in_nylunch, in_nypm}` + tên session active
  - [ ] `get_killzone_levels(symbol, timeframe)` — gọi `compute_killzone_pivots()`
    - Output: `kz_{name}_high/low/mid/range` cho mỗi session
  - [ ] `get_killzone_avg_range(symbol, timeframe, n=5)` — gọi `compute_killzone_avg_range()`
    - Output: `kz_{name}_avg_range` — range trung bình N phiên
  - [ ] `get_dwm_levels(symbol)` — gọi `compute_dwm_levels()`
    - Output: `d_open/high/low`, `w_open/high/low`, `m_open/high/low`, `pd_high/low`, `pw_high/low`, `pm_high/low`

  **S/R + Pivot tools** (dùng `indicator.sr_pp`):
  - [ ] `get_sr_zones(symbol, timeframe)` — gọi `detect_sr_patterns()` + `compute_sr_zones()`
    - Output: `nearest_resist_high/low`, `nearest_support_high/low`, `in_resist_zone`, `in_support_zone`, `sr_role_reversal`
  - [ ] `get_pivot_levels(symbol, timeframe, pivot_type="traditional", anchor="daily")` — gọi `compute_pivot_points()`
    - Output: `pp_p`, `pp_r1..r5`, `pp_s1..s5`, `pp_dist_to_p/r1/s1`, `pp_above_p`
  - [ ] `get_sr_patterns(symbol, timeframe)` — gọi `detect_sr_patterns()`
    - Output: `sr_resist_1bar`, `sr_resist_2bar`, `sr_support_1bar`, `sr_support_2bar`

  **ML + data tools**:
  - [ ] `get_ohlcv(symbol, timeframe, limit=200)` — load + resample từ Parquet
  - [ ] `get_ml_signal(symbol, timeframe)` — chạy full feature pipeline + trained model
    - Output: `{action: LONG/SHORT/NEUTRAL, confidence: 0–100, features_snapshot}`

### Step 5 — LearningMachine (Self-learning)
- [ ] `agent/learning.py` — build `LearningMachine`
  - [ ] ChromaDB collection `"ml_fx_learnings"` (tách khỏi patterns)
  - [ ] `LearningMode.AGENTIC` — agent tự quyết định nhớ gì
  - [ ] Agent học từ kết quả các tín hiệu đã ra

### Step 6 — Skills (Domain Knowledge)

- [ ] `agent/skills/ict-analysis/SKILL.md`

  **ICT Killzone** (từ `killzone.py`):
  - Uu tiên tín hiệu bên trong killzone: `in_london=True` hoặc `in_nyam=True`
  - Killzone pivot: dùng `kz_{name}_high/low` làm S/R key — chờ retest trước khi vào lệnh
  - `kz_{name}_avg_range`: nếu `kz_range < avg_range * 0.5` → session chưa mở, chờ thêm
  - DWM levels: `pd_high/low` (PDH/PDL) là key level ICT cốt lõi; `pw_high/low` cho bias tuần
  - Ngoài killzone và tín hiệu không rất mạnh (confidence > 85%) → HOLD

  **S/R + Pivot** (từ `sr_pp.py`):
  - Pattern `sr_resist_1bar / sr_support_1bar`: xác nhận sớm hơn 2-bar
  - `sr_role_reversal = +1`: resistance đã thành support → tìm BUY khi giảm về vùng
  - `sr_role_reversal = -1`: support đã thành resistance → tìm SELL khi tăng lên
  - `in_resist_zone / in_support_zone`: giá đang trong vùng → entry risk cao, chờ thoát zone
  - `dist_to_nearest_resist/support`: càng nhỏ càng gần mức kiểm tra
  - Pivot P: ngưỡng trung lập ngày; `pp_above_p=True` → bullish bias
  - R1/S1: mục TP1 tiêu chuẩn; R2/S2: mục TP2 aggresive
  - Camarilla R3/S3: đảo chiều mạnh — nếu giá xuất hiện → sử dụng làm SL tight

  **Confidence scoring**:
  - 1 layer đồng thuận → 30–45% → HOLD
  - 2 layers + killzone active → 55–65% → weak signal
  - 3+ layers + killzone + S/R confluence → 70–85% → strong signal
  - Tất cả (động lực + xu hướng + cấu trúc + context) → 85–95% → very strong

- [ ] `agent/skills/risk-management/SKILL.md`
  - Max risk: 1% portfolio / lệnh; không quá 3 lệnh cùng lúc
  - SL BUY: dưới `nearest_support_low` hoặc `pp_s1`, tối đa 3% từ entry
  - SL SELL: trên `nearest_resist_high` hoặc `pp_r1`, tối đa 3% từ entry
  - TP1 BUY: `pp_r1`; TP2: `pp_r2`; R:R tối thiểu 1:2
  - TP1 SELL: `pp_s1`; TP2: `pp_s2`; R:R tối thiểu 1:2
  - Position size theo confidence: 60–69% → 0.5%; 70–79% → 0.75%; 80%+ → 1%
  - Red flags → bỏ qua lệnh: ngoài killzone (điều kiện bất buộc trừ confidence > 85%),
    `in_resist_zone / in_support_zone = True`, MTF mâu thuẫn (1H vs 4H)

### Decision Engine
- [ ] `agent/decision_engine.py` — safety gate
  - [ ] **LLM mode**: `agent.run(prompt, output_schema=TradingDecision)` — Agno validates
  - [ ] **Heuristic mode**: rule-based fallback khi LLM không có
  - [ ] Dataclass `Decision(action, pair, confidence, stop_loss, take_profit, source)`
  - [ ] `should_execute(decision)` — gate: confidence ≥ 60% và action ≠ HOLD
  - [ ] `SqliteDb("ml_fx_sessions.db")` — lưu lịch sử chat

### System Prompt
- [ ] Phân tích 4 lớp (học từ cryage):
  1. **Momentum** — RSI, MACD, Stochastic
  2. **Trend** — EMA alignment, killzone highs/lows
  3. **Structure** — S/R zones, Pivot P/R1/S1
  4. **Context** — killzone session, MTF confluence
- [ ] Confidence gate: < 60% → HOLD bất kể signals

---

## Phase 7 — Mở rộng 📋

- [ ] Multi-symbol: EURUSD, GBPUSD, BTCUSD, ETHUSD
- [ ] Multi-timeframe confluence: MTF signal alignment
- [ ] Auto-retraining pipeline (monthly trigger)
- [ ] Monitoring dashboard (Plotly Dash)
- [ ] Paper trading integration

---

## Kiến trúc thư mục đích đến

```
ML_FX/
├── indicators/          # Feature engineering (done ✅)
│   ├── killzone.py
│   ├── sr_pp.py
│   └── __init__.py
├── pipeline/           # ETL + labeling
│   ├── resample.py
│   ├── features.py
│   └── labels.py
├── models/             # ML models
│   ├── knn.py
│   ├── gradient_boost.py
│   └── lstm.py
├── eval/               # Backtesting
│   └── backtest.py
├── viz/                # Visualization
│   └── charts.py
├── agent/              # Agno agent (cryage pattern)
│   ├── agent.py        # create_agent() — 6 bước
│   ├── toolkit.py      # FXToolkit(Toolkit)
│   ├── decision_engine.py
│   ├── knowledge.py
│   ├── learning.py
│   └── skills/
│       ├── ict-analysis/SKILL.md
│       └── risk-management/SKILL.md
├── outputs/            # Generated assets
│   ├── reports/        # Backtest reports, heatmaps
│   └── models/         # Saved model .json files, SHAP plots
├── data/
│   ├── raw/XAUUSD/     # Tick Parquet ✅
│   ├── raw/BTCUSD/     # Tick Parquet ✅
│   ├── ohlcv/          # Resampled OHLCV
│   └── features/       # Feature DataFrames
└── docs/
    └── TODO.md         # This file
```

---

## Ghi chú kỹ thuật

| Thành phần      | Quyết định            | Lý do                                    |
| --------------- | --------------------- | ---------------------------------------- |
| DataFrame       | **Polars**            | 10–100× nhanh hơn Pandas                 |
| Serialization   | **Parquet** (PyArrow) | Columnar, compressed                     |
| Agent framework | **Agno**              | Native LMStudio, Skills, LearningMachine |
| LLM             | **LM Studio** (local) | Free, offline, OpenAI compatible         |
| Vector DB       | **ChromaDB**          | Tích hợp native Agno Knowledge           |
| Session DB      | **SQLiteDb**          | Lưu lịch sử chat agent                   |
| Env manager     | **Pixi**              | conda-forge + pypi hybrid                |

---

## 🧭 Hướng dẫn sử dụng Skills theo Phase

> Mỗi phase khi bắt đầu, AI agent đọc các skill tương ứng trước khi sinh code.
> Cú pháp tham chiếu: `@skill:<tên-skill>` → đọc `SKILL.md` + resource liên quan.

---

### Phase 1 — Data Collection ✅  
> _Phase đã hoàn thành. Skills dùng để maintain hoặc mở rộng pipeline._

| Skill                      | Resource cần đọc      | Áp dụng vào                                     |
| -------------------------- | --------------------- | ----------------------------------------------- |
| `@skill:aiohttp-async`     | `aiohttp-playbook.md` | Sửa/mở rộng `download_gold.py`                  |
| `@skill:aiohttp-async`     | `combined-usecase.md` | Thêm data source mới (retry pattern, semaphore) |
| `@skill:polars-dataframes` | `pyarrow-playbook.md` | Ghi Parquet theo tháng, schema enforcement      |

**Checklist khi dùng skills:**
- [ ] Đọc `aiohttp-playbook.md` → section "Bounded Concurrency" để calibrate `MAX_CONC`
- [ ] Đọc `pyarrow-playbook.md` → section "Writing Partitioned Parquet" để giữ nhất quán schema

---

### Phase 2 — Feature Engineering ✅  
> _Phase đã hoàn thành. Skills dùng khi thêm indicator mới._

| Skill                      | Resource cần đọc      | Áp dụng vào                                        |
| -------------------------- | --------------------- | -------------------------------------------------- |
| `@skill:polars-dataframes` | `polars-playbook.md`  | Viết `with_columns`, rolling, join trong indicator |
| `@skill:talib-indicators`  | `talib-playbook.md`   | Thêm candlestick pattern detection                 |
| `@skill:talib-indicators`  | `combined-usecase.md` | Build feature vector từ multi-indicator            |

**Checklist khi dùng skills:**
- [ ] Đọc `polars-playbook.md` → "Expressions Over Python Loops" → **không dùng `.apply()`**
- [ ] Đọc `talib-playbook.md` → "Lookback Alignment" → xử lý NaN trước khi join với OHLCV frame

---

### Phase 3 — ETL Pipeline 📋 ← **CẦN LÀM TIẾP**

| Skill                       | Resource cần đọc      | Áp dụng vào                                    |
| --------------------------- | --------------------- | ---------------------------------------------- |
| `@skill:polars-dataframes`  | `polars-playbook.md`  | `pipeline/resample.py` — `group_by_dynamic()`  |
| `@skill:polars-dataframes`  | `pyarrow-playbook.md` | Ghi OHLCV ra `data/ohlcv/{symbol}/{tf}/`       |
| `@skill:polars-dataframes`  | `combined-usecase.md` | End-to-end: tick → OHLCV → validate → save     |
| `@skill:talib-indicators`   | `talib-playbook.md`   | `pipeline/features.py` — RSI, MACD, ATR, EMA   |
| `@skill:questdb-timeseries` | `questdb-playbook.md` | Lưu features vào QuestDB thay vì Parquet thuần |

**Thứ tự đọc skills khi implement Phase 3:**
```
1. polars-dataframes/resources/combined-usecase.md    ← blueprint tổng thể
2. polars-dataframes/resources/polars-playbook.md     ← resample.py
3. polars-dataframes/resources/pyarrow-playbook.md    ← write partitioned Parquet
4. talib-indicators/resources/talib-playbook.md       ← features.py
5. talib-indicators/resources/combined-usecase.md     ← feature matrix đầy đủ
```

**Files cần tạo:**
- `pipeline/resample.py` → dùng `group_by_dynamic()` từ polars-playbook
- `pipeline/features.py` → dùng `add_ta_column()` pattern từ talib-playbook

---

### Phase 4 — Labeling & Training 📋

| Skill                      | Resource cần đọc      | Áp dụng vào                                     |
| -------------------------- | --------------------- | ----------------------------------------------- |
| `@skill:polars-dataframes` | `polars-playbook.md`  | `pipeline/labels.py` — shift/lead để tạo target |
| `@skill:talib-indicators`  | `combined-usecase.md` | Dùng feature matrix làm đầu vào KNN/XGBoost     |
| `@skill:pytest-ml-fx`      | `pytest-playbook.md`  | Test labeling với parametrize edge cases        |
| `@skill:financial-charts`  | `seaborn-playbook.md` | Visualize class balance, feature correlation    |

**Thứ tự đọc skills khi implement Phase 4:**
```
1. talib-indicators/resources/combined-usecase.md     ← hiểu feature matrix input
2. polars-dataframes/resources/polars-playbook.md     ← shift() để tạo label N-bar ahead
3. pytest-ml-fx/resources/pytest-playbook.md          ← test labels + model outputs
4. financial-charts/resources/seaborn-playbook.md     ← plot_indicator_correlation()
```

**Pattern labeling với Polars:**
```python
# Trong pipeline/labels.py
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

| Skill                       | Resource cần đọc         | Áp dụng vào                                          |
| --------------------------- | ------------------------ | ---------------------------------------------------- |
| `@skill:financial-charts`   | `plotly-playbook.md`     | `viz/charts.py` — candlestick + S/R + signal markers |
| `@skill:financial-charts`   | `matplotlib-playbook.md` | Equity curve + drawdown panel                        |
| `@skill:financial-charts`   | `seaborn-playbook.md`    | Session heatmap, return distribution                 |
| `@skill:financial-charts`   | `combined-usecase.md`    | **Full backtest report trong 1 script**              |
| `@skill:questdb-timeseries` | `combined-usecase.md`    | Query walk-forward windows từ QuestDB                |

**Thứ tự đọc skills khi implement Phase 5:**
```
1. financial-charts/resources/combined-usecase.md     ← template backtest report đầy đủ
2. financial-charts/resources/plotly-playbook.md      ← add_sr_overlays(), shade_killzones()
3. financial-charts/resources/matplotlib-playbook.md  ← plot_equity_curve()
4. financial-charts/resources/seaborn-playbook.md     ← plot_session_heatmap()
```

**Files cần tạo:**
- `viz/charts.py` → copy pattern từ `financial-charts/combined-usecase.md`
- `eval/backtest.py` → query từ QuestDB (xem `questdb-playbook.md` → "ASOF JOIN")

---

### Phase 6 — AI Agent (Agno 6-Step) 📋

> Phase quan trọng nhất — mỗi step tương ứng một hoặc nhiều skills.

#### Step 1 — LLM Provider (`agent/agent.py`)

| Skill                    | Resource cần đọc       | Áp dụng vào                               |
| ------------------------ | ---------------------- | ----------------------------------------- |
| `@skill:openai-lmstudio` | `lmstudio-playbook.md` | Config `LMStudio(id=model_id)` local      |
| `@skill:openai-lmstudio` | `openai-playbook.md`   | Fallback OpenAI async client              |
| `@skill:openai-lmstudio` | `combined-usecase.md`  | **Provider router** — route by complexity |

```
Đọc: openai-lmstudio/resources/combined-usecase.md → copy `routed_chat()` function
```

#### Step 2 — ReasoningTools

> `ReasoningTools` là Agno built-in — xem `agno-playbook.md` section "Agent Setup".
```
Đọc: agno-agent/resources/agno-playbook.md → section "Agent Setup"
```

#### Step 3 — Knowledge + ChromaDB (`agent/knowledge.py`)

| Skill                    | Resource cần đọc       | Áp dụng vào                                          |
| ------------------------ | ---------------------- | ---------------------------------------------------- |
| `@skill:chromadb-vector` | `chromadb-playbook.md` | Setup persistent client, collection `ml_fx_patterns` |
| `@skill:chromadb-vector` | `combined-usecase.md`  | Store signal + retrieve similar historical setups    |

```
Đọc: chromadb-vector/resources/chromadb-playbook.md → "Collection Management" + "Storing Trade Signals"
Đọc: chromadb-vector/resources/combined-usecase.md  → blueprint PatternService
```

#### Step 4 — Toolkit (`agent/toolkit.py`)

| Skill                       | Resource cần đọc      | Áp dụng vào                                               |
| --------------------------- | --------------------- | --------------------------------------------------------- |
| `@skill:agno-agent`         | `agno-playbook.md`    | `@tool` decorator, async tool pattern, error handling     |
| `@skill:agno-agent`         | `combined-usecase.md` | **Full toolkit example** với killzone + S/R + OHLCV tools |
| `@skill:questdb-timeseries` | `questdb-playbook.md` | `get_ohlcv()` tool — query QuestDB → Polars               |
| `@skill:talib-indicators`   | `combined-usecase.md` | `get_ml_signal()` — feature pipeline trong tool           |

```
Thứ tự:
1. agno-agent/resources/combined-usecase.md      ← blueprint toàn bộ toolkit
2. agno-agent/resources/agno-playbook.md         ← pattern @tool + error handling
3. questdb-timeseries/resources/questdb-playbook.md ← get_ohlcv() implementation
4. talib-indicators/resources/combined-usecase.md   ← get_ml_signal() feature matrix
```

#### Step 5 — LearningMachine (`agent/learning.py`)

| Skill                    | Resource cần đọc       | Áp dụng vào                                    |
| ------------------------ | ---------------------- | ---------------------------------------------- |
| `@skill:chromadb-vector` | `chromadb-playbook.md` | Collection `ml_fx_learnings` riêng biệt        |
| `@skill:chromadb-vector` | `combined-usecase.md`  | `update_signal_outcome()` — sau khi trade đóng |

```
Đọc: chromadb-vector/resources/chromadb-playbook.md → "Updating an Existing Signal (Add Outcome)"
```

#### Step 6 — Skills (`agent/skills/`)

> Các file `SKILL.md` trong `agent/skills/` đã được define ở Phase 2 và TODO trên.
> Xem nội dung cụ thể tại TODO Phase 6 → Step 6 → sections ICT + Risk Management.

---

### Phase 7 — Mở rộng 📋

| Skill                      | Resource cần đọc      | Áp dụng vào                                |
| -------------------------- | --------------------- | ------------------------------------------ |
| `@skill:polars-dataframes` | `polars-playbook.md`  | Multi-symbol: thêm EURUSD, BTCUSD pipeline |
| `@skill:aiohttp-async`     | `aiohttp-playbook.md` | Download data cho symbol mới               |
| `@skill:financial-charts`  | `plotly-playbook.md`  | Monitoring dashboard (Plotly Dash base)    |
| `@skill:pytest-ml-fx`      | `combined-usecase.md` | Extend test suite cho multi-symbol         |

---

## 📋 Skill Quick Reference

> Bảng tra nhanh: task → skill cần dùng.

| Task                  | Skill chính          | Resource ưu tiên       |
| --------------------- | -------------------- | ---------------------- |
| Đọc/ghi Parquet       | `polars-dataframes`  | `pyarrow-playbook.md`  |
| Resample tick → OHLCV | `polars-dataframes`  | `polars-playbook.md`   |
| Download Dukascopy    | `aiohttp-async`      | `aiohttp-playbook.md`  |
| Tính RSI/MACD/ATR     | `talib-indicators`   | `talib-playbook.md`    |
| Lưu/query QuestDB     | `questdb-timeseries` | `questdb-playbook.md`  |
| Build agent + tools   | `agno-agent`         | `combined-usecase.md`  |
| Vector memory         | `chromadb-vector`    | `chromadb-playbook.md` |
| LLM provider          | `openai-lmstudio`    | `combined-usecase.md`  |
| Chart / dashboard     | `financial-charts`   | `combined-usecase.md`  |
| Viết test             | `pytest-ml-fx`       | `pytest-playbook.md`   |
