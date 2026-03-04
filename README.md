# ML_FX — ICT-Based Price Prediction System

> Xây dựng mô hình Machine Learning dự đoán giá **tiền tệ (Forex)**, **hàng hóa (Commodities)** và **tiền điện tử (Crypto)** dựa trên tín hiệu kỹ thuật từ **ICT Killzone**, **Support/Resistance** và **Pivot Points**.

---

## Tổng quan

ML_FX là hệ thống phân tích và dự đoán giá tài chính end-to-end, kết hợp:
- **Polars** (thay Pandas) để xử lý dữ liệu tick tốc độ cao
- **Machine Learning** để dự đoán hướng giá
- **AI Agent (Agno)** để ra tín hiệu giao dịch tự động

### Thị trường hỗ trợ

| Loại tài sản     | Ví dụ                                |
| ---------------- | ------------------------------------ |
| **Forex**        | EURUSD, GBPUSD, USDJPY, XAUUSD       |
| **Hàng hóa**     | Vàng (XAU), Bạc (XAG), Dầu thô (WTI) |
| **Tiền điện tử** | BTC, ETH, SOL                        |

---

## Cấu trúc dự án
> 📚 **Tài liệu cho người mới bắt đầu**: Nếu bạn muốn tự chạy Bot hoặc chưa hiểu về Machine Learning/Trading. Xin đọc:
> - [Giải Phẫu Hệ Thống & Nguyên Lý Bot](docs/NOOB_GUIDE.md)
> - [Hướng dẫn Setup & Cẩm nang Lệnh (Cheatsheet)](docs/USAGE_GUIDE.md)
> - [Từ Điển Thuật Ngữ](docs/GLOSSARY.md)
> - [Khắc phục Lỗi Cứng Cổ](docs/TROUBLESHOOTING.md)

```
ML_FX/
│
├── indicators/                          # Phase 2 ✅ — Feature Engineering
│   ├── __init__.py                     # Public API: add_killzone_features, add_sr_pp_features
│   ├── killzone.py                     # ICT Killzone: 5 sessions, pivot H/L, DWM levels, avg range
│   └── sr_pp.py                        # S/R patterns (r/r2/s/s2), role reversal, 6 Pivot Point types
│
├── pipeline/                           # Phase 3 📋 — ETL Pipeline
│   ├── resample.py                     # Tick → OHLCV (1m/5m/15m/1H/4H/1D), mid price
│   ├── features.py                     # killzone + sr_pp + TA-Lib + Order Blocks + FVG
│   └── labels.py                       # LONG/SHORT/NEUTRAL labeling (ATR-based threshold)
│
├── models/                             # Phase 4 📋 — ML Models
│   ├── knn.py                          # KNN baseline — TimeSeriesSplit CV
│   ├── gradient_boost.py               # XGBoost/LightGBM — SHAP + Optuna tuning
│   └── lstm.py                         # LSTM (PyTorch) — sequence 50–200 bars
│
├── eval/                               # Phase 5 📋 — Evaluation
│   └── backtest.py                     # Walk-forward, Sharpe, drawdown, win rate, R:R
│
├── viz/                                # Phase 5 📋 — Visualization
│   └── charts.py                       # Plotly candles + S/R overlay, Matplotlib equity curve
│
├── agent/                              # Phase 6 📋 — AI Agent (Agno 6-step)
│   ├── agent.py                        # create_agent(): LMStudio + ReasoningTools + DB
│   ├── toolkit.py                      # FXToolkit(Toolkit): get_killzone_status/levels/sr/pivot/ml_signal
│   ├── decision_engine.py              # Decision dataclass, LLM mode + heuristic fallback
│   ├── knowledge.py                    # ChromaDB "ml_fx_patterns" — RAG lịch sử tín hiệu
│   ├── learning.py                     # LearningMachine "ml_fx_learnings" — agent tự học
│   └── skills/
│       ├── ict-analysis/
│       │   └── SKILL.md               # Killzone rules, S/R role reversal, confidence scoring
│       └── risk-management/
│           └── SKILL.md               # SL/TP vs pp_s1/r1, position size vs confidence
│
├── data/
│   ├── raw/
│   │   └── XAUUSD/                    # Phase 1 ✅ — Tick Parquet từ Dukascopy
│   │       ├── 2015-01.parquet
│   │       ├── ...
│   │       └── completed_months.json  # Trạng thái download + missing hours
│   ├── ohlcv/                         # Phase 3 — Resampled OHLCV (per symbol/tf)
│   └── features/                      # Phase 3 — Feature DataFrames (per symbol/tf)
│
├── docs/
│   └── TODO.md                        # Kế hoạch 7 phase chi tiết
│
├── download_gold.py                    # Phase 1 ✅ — Async Dukascopy downloader
├── main.py                             # Entry point
└── pyproject.toml                      # Pixi workspace (Polars, TA-Lib, Agno, ChromaDB…)
```

---

## Các chỉ báo — nguồn tín hiệu đầu vào

### 1. ICT Killzone — `indicators/killzone.py`

Dịch từ Pine Script indicator **ICT Killzone**.

