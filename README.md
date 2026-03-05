# ML_FX — Hệ Thống Dự Đoán Giá Dựa Trên Khái Niệm ICT

> Xây dựng Mô hình Học Máy dự đoán xu hướng giá cho **Forex**, **Hàng hóa (Commodities)**, và **Mã Hóa (Crypto)** căn cứ theo các tín hiệu kỹ thuật từ **Vùng Giao Dịch (ICT Killzone)**, **Hỗ Trợ/Kháng Cự (Support/Resistance)**, và **Điểm Xoay (Pivot Points)**.

---

## 🌎 Ngôn ngữ (Languages)
- **Tiếng Việt (Vietnamese)**: Tài liệu nằm trong `/docs/` và tại file README hiện tại.
- **Tiếng Anh (English)**: Please visit `/docs/en/` for all English documentation. 

---

## Tổng Quan

ML_FX là một hệ thống phân tích và dự đoán giá tài chính nội bộ toàn diện, qua việc kết hợp:
- **Polars** (thay thế Pandas) để xử lý dữ liệu tick ở tốc độ cực cao
- **Máy Học (Machine Learning)** để dự đoán hướng đi của giá
- **Trợ lý AI Agent (Agno)** dùng để suy diễn và tạo tín hiệu giao dịch tự động

### Các Thị trường được Hỗ trợ

| Lớp Tài Sản  | Ví dụ                                |
| ------------ | ------------------------------------ |
| **Forex**    | EURUSD, GBPUSD, USDJPY, XAUUSD       |
| **Hàng Hóa** | Vàng (XAU), Bạc (XAG), Dầu Thô (WTI) |
| **Crypto**   | BTC, ETH, SOL                        |

---

## Cấu trúc Dự án
> 📚 **Tài liệu cho người mới bắt đầu**: Nếu bạn muốn tự chạy Bot hoặc không rành về Máy học/Giao dịch. Vui lòng đọc:
> - [Cấu phẫu Hệ thống & Nguyên lý Bot](docs/NOOB_GUIDE.md)
> - [Hướng dẫn Cài đặt & Code lệnh](docs/USAGE_GUIDE.md)
> - [Bảng Thuật Ngữ](docs/GLOSSARY.md)
> - [Hướng dẫn Khắc phục Lỗi](docs/TROUBLESHOOTING.md)

