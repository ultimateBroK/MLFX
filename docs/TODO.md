# Kế Hoạch Phát Triển ML_FX (TODO)

Kế hoạch phát triển chi tiết, được xây dựng dựa trên kiến trúc từ dự án cryage-demo.

**Chú giải:** `[ ]` Chưa bắt đầu · `[/]` Đang tiến hành · `[x]` Đã hoàn thành

---

## Giai đoạn 1 — Thu thập Dữ liệu ✅

- [x] Tải dữ liệu tick XAUUSD từ Dukascopy (`download_data.py`)
  - [x] Bất đồng bộ aiohttp — 20 kết nối song song
  - [x] Dịch file nhị phân `.bi5` → Polars DataFrame
  - [x] Lưu định dạng Parquet theo tháng vào thư mục `data/raw/XAUUSD/`
  - [x] Quản lý trạng thái thông qua `completed_months.json` (chuyển đổi từ định dạng `.complete` cũ)
  - [x] Tự động phát hiện + vá các giờ dữ liệu bị thiếu

- [x] Đảm bảo Chất lượng Dữ liệu (Quality Assurance) (`pipeline/qa_data.py`)
  - [x] Phát hiện các khoảng trống (gaps) lớn và số giờ bị thiếu bất thường
  - [x] Phát hiện giá trị NaN, giá trị âm, và nhiễu spread âm
  - [x] Tự động tạo Báo cáo Chất lượng Markdown (`{symbol}_Data_Quality_Report.md`)

---

## Giai đoạn 2 — Kỹ thuật Dữ liệu Đặc trưng (Feature Engineering) ✅

- [x] **Vùng Giao dịch ICT Killzone** — `indicators/killzone.py`
  - [x] `add_session_flags()` — 5 cờ (flags) boolean tương ứng với 5 phiên
  - [x] `compute_killzone_pivots()` — Phân tích High/Low/Mid/Range qua hàm cum_max/min
  - [x] `compute_killzone_avg_range()` — Tính trung bình độ rộng (range) của N-phiên
  - [x] `compute_dwm_levels()` — Các mốc Open của Ngày/Tuần/Tháng + H/L quá khứ
  - [x] `add_killzone_features()` — Gom toàn bộ pipeline

- [x] **Hỗ trợ/Kháng cự (S/R) + Điểm Xoay (Pivot Points)** — `indicators/sr_pp.py`
  - [x] `detect_sr_patterns()` — Phát hiện r/r2/s/s2 với tính năng lọc trùng lập
  - [x] `compute_sr_zones()` — Theo dõi các vùng giá trị + Quá trình Role reversal (đổi vai trò Hỗ trợ/Kháng cự)
  - [x] `compute_pivot_points()` — 6 loại Điểm xoay × 5 khung anchor qua hàm asof_join
  - [x] `add_sr_pp_features()` — Gom toàn bộ pipeline

---

## Giai đoạn 3 — ETL Pipeline ✅

- [x] **Đồng bộ tick → Candlesticks (OHLCV)** — `pipeline/resample.py`
  - [x] Giá trung bình (Mid price): `(ask + bid) / 2`
  - [x] Hỗ trợ các khung: `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`
  - [x] Xử lý khoảng trống cuối tuần — `detect_gaps()`
  - [x] Lưu đầu ra vào `data/ohlcv/{symbol}/{tf}/`

- [x] **Pipeline xử lý Đặc trưng** — `pipeline/features.py`
  - [x] Kích hoạt `add_killzone_features()` + `add_sr_pp_features()`
  - [x] Tính toán bằng TA-Lib: RSI(14), MACD, ATR(14), EMA(20/50/200)
  - [x] Thêm **Order Blocks** (Khối lệnh) — `add_order_blocks()`
  - [x] Thêm **Fair Value Gaps** (Khoảng trống Giá Trị Hợp Lý) — `add_fair_value_gaps()`
  - [x] Chuẩn hóa khoảng cách + tỷ lệ chênh lệch ATR
  - [x] Lưu vào `data/features/{symbol}/{tf}/`

---

## Giai đoạn 4 — Gắn Nhãn & Huấn Luyện (Labeling & Training) ✅

- [x] **Gắn nhãn (Labeling)** — `pipeline/labels.py`
  - [x] Mục tiêu: dự đoán hướng giá sau N cây nến (N = 5, 10, 20)
  - [x] Lớp phân loại: MUA (+1), BÁN (−1), ĐI NGANG (0)
  - [x] ATR filter threshold nhằm tránh tín hiệu nhiễu
  - [x] Kiểm soát cân bằng lớp mẫu + phân chia Stratified

- [x] **Baseline — Mô hình KNN** — `models/knn.py`
  - [x] Huấn luyện bằng TimeSeriesSplit Cross-validation
  - [x] Lưu model + file số liệu (metrics)

- [x] **XGBoost / LightGBM** — `models/gradient_boost.py`
  - [x] Feature importance + Giá trị SHAP
  - [x] Cấu hình Optuna hyperparameter tuning

- [x] **Mạng nơ-ron LSTM** — `models/lstm.py`
  - [x] Chiều dài chuỗi tuần tự (Sequence length) khoảng 50–200 bars
  - [x] PyTorch — LSTM → Dropout → Mạng Dense

---

