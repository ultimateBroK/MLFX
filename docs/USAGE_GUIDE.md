# ML_FX — Hướng dẫn Cấu hình & Sử dụng

Hướng dẫn này giải thích **từng tham số** của tất cả công cụ trong ML_FX — từ giao diện TUI (`main.py`) đến từng script CLI.

> 📚 **Lần đầu dùng?** Đọc trước:
> - [NOOB_GUIDE.md](NOOB_GUIDE.md) — Hiểu hệ thống hoạt động thế nào
> - [GLOSSARY.md](GLOSSARY.md) — Giải thích thuật ngữ giao dịch / ML

---

## Mục lục

- [ML\_FX — Hướng dẫn Cấu hình \& Sử dụng](#ml_fx--hướng-dẫn-cấu-hình--sử-dụng)
  - [Mục lục](#mục-lục)
  - [1. Cài đặt môi trường](#1-cài-đặt-môi-trường)
  - [2. Cách nhanh nhất — TUI (`main.py`)](#2-cách-nhanh-nhất--tui-mainpy)
  - [3. Cấu hình `config.toml`](#3-cấu-hình-configtoml)
    - [Các giá trị hợp lệ](#các-giá-trị-hợp-lệ)
  - [4. CLI: Download Data](#4-cli-download-data)
  - [5. CLI: Resample (Tick → OHLCV)](#5-cli-resample-tick--ohlcv)
  - [6. CLI: Feature Engineering](#6-cli-feature-engineering)
  - [7. CLI: Label Generation](#7-cli-label-generation)
  - [8. CLI: Train Model](#8-cli-train-model)
    - [XGBoost / LightGBM](#xgboost--lightgbm)
    - [KNN (Baseline)](#knn-baseline)
    - [LSTM (Deep Learning)](#lstm-deep-learning)
  - [9. CLI: Backtest \& Evaluation](#9-cli-backtest--evaluation)
  - [10. Environment Reproducibility](#10-environment-reproducibility)

---

## 1. Cài đặt môi trường

```bash
# Cài Pixi (lần đầu)
curl -fsSL https://pixi.sh/install.sh | bash

# Cài tất cả dependencies của dự án
pixi install
```

> **Tại sao dùng Pixi?** Pixi lock chính xác version của TA-Lib, Polars, PyTorch, XGBoost vào `pixi.lock`. Ai clone repo về cũng có _đúng_ môi trường.

---

## 2. Cách nhanh nhất — TUI (`main.py`)

Khởi động giao diện Terminal interactive:

```bash
pixi run python main.py
```

| Phím          | Chức năng                |
| ------------- | ------------------------ |
| `q`           | Thoát                    |
| `d`           | Chuyển dark / light mode |
| `Tab` / click | Chuyển tab               |

Giao diện có **4 tab**, mỗi tab tương ứng một bước trong pipeline:

| Tab             | Bước                         |
| --------------- | ---------------------------- |
| 📥 Download Data | Tải tick data từ Dukascopy   |
| 🔄 Pipeline      | Resample → Features → Labels |
| 🧠 Train Model   | Train XGBoost / LightGBM     |
| 📊 Backtest      | Chạy walk-forward backtest   |

Khi nhấn **▶ Run** trên bất kỳ tab nào, task sẽ chạy ngầm — giao diện không bị đơ và log hiện trực tiếp trong panel bên phải.

---

## 3. Cấu hình `config.toml`

File `config.toml` ở thư mục gốc chứa **giá trị mặc định** để TUI tự điền vào form khi khởi động. Sửa file này để thay đổi defaults của bạn.

```toml
# ── Download ──────────────────────────────────────────────────
[download]
symbol      = "XAUUSD"    # Symbol cần tải (xem bảng bên dưới)
asset_class = "fx"        # "fx" (Forex/vàng) | "crypto" (Bitcoin...)
start_year  = 2015        # Năm bắt đầu tải dữ liệu
start_month = 1           # Tháng bắt đầu (1–12)
concurrency = 20          # Số kết nối đồng thời (20 là tối ưu)

# ── Pipeline (Resample + Features + Labels) ───────────────────
[pipeline]
symbol       = "XAUUSD"
timeframe    = "1H"          # Khung thời gian (xem bảng)
pivot_type   = "traditional" # Loại Pivot Point (xem bảng)
pivot_anchor = "daily"       # Anchor TF cho Pivot (xem bảng)

# ── Train Model ───────────────────────────────────────────────
[train]
symbol    = "XAUUSD"
timeframe = "1H"
label_col = "label_10"  # "label_5" | "label_10" | "label_20"
backend   = "xgb"       # "xgb" (XGBoost) | "lgb" (LightGBM)
n_trials  = 30          # Số lần Optuna thử hyperparameter (cao hơn = tốt hơn nhưng lâu hơn)
n_splits  = 5           # Số fold TimeSeriesSplit (CV)

# ── Backtest ──────────────────────────────────────────────────
[backtest]
symbol    = "XAUUSD"
timeframe = "1H"
label_col = "label_10"
```

### Các giá trị hợp lệ

**Symbol (tất cả scripts):**

| Symbol                       | Loại   | Ghi chú                       |
| ---------------------------- | ------ | ----------------------------- |
| `XAUUSD`                     | Vàng   | Default của project           |
| `EURUSD`, `GBPUSD`, `USDJPY` | Forex  | Pairs phổ biến                |
| `BTCUSD`, `ETHUSD`           | Crypto | Dùng `asset_class = "crypto"` |

**Timeframe (`timeframe`):**

| Giá trị       | Ý nghĩa      | Ghi chú                     |
| ------------- | ------------ | --------------------------- |
| `1m`          | 1 phút       | File rất lớn, cần nhiều RAM |
| `5m`          | 5 phút       | Dùng cho scalping           |
| `15m` / `30m` | 15 / 30 phút | Swing intraday              |
| `1H`          | 1 giờ        | **Recommended default**     |
| `2H` / `4H`   | 2 / 4 giờ    | Swing trading               |
| `1D`          | 1 ngày       | Dài hạn                     |

**Label Column (`label_col`):**

| Giá trị    | Ý nghĩa                                   |
| ---------- | ----------------------------------------- |
| `label_5`  | Dự báo 5 nến tới (~5 giờ ở TF=1H)         |
| `label_10` | Dự báo 10 nến tới (~10 giờ) — Recommended |
| `label_20` | Dự báo 20 nến tới (~1 ngày thị trường)    |

**Pivot Type (`pivot_type`):**

| Giá trị       | Mô tả                           |
| ------------- | ------------------------------- |
| `traditional` | `P = (H+L+C)/3` — Phổ biến nhất |
| `fibonacci`   | Mức Fib 0.236 / 0.382 / 0.618   |
| `woodie`      | Nhấn mạnh giá đóng cửa          |
| `classic`     | Classic pivot                   |
| `demark`      | Chỉ 3 level: P, R1, S1          |
| `camarilla`   | 9 mức intraday                  |

**Pivot Anchor (`pivot_anchor`):**

| Giá trị   | Mô tả                              |
| --------- | ---------------------------------- |
| `daily`   | Reset pivot mỗi ngày — Recommended |
| `weekly`  | Reset pivot mỗi tuần               |
| `monthly` | Reset pivot mỗi tháng              |

---

## 4. CLI: Download Data

```bash
pixi run python pipeline/download_data.py [OPTIONS]
```

| Tham số          | Mặc định       | Mô tả                                   |
| ---------------- | -------------- | --------------------------------------- |
| `--symbol`       | `XAUUSD`       | Symbol cần tải                          |
| `--start-year`   | `2015`         | Năm bắt đầu                             |
| `--start-month`  | `1`            | Tháng bắt đầu (1–12)                    |
| `--end-year`     | Năm hiện tại   | Năm kết thúc                            |
| `--end-month`    | Tháng hiện tại | Tháng kết thúc                          |
| `--asset-class`  | `fx`           | `fx` hoặc `crypto`                      |
| `--concurrency`  | `20`           | Số kết nối async song song              |
| `--force-repair` | False          | Bật để kiểm tra lại TẤT CẢ tháng đã tải |

**Ví dụ:**
```bash
# Tải XAUUSD từ 2020 đến nay
pixi run python pipeline/download_data.py --start-year 2020

# Tải Bitcoin (24/7, không bỏ qua cuối tuần)
pixi run python pipeline/download_data.py --symbol BTCUSD --asset-class crypto

# Tải chậm hơn nhưng ổn định hơn (giảm concurrency)
pixi run python pipeline/download_data.py --concurrency 5

# Kiểm tra lại và vá tất cả tháng bị thiếu giờ
pixi run python pipeline/download_data.py --force-repair
```

> 💡 **Lần chạy sau sẽ nhanh hơn nhiều:** Script đọc `data/raw/{symbol}/completed_months.json` và _bỏ qua_ các tháng đã tải xong, chỉ tải các tháng còn thiếu.

---

## 5. CLI: Resample (Tick → OHLCV)

```bash
pixi run python pipeline/resample.py [OPTIONS]
```

| Tham số    | Mặc định   | Mô tả                                                 |
| ---------- | ---------- | ----------------------------------------------------- |
| `--symbol` | `XAUUSD`   | Symbol cần resample                                   |
| `--tf`     | _(tất cả)_ | Một timeframe cụ thể. Bỏ trống = resample tất cả 8 TF |
| `--force`  | False      | Ghi đè các file đã tồn tại                            |

**Ví dụ:**
```bash
# Resample tất cả 8 timeframe (1m, 5m, 15m, 30m, 1H, 2H, 4H, 1D)
pixi run python pipeline/resample.py --symbol XAUUSD

# Chỉ resample 1H
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H

# Regenerate lại từ đầu (xóa cache)
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H --force
```

*Output lưu vào:* `data/ohlcv/{symbol}/{tf}/YYYY-MM.parquet`

---

## 6. CLI: Feature Engineering

```bash
pixi run python pipeline/features.py [OPTIONS]
```

| Tham số    | Mặc định      | Mô tả                                    |
| ---------- | ------------- | ---------------------------------------- |
| `--symbol` | `XAUUSD`      | Symbol                                   |
| `--tf`     | `1H`          | Timeframe (phải có file OHLCV tương ứng) |
| `--pivot`  | `traditional` | Loại Pivot Point                         |
| `--anchor` | `daily`       | Anchor timeframe của Pivot               |
| `--force`  | False         | Ghi đè file đã tồn tại                   |

**Ví dụ:**
```bash
# Features mặc định (133+ cột)
pixi run python pipeline/features.py --symbol XAUUSD --tf 1H

# Dùng Fibonacci pivot với anchor tuần
pixi run python pipeline/features.py --symbol XAUUSD --tf 4H --pivot fibonacci --anchor weekly
```

*Output lưu vào:* `data/features/{symbol}/{tf}/YYYY-MM.parquet`

---

## 7. CLI: Label Generation

```bash
pixi run python pipeline/labels.py [OPTIONS]
```

| Tham số      | Mặc định  | Mô tả                                                                  |
| ------------ | --------- | ---------------------------------------------------------------------- |
| `--symbol`   | `XAUUSD`  | Symbol                                                                 |
| `--tf`       | `1H`      | Timeframe                                                              |
| `--horizons` | `5 10 20` | Danh sách look-ahead horizon (nến)                                     |
| `--atr-mult` | `0.5`     | Hệ số ATR cho ngưỡng LONG/SHORT. Tăng → ít tín hiệu hơn nhưng chắc hơn |
| `--force`    | False     | Ghi đè                                                                 |

**Ví dụ:**
```bash
# Label mặc định (3 horizon: 5, 10, 20 nến)
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H

# Chỉ label 10 nến, ngưỡng ATR cao hơn (ít LONG/SHORT, nhiều NEUTRAL)
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H --horizons 10 --atr-mult 1.0
```

> **`atr-mult` ảnh hưởng gì?**
> - `0.3` → Nhạy — nhiều tín hiệu LONG/SHORT, nhiễu hơn
> - `0.5` → Cân bằng (recommended)
> - `1.0` → Bảo thủ — ít tín hiệu, chỉ bắt move lớn

*Output lưu vào:* `data/labels/{symbol}/{tf}/YYYY-MM.parquet`

---

## 8. CLI: Train Model

### XGBoost / LightGBM

```bash
pixi run python models/gradient_boost.py [OPTIONS]
```

| Tham số     | Mặc định   | Mô tả                                             |
| ----------- | ---------- | ------------------------------------------------- |
| `--symbol`  | `XAUUSD`   | Symbol                                            |
| `--tf`      | `1H`       | Timeframe                                         |
| `--label`   | `label_10` | Cột nhãn mục tiêu                                 |
| `--backend` | `xgb`      | `xgb` (XGBoost) hoặc `lgb` (LightGBM)             |
| `--trials`  | `30`       | Số lần Optuna tune. Tăng → tốt hơn nhưng chậm hơn |
| `--splits`  | `5`        | Số fold TimeSeriesSplit                           |
| `--force`   | False      | Retrain dù model đã tồn tại                       |
| `--no-shap` | False      | Bỏ qua tính SHAP (nhanh hơn)                      |

**Ví dụ:**
```bash
# Train nhanh (ít trials, bỏ SHAP)
pixi run python models/gradient_boost.py --trials 10 --no-shap

# Train kỹ với LightGBM
pixi run python models/gradient_boost.py --backend lgb --trials 100 --splits 7

# Retrain lại từ đầu
pixi run python models/gradient_boost.py --force
```

### KNN (Baseline)

```bash
pixi run python models/knn.py [OPTIONS]
```

| Tham số    | Mặc định   | Mô tả                                                 |
| ---------- | ---------- | ----------------------------------------------------- |
| `--symbol` | `XAUUSD`   | Symbol                                                |
| `--tf`     | `1H`       | Timeframe                                             |
| `--label`  | `label_10` | Cột nhãn                                              |
| `--k`      | `10`       | Số neighbors (K). Giảm → nhạy hơn, tăng → ổn định hơn |

### LSTM (Deep Learning)

```bash
pixi run python models/lstm.py [OPTIONS]
```

| Tham số        | Mặc định   | Mô tả                                           |
| -------------- | ---------- | ----------------------------------------------- |
| `--symbol`     | `XAUUSD`   | Symbol                                          |
| `--tf`         | `1H`       | Timeframe                                       |
| `--label`      | `label_10` | Cột nhãn                                        |
| `--epochs`     | `50`       | Số epoch train. Tăng → học lâu hơn              |
| `--seq-len`    | `50`       | Độ dài sequence input (số nến/step). Thử 50–200 |
| `--batch-size` | `64`       | Batch size. Giảm nếu hết RAM GPU                |

### BiLSTM (Deep Learning - Bidirectional)

```bash
pixi run python models/bilstm.py [OPTIONS]
```

| Tham số        | Mặc định   | Mô tả                                           |
| -------------- | ---------- | ----------------------------------------------- |
| `--symbol`     | `XAUUSD`   | Symbol                                          |
| `--tf`         | `1H`       | Timeframe                                       |
| `--label`      | `label_10` | Cột nhãn                                        |
| `--force`      | False      | Bắt buộc retrain dù model đã tồn tại            |

---

## 9. CLI: Backtest & Evaluation

```bash
pixi run python eval/run_eval.py [OPTIONS]
```

| Tham số   | Ví dụ                                   | Mô tả                              |
| --------- | --------------------------------------- | ---------------------------------- |
| `--data`  | `data/labels/XAUUSD/1H/2026-02.parquet` | File dữ liệu đã label              |
| `--label` | `label_5`                               | Cột nhãn dùng để đánh giá          |
| `--tp`    | `1.5`                                   | Take Profit (tính theo R-multiple) |
| `--sl`    | `1.0`                                   | Stop Loss (tính theo R-multiple)   |

**Ví dụ:**
```bash
# Backtest với Risk:Reward = 1:1.5
pixi run python eval/run_eval.py \
  --data data/labels/XAUUSD/1H/2026-02.parquet \
  --label label_5 --tp 1.5 --sl 1.0
```

*Output:* Metrics in-terminal + biểu đồ trong `outputs/reports/`

---

## 10. Environment Reproducibility

Dự án dùng 2 file để đảm bảo _ai cũng chạy được_:

| File             | Vai trò                                |
| ---------------- | -------------------------------------- |
| `pyproject.toml` | Khai báo dependencies và version range |
| `pixi.lock`      | Lock chính xác version của mọi package |

**Luôn commit `pixi.lock` lên Git** để đồng nghiệp clone về không bị lỗi version.

```bash
# Cài lại đúng môi trường từ lock file (không cập nhật gì)
pixi install

# Cập nhật tất cả packages lên version mới nhất (tạo pixi.lock mới)
pixi update
```

> ⚠️ Sau khi `pixi update`, hãy chạy `pixi run pytest` để chắc chắn không có breaking change.