```text
ML_FX/
│
├── indicators/                          # Giai đoạn 2 ✅ — Trích xuất Đặc trưng (Feature Engineering)
│   ├── __init__.py                     # API Mở: add_killzone_features, add_sr_pp_features
│   ├── killzone.py                     # ICT Killzone: Phân khu 5 phiên, xác định đỉnh/đáy, biên độ giá trung bình
│   └── sr_pp.py                        # Các mẫu S/R (r/r2/s/s2), quy luật đổi vai trò, 6 Loại Pivot Point
│
├── pipeline/                           # Giai đoạn 1 & 3 ✅ — Đường dẫn ETL
│   ├── download_data.py                # Lấy dữ liệu Tick thô từ Dukascopy (hỗ trợ FX, Crypto)
│   ├── qa_data.py                      # Kịch bản kiểm tra chất lượng để tra cứu dữ liệu thiếu giờ
│   ├── resample.py                     # Chuyển đổi Tick → OHLCV (1m/5m/15m/30m/1H/2H/4H/1D), lấy giá mid
│   ├── features.py                     # killzone + sr_pp + TA-Lib + Khối lệnh (Order Blocks) + FVG
│   └── labels.py                       # Gắn nhãn MUA/BÁN/ĐI NGANG (dựa theo giới hạn ATR)
│
├── models/                             # Giai đoạn 4 ✅ — Mô hình Học Máy (ML Models)
│   ├── knn.py                          # Tuyến cơ sở KNN — phân tách bằng TimeSeriesSplit CV
│   ├── gradient_boost.py               # XGBoost/LightGBM — giá trị SHAP + dò tìm Optuna
│   └── lstm.py                         # Mạng nơ rôn tuần từ LSTM (PyTorch) — chuỗi độ dài 50-200
│
├── eval/                               # Giai đoạn 5 ✅ — Đánh giá
│   ├── backtest.py                     # Mô phỏng Walk-forward, đo Sharpe, drawdown, tỷ lệ thắng, R:R
│   └── run_eval.py                     # Tính toán tổng hợp báo cáo và chạy mô phỏng
│
├── viz/                                # Giai đoạn 5 ✅ — Trực Quan Hóa (Visualization)
│   └── charts.py                       # Biểu đồ nến Plotly + S/R overlay, đường cong lợi nhuận Matplotlib
│
├── agent/                              # Giai đoạn 6 📋 — AI Agent (Agno 6-bước)
│   ├── agent.py                        # create_agent(): LMStudio + ReasoningTools + DB
│   ├── toolkit.py                      # FXToolkit(Toolkit): get_killzone_status/levels/sr/pivot/ml_signal
│   ├── decision_engine.py              # Động cơ Quyết định, chế độ LLM + phương pháp heuristic dự phòng
│   ├── knowledge.py                    # ChromaDB "ml_fx_patterns" — RAG phân tích lịch sử tín hiệu
│   ├── learning.py                     # LearningMachine "ml_fx_learnings" — khả năng tự học của agent
│   └── skills/
│       ├── ict-analysis/
│       │   └── SKILL.md               # Quy luật Killzone, đảo vai trò S/R, chấm điểm độ tự tin
│       └── risk-management/
│           └── SKILL.md               # SL/TP với tỷ số pp_s1/r1, kích thước lệnh dựa theo xếp hạng tự tin
│
├── outputs/                            # Thư mục xuất dữ liệu kết quả tự động
│   ├── reports/                        # Báo cáo Backtest, Bản đồ nhiệt, Đường cong Lợi nhuận
│   └── models/                         # Lưu trữ file cấu hình lưu của các mô hình ML (.json, .joblib), Plot SHAP
│
├── data/
│   ├── raw/                            # Giai đoạn 1 ✅ — Dữ liệu Tick Parquet lấy từ Dukascopy
│   │   ├── XAUUSD/                    
│   │   │   ├── 2015-01.parquet
│   │   │   ├── ...
│   │   │   └── completed_months.json  # Tiến độ tải xuống + số giờ còn thiếu
│   │   └── BTCUSD/                    # Ví dụ thu thập tiền điện tử (Crypto)
│   ├── ohlcv/                         # Giai đoạn 3 — Biên dịch OHLCV (chia theo symbol/khung giờ)
│   ├── features/                      # Giai đoạn 3 — DataFrame chỉ báo (theo symbol/khung giờ)
│   └── labels/                        # Giai đoạn 3 — Dữ liệu đã gán nhãn (MUA/BÁN/ĐI NGANG)
│
├── docs/                               # Hệ thống Tài liệu
│   ├── en/                             # Tài liệu bản Tiếng Anh
│   ├── NOOB_GUIDE.md                  # Hướng dẫn chi tiết nguyên lý (Tiếng Việt)
│   ├── USAGE_GUIDE.md                 
│   ├── TROUBLESHOOTING.md             
│   ├── GLOSSARY.md                    
│   └── TODO.md                        
│
├── main.py                             # 🖥 TUI (Textual) — App terminal dạng 4 tabs: Download | Pipeline | Train | Backtest
├── main.tcss                           # Thiết kế giao diện Textual CSS cho TUI
├── config.toml                         # Thông số cấu hình mặc định (tự động điền trên TUI)
└── pyproject.toml                      # Công cụ cài đặt bằng môi trường Pixi (Polars, TA-Lib, Agno, ChromaDB…)
```

---

## Chỉ báo — Tiền Nguồn Tín Hiệu Đầu Vào

### 1. Vùng Giao Dịch (ICT Killzone) — `indicators/killzone.py`

Được giải thuật và chuyển thể từ mã **ICT Killzone** theo Pine Script.

#### `killzone.py` — API Chính

Giám sát và kẻ vùng **Killzones** — Khung giờ mang tính thanh khoản cao nhất trong quy trình vận hành của ngày:

| Killzone       | Giờ (ET)      | Đặc Điểm                                                               |
| -------------- | ------------- | ---------------------------------------------------------------------- |
| **Châu Á**     | 20:00 – 00:00 | Thanh khoản thấp, thiết lập vùng giá cơ sở cho ngày mới                |
| **Luân Đôn**   | 02:00 – 05:00 | Đột phá mạnh mẽ (Breakout), thường xuyên thiết lập đỉnh/đáy trong ngày |
| **NY AM**      | 09:30 – 11:00 | Các sự kiện kinh tế vĩ mô, truy quét cạn kiệt thanh khoản              |
| **NY Ăn Trưa** | 12:00 – 13:00 | Thanh khoản sụt giảm mạnh, tránh giao dịch                             |
| **NY PM**      | 13:30 – 16:00 | Thường xuất hiện các pha đảo chiều cuối ngày                           |