#### `killzone.py` — API chính

Theo dõi và vẽ các **Killzone** — khung thời gian có thanh khoản cao nhất trong ngày:

| Killzone     | Thời gian (ET) | Đặc điểm                                    |
| ------------ | -------------- | ------------------------------------------- |
| **Asia**     | 20:00 – 00:00  | Thanh khoản thấp, tạo range cho ngày mới    |
| **London**   | 02:00 – 05:00  | Breakout mạnh, thường set high/low của ngày |
| **NY AM**    | 09:30 – 11:00  | Sự kiện macro, liquidity sweep              |
| **NY Lunch** | 12:00 – 13:00  | Thanh khoản thấp, tránh giao dịch           |
| **NY PM**    | 13:30 – 16:00  | Đảo chiều cuối ngày                         |

**Tính năng bổ sung:**
- **Killzone Pivots**: High/Low của từng session, mở rộng cho đến khi bị phá vỡ
- **DWM Levels**: Giá mở cửa và high/low của Day, Week, Month
- **Opening Prices**: True Day Open (00:00), 06:00, 10:00, 14:00 lines
- **Timestamp verticals**: Đánh dấu các mốc thời gian quan trọng

**Features ML được trích xuất:**
```
in_{asia,london,nyam,nylunch,nypm}    # Killzone session flag
kz_{name}_high / _low / _mid          # Pivot của mỗi session
kz_{name}_range / _avg_range          # Range và trung bình N phiên
kz_{name}_session_id                  # Số thứ tự session
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

Dịch từ Pine Script indicator **SR + PP**.

#### A. Support/Resistance Boxes (Dynamic S/R)

Phát hiện vùng S/R dựa trên **price pattern**, phân loại:

| Pattern      | Điều kiện                               | Loại       |
| ------------ | --------------------------------------- | ---------- |
| `r` (1 nến)  | Nến giảm đột phá mạnh xuống dưới low[2] | Resistance |
| `r2` (2 nến) | Nến giảm kép đột phá vùng 2-nến         | Resistance |
| `s` (1 nến)  | Nến tăng đột phá mạnh lên trên high[2]  | Support    |
| `s2` (2 nến) | Nến tăng kép đột phá vùng 2-nến         | Support    |

**Role Reversal**: khi giá phá vỡ resistance → thành support, và ngược lại.

#### B. Pivot Points (Multi-Timeframe)

| Loại            | Công thức / Đặc điểm           |
| --------------- | ------------------------------ |
| **Traditional** | P = (H+L+C)/3 — phổ biến nhất  |
| **Fibonacci**   | Dùng tỷ lệ 0.236, 0.382, 0.618 |
| **Woodie**      | Ưu tiên giá đóng cửa           |
| **Classic**     | Pivot cổ điển                  |
| **DM**          | DeMark — chỉ 3 mức (P, R1, S1) |
| **Camarilla**   | 9 mức phân phối trong ngày     |

Timeframe anchor: Auto / Daily / Weekly / Monthly / Quarterly / Yearly — tối đa **200 pivot sets** lịch sử.

**Features ML được trích xuất:**
```
sr_resist_1bar / sr_resist_2bar        # Pattern resistance 1-bar / 2-bar
sr_support_1bar / sr_support_2bar      # Pattern support 1-bar / 2-bar
nearest_resist_high / _low             # Biên trên/dưới của vùng resistance gần nhất
nearest_support_high / _low            # Biên trên/dưới của vùng support gần nhất
in_resist_zone / in_support_zone        # Giá đang trong vùng S/R
dist_to_nearest_resist / _support       # close − biên vùng gần nhất
sr_role_reversal                       # 0 = neutral, +1 = resist→support, -1 = support→resist
pp_p / pp_r1..r5 / pp_s1..s5          # Giá trị các mức Pivot
pp_dist_to_p / pp_dist_to_r1 / _s1    # close − mức Pivot
pp_above_p                             # Giá trên hay dưới Pivot P
```

---

## Sử dụng — Python Indicators

```python
import polars as pl
from indicators import add_killzone_features, add_sr_pp_features

# Load dữ liệu tick đã resample lên 1H
df = pl.read_parquet("data/raw/XAUUSD/2024-01.parquet")

# Resample sang OHLCV 1H
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

# Thêm ICT Killzone features
ohlcv = add_killzone_features(ohlcv, avg_range_n=5)

# Thêm S/R + Pivot Point features
ohlcv = add_sr_pp_features(ohlcv, pivot_type="traditional", anchor="daily")

