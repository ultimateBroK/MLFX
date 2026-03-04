# Hướng Dẫn Sử Dụng ML_FX Pipeline

Dự án này là một Data Pipeline và Machine Learning Engine chuyên biệt cho việc giao dịch **XAUUSD (Vàng)**. Tất cả các script đều được quản lý tự động bởi `pixi` và Polars, giúp xử lý hàng chục năm tick data chỉ tóm gọn trong RAM laptop.

---

## 1. Cài đặt Môi trường (Cần thiết trước khi chạy)

Sử dụng `pixi` (Rust-based package manager) để xử lý toàn bộ các package, không cần quan tâm đến `pip` hay `conda`.

```bash
# Cài đặt Pixi (nếu chưa có)
curl -fsSL https://pixi.sh/install.sh | bash

# Cài đặt toàn bộ lib & pull môi trường dự án
pixi install
```

---

## 2. Quy trình 4 Bước: Từ Dữ liệu Thô đến AI Model

### Bước 1: Thu thập Dữ liệu (Dukascopy)
Tải toàn bộ tick data thô của XAUUSD. Dữ liệu sẽ tự động lưu tải đa luồng thành các tệp Parquet theo tháng ở thư mục `data/raw/XAUUSD/`.

```bash
# Chạy download
pixi run python pipeline/download_gold.py
```
> *Tips*: Hỗ trợ dừng lại giữa chừng và chạy tiếp. Tiến độ được lưu ở file `completed_months.json`.

---

### Bước 2: Resample (Tick → Nến OHLCV)
Dữ liệu tick không thể train ML trực tiếp, nó phải được chuyển đổi thành khung thời gian (Timeframe). Module này tự động nhận diện và nhảy qua các bước "Gap cuối tuần" (Weekend Gaps), giảm sát dữ liệu lỗi.

```bash
# Resample 10 năm tick data thành nến 1H (1 tiếng)
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H

# Hoặc resample nhiều khung thời gian cùng lúc
pixi run python pipeline/resample.py --symbol XAUUSD --tf 5m
```
*Kết quả xuất ra thư mục*: `data/ohlcv/XAUUSD/1H/`

---

### Bước 3: Feature Engineering (Tính toán các chỉ báo)
Tạo ra **133 features** dùng làm bối cảnh để Agent/Bot Machine Learning học phân tích kỹ thuật (Technical Analysis):
* Cụm Trend: RSI, MACD, EMA.
* Cụm Cấu trúc: Pivot S/R (Kháng cự/Hỗ trợ theo Rvol).
* Cụm ICT (Smart Money Concept): Order Blocks, Fair Value Gaps, và Session Killzones (Asian, London, NY).

```bash
pixi run python pipeline/features.py --symbol XAUUSD --tf 1H
```
*Kết quả xuất ra thư mục*: `data/features/XAUUSD/1H/`

---

### Bước 4: Labeling (Gán nhãn)
Chúng ta cần phải dạy cho Model biết "Sau cây nến này, giá sẽ lên hay xuống?".
Labeling sử dụng **Band ATR** (ví dụ: ATR_14 * 0.5) để loại bỏ các vùng sideway "nhiễu".

* **`+1`**: LONG (Giá trị sau đó tăng vượt kháng cự)
* **`-1`**: SHORT (Giá trị sau đó sụt giảm thủng hỗ trợ)
* **`0`**: NEUTRAL (Giá giậm chân tại chỗ đi ngang, bỏ qua trade)

```bash
# Label tương lai của 5, 10, và 20 nến tiếp theo
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H --horizons 5 10 20
```
*Kết quả xuất ra thư mục*: `data/labels/XAUUSD/1H/`

---

## 3. Train Mô hình Machine Learning (AI)

Sau khi có Label, chạy trực tiếp các tệp Machine Learnings sau, chúng sẽ tự động dò tìm Hyperparameters bằng **Optuna** và áp dụng TimeSeriesSplit (tránh việc "nhìn trộm tương lai" - Lookahead Bias):

```bash
# Chế độ Baseline dễ dàng diễn giải nhưng giới hạn hiệu suất: KNN
pixi run python models/knn.py --symbol XAUUSD --tf 1H --label label_10 --k 10

# Chế độ Deep Tree cực mạnh: XGBoost hoặc LightGBM
pixi run python models/gradient_boost.py --symbol XAUUSD --tf 1H --label label_10 --backend xgb --trials 30

# Chế độ Nhận diện Mẫu Dáng (Sequence) cho chuỗi nến: LSTM (PyTorch)
pixi run python models/lstm.py --symbol XAUUSD --tf 1H --label label_10 --epochs 50 --seq-len 50
```

> **Làm sao để biết Model chạy tốt hay không?**
> System tự động trích xuất các bức ảnh `Feature Importance` và bảng phân tích giá trị `SHAP Values` vào mục `models/saved/XAUUSD/1H/`. Nó sẽ chỉ cho bạn biết *Điều kiện gì khiến bot quyết định đó là lệnh Buy, điều kiện gì quyết định nó là lệnh Sell*.

---

## 4. Backtest & Vẽ biểu đồ hiệu suất (Evaluation)

Sau khi tạo mô hình, đưa dự đoán hoặc nhãn vào Backtester để giả lập Trade thực tế bằng luật Risk:Reward (Ví dụ Risk 1R, target Reward 1.5R):

Đọc [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) để biết cách chạy báo cáo Performance (Gồm *HTML Candlestick*, *Equity Max Drawdown* và *Session Radar*).