**Tính Năng Bổ Sung:**
- **Killzone Pivots**: Lấy đỉnh/đáy (High/Low) cho từng phiên, kéo dài vô tận cho đến khi bị giá phá vỡ
- **Mức Cản DWM (Day, Week, Month)**: Theo sát mức giá Mở Cửa (Open), Cao Nhất (High), Thấp Nhất (Low)
- **Mức giá Mở cửa (Opening Prices)**: Các mốc rẽ True Day Open (00:00), 06:00, 10:00, 14:00
- **Dấu mốc thời gian dọc**: Đánh dấu các mốc thời gian quan trọng trong ngày

**Các thuộc tính được máy học trích xuất (ML Features):**
```text
in_{asia,london,nyam,nylunch,nypm}    # Cờ xác nhận phiên Killzone
kz_{name}_high / _low / _mid          # Mức giá trục phân chia cho mỗi phiên
kz_{name}_range / _avg_range          # Độ biến động biên độ trong và N-phiên gần nhất
kz_{name}_session_id                  # Số chỉ mục liên tiếp của phiên
dist_to_{name}_high / _low            # Khoảng cách từ giá close − mức giá trục phiên
d_open / d_high / d_low               # Giá ngày mở cửa, đỉnh/đáy đang trôi
w_open / w_high / w_low               # Giá tuần mở cửa, đỉnh/đáy đang trôi
m_open / m_high / m_low               # Giá tháng mở cửa, đỉnh/đáy đang trôi
pd_high / pd_low                      # Đỉnh/Đáy ngày hôm trước (PDH/PDL)
pw_high / pw_low                      # Đỉnh/Đáy tuần trước
pm_high / pm_low                      # Đỉnh/Đáy tháng trước
```

---

### 2. Hỗ Trợ/Kháng Cự (Support/Resistance) & Các Điểm Cú Quay (Pivot Points) — `indicators/sr_pp.py`

Được giải thuật từ mã kịch bản chỉ báo **SR + PP** thuộc nguồn Pine Script.

#### A. Đặc Vùng Hỗ Trợ/Kháng Cự (Dynamic S/R)

Phát hiện vùng S/R dựa trên các **khuôn mẫu biểu đồ nến**:

| Trùng lặp Khớp | Hình dạng                                     | Nhóm Lớp           |
| -------------- | --------------------------------------------- | ------------------ |
| `r` (1 nến)    | Cây nến giả mạnh đâm thủng phá đáy cũ low[2]  | Kháng Cự (Lực Bán) |
| `r2` (2 nến)   | Hình mẫu 2 nến kép giảm thủng đáy 2 nhịp      | Kháng Cự (Lực Bán) |
| `s` (1 nến)    | Nến tăng cường lực đột phá vỡ đỉnh cũ high[2] | Hỗ Trợ (Lực Mua)   |
| `s2` (2 nến)   | Hình mẫu 2 nến kép tăng thủng đỉnh 2 nhịp     | Hỗ Trợ (Lực Mua)   |

**Vai Trò Đảo Ngược (Role Reversal)**: lúc giá phi thủng bức tường kháng cự → ngưỡng kháng cự đó chính thức đổi vai sang công dụng hỗ trợ ở chu kỳ tiếp theo, và ngược lại.

#### B. Điểm Dừng Định Hướng Trục (Pivot Points Đa Khung)

| Định Dạng Phân Tích    | Giải Thích Thuật Toán & Đặc Điểm                            |
| ---------------------- | ----------------------------------------------------------- |
| **Truyền thống(Trad)** | P = (H+L+C)/3 — Mô Thức Thông Dụng Nhất                     |
| **Fibonacci**          | Sử dụng những mốc quan trọng bậc 0.236, 0.382, 0.618        |
| **Woodie**             | Nhấn mạnh lực giá tác động sát tại đỉnh khép phiên Close    |
| **Classic**            | Tương tự cốt lõi trục quay dòng truyền thống                |
| **DM (DeMark)**        | Rút nhỏ còn 3 Mốc Level cơ bản rủi ro (P, R1, S1)           |
| **Camarilla**          | Chẻ nhỏ 9 lưới chia rẽ hỗ trợ đường biên Intraday hằng ngày |