print(ohlcv.columns)
```

---

## Dữ liệu — Thu thập và lưu trữ

### `download_gold.py` — XAUUSD Tick Data

Script tải dữ liệu **tick (bid/ask)** lịch sử từ **Dukascopy** (từ năm 2015):

| Tham số       | Giá trị                                               |
| ------------- | ----------------------------------------------------- |
| Symbol        | `XAUUSD`                                              |
| Nguồn         | `datafeed.dukascopy.com`                              |
| Định dạng raw | `.bi5` (LZMA-compressed binary)                       |
| Định dạng lưu | **Parquet** (Polars, theo tháng)                      |
| Thư mục lưu   | `data/raw/XAUUSD/`                                    |
| Schema        | `timestamp`, `ask`, `bid`, `ask_volume`, `bid_volume` |

**Tính năng của script:**
- **Async download** (`aiohttp`) — 20 kết nối đồng thời, tối ưu tốc độ
- **State management** qua `completed_months.json` — bỏ qua tháng đã tải
- **Tự động repair** — phát hiện và vá các giờ còn thiếu trong tháng
- **Migration** — chuyển đổi format `.complete` cũ sang JSON mới
- **Retry logic** — exponential backoff khi gặp timeout/rate-limit
- Bỏ qua giờ thứ 7 và chủ nhật trước 21:00 UTC (thị trường vàng đóng)

```bash
# Tải toàn bộ dữ liệu XAUUSD
python download_gold.py
```

---

## Pipeline ML

```
Thu thập tick     →  ETL & Resample   →  Feature Engineering   →  Labeling
(Dukascopy/bi5)      (Polars/Parquet)    (ICT + S/R + PP)         (LONG/SHORT/NEUTRAL)
      ↓
  Training          →  Backtesting    →  Model Registry   →  AI Agent (Agno)
(XGBoost/LSTM/KNN)    (Equity curve)     (Best model)         (Realtime signal)
```

### Labeling

- **Target**: Hướng giá sau `N` nến (N = 5, 10, 20)
- **Classes**: `LONG (1)`, `SHORT (−1)`, `NEUTRAL (0)`
- Ngưỡng xác định bằng **ATR-based threshold**

### Mô hình

| Mô hình                | Dùng cho                               |
| ---------------------- | -------------------------------------- |
| **KNN**                | Baseline, lọc tín hiệu killzone        |
| **XGBoost / LightGBM** | Feature-based classification (tabular) |
| **LSTM**               | Dự đoán chuỗi thời gian ngắn hạn       |
| **Transformer**        | Multi-timeframe attention              |

---

## Công nghệ sử dụng

### Data & Processing

| Thư viện                                 | Mục đích                            | Ghi chú                         |
| ---------------------------------------- | ----------------------------------- | ------------------------------- |
| **[Polars](https://pola.rs/)**           | DataFrame, ETL, feature engineering | Thay Pandas — nhanh hơn 10–100x |
| **[PyArrow](https://arrow.apache.org/)** | Parquet I/O                         | Columnar format, nén tốt        |
| **[TA-Lib](https://ta-lib.org/)**        | RSI, EMA, ATR, indicators           | Tính bằng C, rất nhanh          |
| **[aiohttp](https://docs.aiohttp.org/)** | Async HTTP download                 | 20 concurrent connections       |
| **[QuestDB](https://questdb.io/)**       | Time-series database                | Query tick data cực nhanh       |

### Visualization

| Thư viện                 | Mục đích                                           |
| ------------------------ | -------------------------------------------------- |
| **Plotly**               | Biểu đồ nến tương tác, overlay S/R, killzone       |
| **Matplotlib / Seaborn** | Feature importance, equity curve, confusion matrix |

### AI Agent

| Thư viện                                     | Mục đích                                                                               |
| -------------------------------------------- | -------------------------------------------------------------------------------------- |
| **[Agno](https://github.com/agno-agi/agno)** | Agent framework — 6-step: LMStudio, ReasoningTools, Knowledge, LearningMachine, Skills |
| **[LM Studio](https://lmstudio.ai/)**        | LLM local (miễn phí, offline, OpenAI-compatible)                                       |
| **[ChromaDB](https://www.trychroma.com/)**   | Vector store — RAG patterns + agent learnings                                          |
| **SqliteDb** (agno)                          | Lưu lịch sử chat theo session                                                          |

---

## Cài đặt

```bash
# Quản lý môi trường với Pixi (khuyến nghị)
pixi install

# Tải dữ liệu XAUUSD từ 2015 đến nay
python download_gold.py
```

**Yêu cầu**: Python ≥ 3.13, Pixi

---

## Roadmap

- [x] Phase 1: Thu thập dữ liệu tick XAUUSD từ Dukascopy (`download_gold.py`)
- [x] Phase 2: Kỹ thuật nhúng tín hiệu (ICT Killzone, Support/Resistance + Pivot Points)
- [x] Phase 3: ETL & Feature Engineering Pipeline (Resample OHLCV, tính toán 130+ features)
- [x] Phase 4: Labeling + Training mô hình Machine Learning (KNN, XGBoost, LSTM)
- [x] Phase 5: Backtesting Engine giả lập Risk:Reward và Sinh báo cáo đồ thị (Plotly, Matplotlib)
- [ ] Phase 6: AI Agent (Agno 6-step) — Chatbot giao tiếp tự nhiên dựa trên tín hiệu mô hình
- [ ] Phase 7: Mở rộng sang Forex + Crypto

---

## Tác giả

**Hieu Nguyen** — [@ultimateBroK](https://github.com/ultimateBroK)  
Contact: hieuteo03@gmail.com