## Giai đoạn 5 — Đánh giá & Trực Quan hóa (Evaluation & Visualization) ✅

- [x] **Mô phỏng Giao Dịch (Backtesting)** — `eval/backtest.py`
  - [x] Kiểm định tiến tới Walk-forward
  - [x] Tỷ số: Sharpe, Độ sụt giảm tối đa (drawdown), win rate, Tỷ lệ Rủi ro/Lợi nhuận (R:R)

- [x] **Đồ Thị (Visualization)** — `viz/charts.py`
  - [x] Biểu đồ Candlestick + Kẻ vùng S/R + Vùng Killzone (bằng Plotly)
  - [x] Ký hiệu Giao dịch cho lệnh đánh: LONG/SHORT/NEUTRAL
  - [x] Đường lợi nhuận tổng (Equity curve) + Độ rớt giá tài khoản (Matplotlib)
  - [x] Heatmap bản đồ nhiệt mức độ mức độ tập trung (Seaborn)

---

## Giai đoạn 6 — Hệ thống Trợ lý AI Agent (Hoạt động Agno 6-bước) 📋

> **Cấu trúc đúc kết từ quá trình học:** Thiết lập tính năng Agno 6-bước:

### Bước 1 — Trình xuất mã nền tảng LLM Provider
- [ ] `agent/agent.py` — Chạy `LMStudio(id=model_id)` với LLM mạng nội bộ
  - [ ] Hoán đổi fallback qua máy chủ của OpenAI nếu như Offline Server đang gặp sự cố

### Bước 2 — Luồng Suy luận (ReasoningTools)
- [ ] Kích hoạt khả năng `ReasoningTools(add_instructions=True)`
  - [ ] Hạn chế sự việc rạo ảo giác (hallucination), bọc hệ thống đưa phân tích thành nhiều chặng đơn lẻ chi tiết.

### Bước 3 — Kiến thức (Knowledge) + Cơ sở Vector ChromaDB (RAG)
- [ ] `agent/knowledge.py` — xây dựng chức năng tri thức `Knowledge`
  - [ ] Chạy kho Vector ChromaDB mã `"ml_fx_patterns"` — Lưu tiến trình của tín hiệu phân tích cũ đi với diễn biến tương lai cụ thể của chúng.
  - [ ] Công đoạn cung cấp tin ghi, và Agent đọc dựa trên lệnh `search_knowledge_base`

### Bước 4 — Valy Công cụ (Toolkit)
- [ ] `agent/toolkit.py` — mã lớp con kế thừa từ bộ phận `agno.tools.Toolkit`

  **Bộ cung cấp ICT Killzone** (Tích hợp `indicator.killzone`):
  - [ ] `get_killzone_status()` — Mở cửa cho `add_session_flags()` cung cấp xem phiên hiện tại đang đánh là vùng gì.
  - [ ] `get_killzone_levels(symbol, timeframe)` — Yêu cầu `compute_killzone_pivots()` đánh xuất điểm Low/High
  - [ ] `get_killzone_avg_range(symbol, timeframe, n=5)` — Xét độ biến động trung bình qua vùng
  - [ ] `get_dwm_levels(symbol)` — Báo mức Open Day/Week/Month quá khứ.

  **Bộ Cung cấp Phân tích Vùng giá/S/R + Chốt Pivot**:
  - [ ] `get_sr_zones(symbol, timeframe)` — Chạy `detect_sr_patterns()` + `compute_sr_zones()`, tìm Hỗ trợ, Kháng cự
  - [ ] `get_pivot_levels(...)` — Đi tìm chốt Pivot
  - [ ] `get_sr_patterns(...)` — Mở `detect_sr_patterns()`

  **Nhóm Công cụ Máy học (Machine Learning)**:
  - [ ] `get_ohlcv(...)` — Tra cứu dữ liệu biểu diễn số lượng Parquet giới hạn để làm bước đệm.
  - [ ] `get_ml_signal(...)` — Đưa lệnh qua nguyên ống quy trình và tính xem thuật toán chỉ ra giá lên tới bao nhiêu.

### Bước 5 — Cỗ máy tự học (LearningMachine)
- [ ] `agent/learning.py` — dựng Cỗ Máy Tự Rèn Trí
  - [ ] Khu nạp Vector DB `ml_fx_learnings`

### Bước 6 — Kỹ Năng / Tập Tài Liệu Tham chiếu (Skills)
- [ ] `agent/skills/ict-analysis/SKILL.md`: Các điều luật đánh Killzone, đổi vùng Resistance sang Support (và ngược lại), các nguyên tắc xếp hạng sức tin cậy (Confidence).
- [ ] `agent/skills/risk-management/SKILL.md`: Kiểm duyệt vốn % rủi ro, phân bậc chia mức cắt lỗ chuẩn chỉ cho từng khu Support, cách chặn giao dịch cấm lúc đang sideway

---

## Giai đoạn 7 — Không gian Cải tiến Phụ (Expansion) 📋

- [ ] Multi-symbol: Cho chạy trên BTC, EUR
- [ ] Tính năng khớp lệnh Multi-timeframe
- [ ] Mở rộng kịch bản đào tạo tự động hàng tháng
- [ ] Dashboard theo dõi biểu đồ theo (Plotly Dash)
- [ ] Paper Trading ảo qua sàn API