Thiết Lập Vùng Timeframe Cố Định: Chạy tự động Automatic / Ngày / Tuần / Tháng / Quý / Năm — cho tốc độ lên tới tận **200 đỉnh đáy Pivot xoay vòng trong lịch sử** để theo dõi hồi quy.

**Các thuộc tính được máy học trích xuất (ML Features):**
```text
sr_resist_1bar / sr_resist_2bar        # Hình thức kháng cự 1 / 2 nến
sr_support_1bar / sr_support_2bar      # Hình thức hỗ trợ 1 / 2 nến
nearest_resist_high / _low             # Các mức biên cao/thấp của khu kháng cự đang hoạt động gần nhất
nearest_support_high / _low            # Các mức biên cao/thấp của khu hỗ trợ đang hoạt động gần nhất
in_resist_zone / in_support_zone       # Cờ Boolean Giá hiện đang tiếp xúc nằm ngay trong biên vùng S/R
dist_to_nearest_resist / _support      # Tính toán giá đóng cửa close − vùng ranh giới S/R gần nhất
sr_role_reversal                       # Khớp 0 = trung lập, +1 = Kháng Cự → Hỗ Trợ, -1 = Hỗ Trợ → Kháng Cự
pp_p / pp_r1..r5 / pp_s1..s5           # Dữ liệu xuất từ đường giá trị cấp độ xoay trục phân lô (Pivot P)
pp_dist_to_p / pp_dist_to_r1 / _s1     # Tính toán giá đóng cửa close − vùng ranh giới Pivot Level đang hoạt động
pp_above_p                             # Cờ đánh giá Boolean đường đỉnh Giá hiện đang cao hay thấp hơn mức trục P
```

---

## Hướng Dẫn — Bộ Chỉ báo Python

```python
import polars as pl
from indicators import add_killzone_features, add_sr_pp_features

# Tải dữ liệu tick đã lưu thành OHLCV 1H
df = pl.read_parquet("data/raw/XAUUSD/2024-01.parquet")

# Quy tụ Data thô làm mẫu sang nến 1H OHLCV
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

# Chèn thêm Thông tin định vị đặc trưng ICT Killzone
ohlcv = add_killzone_features(ohlcv, avg_range_n=5)

# Đắp vô đặc trưng cho mô thức S/R và Điểm Quay Trục (Pivot Points)
ohlcv = add_sr_pp_features(ohlcv, pivot_type="traditional", anchor="daily")

print(ohlcv.columns)
```

---

## Dữ Liệu — Thu Thập và Lưu Trữ Trạm Thông Tin

### `download_data.py` — Dữ liệu Tick XAUUSD

Mã Script phục vụ kết nối tự chủ fetch kho dữ liệu biểu **tick (bid/ask)** lấy từ **Dukascopy** (đăng tải từ năm 2015 đổ lại):

| Biến Tham Số (Parameter) | Ý nghĩa Chỉ Dẫn Setup                                                          |
| ------------------------ | ------------------------------------------------------------------------------ |
| Biểu đồ Symbol           | `XAUUSD`                                                                       |
| Nguồn                    | `datafeed.dukascopy.com`                                                       |
| Loại lưu liệu            | `.bi5` (Hệ Nén Nhị Phân Cao LZMA)                                              |
| Lưu Giữ Cấu Trúc         | **Parquet** (Chạy từ Polars, được phân nhóm chia riêng tự động theo các tháng) |
| Lộ trình Trữ ổ đĩa       | `data/raw/XAUUSD/`                                                             |
| Schema                   | `timestamp`, `ask`, `bid`, `ask_volume`, `bid_volume`                          |

**Năng lực của Kịch bản (Script):**
- **Async download** Phương thức đa kết nối tải bất động bộ (`aiohttp`) — Chạy ngầm 20 đường song song, tối ưu siêu tốc
- **Trình Quản lý Hiện Trạng** thông qua hệ thống kiểm thử tự nhận diện tệp `completed_months.json` — Tự động lọc nhận bỏ qua các danh mục tháng nào từng được truy kéo đợt trước.
- **Tự trị Fix lỗi Vấp (Auto-repair)** — nhận ra khoảng chênh vênh số giờ và tự động xin lại bản bổ khuyết ngay giữa khoảng một tháng đang gián đoạn.
- **Tính năng Retry linh động** — Kỹ năng thiết kế tính độ làm trễ theo lũy thừa bù giờ (exponential backoff) vào bất kể khi nào nguồn hệ thống nghẽn tắt.

```bash
# Chuỗi dòng Code khởi chạy tính năng tự lấy rễ dòng Vàng (XAUUSD)
pixi run python pipeline/download_data.py
```

---

## Lộ Trình Ống Luồng Thực Thi ML

```text
Truy Nạp raw Tick → Chỉnh Lý Nến (Resample) → Ghép thẻ Kỹ thuật (Features) → Ghi thẻ nhãn (Labeling)
 (Từ Dukascopy/bi5)   (Bằng Polars/Parquet)    (ICT + S/R + PP)              (MUA/BÁN/ĐI NGANG)
                             ↓
Tiến vào Huấn Luyện → In đồ thị Khảo Sát    → Thư viện Cất Trữ   → Kết Nối AI Bot Giao Dịch
 (XGB/LSTM/KNN)      (Backtest/Đường Vốn)      (Cho mô hình)      (Dùng qua Agno - Tín hiệu Thực)
```

### Cách thức Xếp Hạng Gán Nhãn (Labeling)

- **Mục Định Xét**: Trục chuyển dịch giá thành hướng sau một ngưỡng chuỗi thời gian nến là `N` (Có N = 5, 10, 20)
- **Hạng Tầng (Classes)**: `MUA/LONG (1)`, `BÁN/SHORT (−1)`, `ĐI NGANG/NEUTRAL (0)`
- Nếp điểm kích (Threshhold) được định quy dựa theo **ngưỡng lô-gic cấu trúc ATR filter**

### Các hệ Mô Hình

| Định Danh Mô Hình      | Dựng vào mục tiêu                              |
| ---------------------- | ---------------------------------------------- |
| **KNN**                | Tín hiệu Baseline, phân hạng rèm chắn Killzone |
| **XGBoost / LightGBM** | Thao thức xác suất thống kê quy mô Bảng        |
| **LSTM**               | Mạng Nơ - Phân tuyến trù tính biến dạng Series |

---

## Ứng Dụng Hỗ Trợ 

### Kết Xuất & Dữ Kiện Xử Lý

| Thư Viện Lõi                             | Định Mục                            | Chú Ý Bổ Sung                       |
| ---------------------------------------- | ----------------------------------- | ----------------------------------- |
| **[Polars](https://pola.rs/)**           | DataFrame, Đường ống ETL, Chế trích | Ưu việt đẩy Pandas lùi gấp 10-100x  |
| **[PyArrow](https://arrow.apache.org/)** | Định Hình dữ file lưu Parquet O/I   | Nguồn File thể Hệ Trụ, nén vượt bậc |
| **[TA-Lib](https://ta-lib.org/)**        | Tính toán bộ thông số RSI, EMA, ATR | Dựa trên mã gốc C++, rất lẹ         |
| **[aiohttp](https://docs.aiohttp.org/)** | Truy kích tải tập tin qua Async Web | Mở luân 20 khe truy                 |

### Khối Tính Trực Quan Diễn Nghĩa Hóa

| Dạng Thư Viện            | Tiêu Điểm Mục Tiêu                                   |
| ------------------------ | ---------------------------------------------------- |
| **Plotly**               | Bảng Biểu Nến Tương Tác, Bọc khối S/R & Killzone     |
| **Matplotlib / Seaborn** | Biểu thị sức nặng Tín hiệu, Đường lợi nhuận sinh lời |

### Khối Cấu Kiện Trợ Lý Vô Tri Hữu Ý

| Trụ Cơ Sở                                    | Tiêu Điểm                                                                        |
| -------------------------------------------- | -------------------------------------------------------------------------------- |
| **[Agno](https://github.com/agno-agi/agno)** | Mô Đun thiết kế bot tác nhân (Agent) - Bước lõi sườn LMStudio, Reasoning, Skills |
| **[LM Studio](https://lmstudio.ai/)**        | Mạng chạy cục bộ LLM Offline an toàn, tương thích chuẩn mức OpenAI               |
| **[ChromaDB](https://www.trychroma.com/)**   | Cấu trúc Vector - Tìm lục dữ kiệu Mẫu RAG cũ cho học thuộc vào AI Machine        |

---

## Cài Đặt Khởi Động

```bash
# Quản lý gói mã Python cài nội bộ với Pixi (TUYỆT ĐỐI NÊN DÙNG LÊN HÀNG ĐẦU)
pixi install

# Tải ngay lịch sử XAUUSD từ giai đoạn khởi nguồn năm 2015 (Thông số mặc định)
pixi run python pipeline/download_data.py
```

**Yêu Cầu Nền Tảng**: Python ≥ 3.13, Pixi

---

## 🚀 Quickstart 5 phút với Giao diện Textual

ML_FX có giao diện Terminal tương tác (TUI) được xây dựng bằng [Textual](https://textual.textualize.io/).  
Thay vì gõ lệnh dài, bạn chọn tab, điền form và nhấn nút — log output hiện trực tiếp trên màn hình.

### Chạy TUI

```bash
# Cài đặt môi trường (dành cho lần đầu)
pixi install

# Gõ lệnh để gọi app
pixi run python main.py
```

> **Phím tắt trong màn Console:** `q` — Thoát &nbsp;|&nbsp; `d` — Chuyển đổi Dark/Light mode

### Cấu hình nạp form mặc định (`config.toml`)

Khi app khởi chạy, `main.py` sẽ đọc file `config.toml` ở ngọn cây thư mục và tự động điền số liệu vào bảng (form).  
Sửa file này để thiết định mặc định symbol, timeframe, hay siêu tham số (hyperparameter):

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

### Chạy Luồng Phân Lớp Hoàn Chỉnh (4 Chặng)

| Bước | Diễn Tên Tab        | Chức Trách                                                                            |
| ---- | ------------------- | ------------------------------------------------------------------------------------- |
| 1️⃣    | **📥 Download Data** | Tải luồng tick từ sàn Dukascopy, chọn đồng cặp và mốc thời gian                       |
| 2️⃣    | **🔄 Pipeline**      | Co bó Tick (Resample) → Cấy mã Features → Ấn Chỉ Báo Nhãn (Labeling)                  |
| 3️⃣    | **🧠 Train Model**   | Chọn bộ giải toán (XGBoost/LightGBM), chạy tự phân tích Optuna tuning                 |
| 4️⃣    | **📊 Backtest**      | Kích lệnh walk-forward đánh kiểm, xem kết xuất chỉ báo Sharpe / Sụt vốn Của Tài Khoản |

Toàn bộ các tác vụ xử lý đều chạy nền (ẩn qua background thread) — Hệ thống sẽ hoàn toàn mượt mà chứ không hề bị sập, treo hay đơ (freeze).

---

## Lộ Trình Phát Triển Nâng Cấp (Roadmap)

- [x] Giai đoạn 1: Tuyển mộ hệ nạp Data dòng chạy Tick Data chung vạn năng (`pipeline/download_data.py`)
- [x] Giai đoạn 2: Cấy nhúng thông số nền (ICT Killzone, Các khu Support/Resistance + Các Điểm Quay Pivot)
- [x] Giai đoạn 3: Đường ống trích lọc (ETL) & Lắp đặc tính Nến Feature Pipeline (Săn đúc hơn 130+ giá trị)
- [x] Giai đoạn 4: Đánh Nhãn Mục Đối Tượng + Khởi chạy Model Huấn Luyện (Sử dụng KNN, XGBoost, LSTM)
- [x] Giai đoạn 5: Vận hành cỗ máy Backtesting (Mô phỏng Khớp lệnh tỷ số Lãi/Rủi ro) & Cạo xuất Biểu Đồ (Plotly, Matplotlib)
- [ ] Giai đoạn 6: Khung lưới kiến lập Trí Tuệ (AI Agent Agno) — Chatbot hỗ trợ đọc vị báo hiệu mô hình ra sao
- [ ] Giai đoạn 7: Khuếch trương độ phủ sang nhiều hạng cặp Forex và thị trường Crypto

---

## Tác Giả

**Hieu Nguyen** — [@ultimateBroK](https://github.com/ultimateBroK)  
Phản hồi hoặc Đóng góp: hieuteo03@gmail.com