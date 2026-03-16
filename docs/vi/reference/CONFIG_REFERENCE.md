# MLFX - Tham chiếu cấu hình

Tài liệu này là bản tham chiếu đầy đủ cho `config.toml` và các cờ dòng lệnh tương ứng trong MLFX.

---

## Tài liệu liên quan

- [Cổng tài liệu tiếng Việt](../README.md)
- [Bắt đầu nhanh](../getting-started/QUICKSTART.md)
- [Hướng dẫn cấu hình và sử dụng](../guides/USAGE_GUIDE.md)
- [Hướng dẫn đánh giá](../guides/EVALUATION_GUIDE.md)
- [Kiến trúc hệ thống](../architecture/ARCHITECTURE.md)
- [Tham chiếu đặc trưng](FEATURE_REFERENCE.md)

---

## 1. Tổng quan

MLFX sử dụng mô hình cấu hình hai lớp:

1. **`config.toml`** — nơi khai báo các giá trị mặc định cho toàn bộ dự án
2. **Cờ dòng lệnh** — dùng để ghi đè các giá trị mặc định cho từng lần chạy

Giao diện dòng lệnh sẽ tự động đọc `config.toml` trong thư mục gốc của dự án. Nếu bạn truyền tham số trực tiếp trên dòng lệnh, giá trị đó sẽ **được ưu tiên cao hơn** cấu hình trong tệp.

---

## 2. Các phần trong `config.toml`

## 2.1. `[download]` — Tải dữ liệu đầu vào

| Khóa | Kiểu | Mặc định | Cờ dòng lệnh tương ứng | Mô tả |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Mã công cụ tài chính cần tải |
| `asset_class` | string | `"fx"` | `--asset-class` | Nhóm tài sản: `"fx"`, `"crypto"` |
| `start_year` | integer | `2015` | `--start-year` | Năm bắt đầu tải |
| `start_month` | integer | `1` | `--start-month` | Tháng bắt đầu tải (`1-12`) |
| `end_year` | integer | năm hiện tại | `--end-year` | Năm kết thúc tải |
| `end_month` | integer | tháng hiện tại | `--end-month` | Tháng kết thúc tải |
| `concurrency` | integer | `20` | `--concurrency` | Số tiến trình tải song song |

### Ví dụ

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

## 2.2. `[pipeline]` — Cấu hình xử lý dữ liệu, đặc trưng và nhãn

| Khóa | Kiểu | Mặc định | Cờ dòng lệnh tương ứng | Mô tả |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Mã công cụ tài chính cần xử lý |
| `tf` | string | `"1H"` | `--tf` | Khung thời gian mục tiêu |
| `pivot_type` | string | `"traditional"` | `--pivot` | Phương pháp tính điểm xoay |
| `pivot_anchor` | string | `"daily"` | `--anchor` | Chu kỳ neo điểm xoay |
| `atr_period` | integer | `14` | `--atr-period` | Chu kỳ tính ATR |
| `atr_mult` | float | `0.5` | `--atr-mult` | Hệ số ATR dùng khi tạo nhãn |

### Các phương pháp điểm xoay được hỗ trợ

- `traditional`
- `fibonacci`
- `woodie`
- `classic`
- `demark`
- `camarilla`

### Các chu kỳ neo được hỗ trợ

- `daily`
- `weekly`
- `monthly`

### Các khung thời gian thường dùng

- `1m`
- `5m`
- `15m`
- `30m`
- `1H`
- `2H`
- `4H`
- `1D`

### Ví dụ

```toml
[pipeline]
symbol = "XAUUSD"
tf = "1H"
pivot_type = "traditional"
pivot_anchor = "daily"
atr_mult = 0.5
```

---

## 2.3. `[train]` — Cấu hình huấn luyện

| Khóa | Kiểu | Mặc định | Cờ dòng lệnh tương ứng | Mô tả |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Mã công cụ tài chính dùng để huấn luyện |
| `tf` | string | `"1H"` | `--tf` | Khung thời gian dùng để huấn luyện |
| `label` | string | `"label_10"` | `--label` | Cột nhãn mục tiêu |
| `backend` | string | `"mlf"` | `--backend` | Bộ máy huấn luyện |
| `n_trials` | integer | `30` | `--n-trials` | Số lần thử siêu tham số, chủ yếu áp dụng cho `mlf` |
| `n_splits` | integer | `5` | `--n-splits` | Số phần chia trong kiểm định chéo |
| `random_seed` | integer | `42` | — | Hạt giống ngẫu nhiên để tái tạo kết quả |
| `train_start` | string | `null` | `--train-start` | Ngày bắt đầu huấn luyện (định dạng YYYYMMDD) |
| `train_end` | string | `null` | `--train-end` | Ngày kết thúc huấn luyện (định dạng YYYYMMDD) |
| `force` | boolean | `false` | `--force` | Huấn luyện lại ngay cả khi mô hình đã tồn tại |

### Các bộ máy được hỗ trợ

- `mlf`
- `lstm`
- `sgd`
- `stats`

### Các nhãn được hỗ trợ

- `label_5`
- `label_10`
- `label_20`

### Ví dụ

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

## 2.4. `[benchmark]` — So sánh nhiều bộ máy

| Khóa | Kiểu | Mặc định | Cờ dòng lệnh tương ứng | Mô tả |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Mã công cụ tài chính |
| `tf` | string | `"1H"` | `--tf` | Khung thời gian |
| `label` | string | `"label_10"` | `--label` | Cột nhãn mục tiêu |
| `backends` | list | `["mlf", "sgd", "stats"]` | `--backends` | Danh sách bộ máy cần so sánh |
| `n_trials` | integer | `5` | `--n-trials` | Số lần thử siêu tham số cho mỗi bộ máy |
| `n_splits` | integer | `3` | `--n-splits` | Số phần chia trong kiểm định chéo |
| `train_start` | string | `null` | `--train-start` | Ngày bắt đầu huấn luyện (định dạng YYYYMMDD) |
| `train_end` | string | `null` | `--train-end` | Ngày kết thúc huấn luyện (định dạng YYYYMMDD) |
| `force` | boolean | `false` | `--force` | Huấn luyện lại tất cả bộ máy |

### Ví dụ

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

## 2.5. `[features]` — Cấu hình xây dựng đặc trưng

| Khóa | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| `rsi_period` | integer | `14` | Chu kỳ tính RSI |
| `atr_period` | integer | `14` | Chu kỳ tính ATR |
| `ema_periods` | list | `[20, 50, 200]` | Danh sách EMA cần tạo |
| `macd_fast` | integer | `12` | Chu kỳ EMA nhanh của MACD |
| `macd_slow` | integer | `26` | Chu kỳ EMA chậm của MACD |
| `macd_signal` | integer | `9` | Chu kỳ đường tín hiệu của MACD |
| `avg_range_n` | integer | `5` | Số phiên dùng để tính biên độ trung bình của khung giờ trọng điểm |

### Ví dụ

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

## 2.6. `[qa]` — Kiểm tra chất lượng dữ liệu

| Khóa | Kiểu | Mặc định | Cờ dòng lệnh tương ứng | Mô tả |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Mã công cụ tài chính cần kiểm tra |
| `asset_class` | string | `"fx"` | `--asset-class` | Nhóm tài sản: `"fx"`, `"crypto"` |

### Ví dụ

```toml
[qa]
symbol = "XAUUSD"
asset_class = "fx"
```

---

## 2.7. `[serve]` — Máy chủ suy luận FastAPI

| Khóa | Kiểu | Mặc định | Cờ dòng lệnh tương ứng | Mô tả |
|---|---|---|---|---|
| `host` | string | `"0.0.0.0"` | `--host` | Địa chỉ kết nối cho máy chủ API |
| `port` | integer | `8000` | `--port` | Cổng cho máy chủ API |
| `reload` | boolean | `false` | `--reload` | Bật tự động tải lại cho phát triển |

### Ví dụ

```toml
[serve]
host = "0.0.0.0"
port = 8000
reload = false
```

---

## 2.8. `[batch_predict]` — Cấu hình suy luận hàng loạt

| Khóa | Kiểu | Mặc định | Cờ dòng lệnh tương ứng | Mô tả |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Mã công cụ tài chính |
| `tf` | string | `"1H"` | `--tf` | Khung thời gian |
| `label` | string | `"label_10"` | `--label` | Cột nhãn tương ứng với mô hình |

### Ví dụ

```toml
[batch_predict]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
```

---

## 2.9. `[drift]` — Phát hiện độ lệch đặc trưng

| Khóa | Kiểu | Mặc định | Cờ dòng lệnh tương ứng | Mô tả |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Mã công cụ tài chính |
| `tf` | string | `"1H"` | `--tf` | Khung thời gian |
| `label` | string | `"label_10"` | `--label` | Cột nhãn |
| `threshold_ks` | float | `0.1` | `--threshold-ks` | Ngưỡng kiểm định Kolmogorov-Smirnov |
| `threshold_psi` | float | `0.2` | `--threshold-psi` | Ngưỡng PSI (Population Stability Index) |
| `min_samples` | integer | `30` | `--min-samples` | Số mẫu tối thiểu cho mỗi đặc trưng khi kiểm tra độ lệch |

### Ví dụ

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

## 2.10. `[backtest]` — Cấu hình đánh giá và mô phỏng giao dịch

| Khóa | Kiểu | Mặc định | Cờ dòng lệnh tương ứng | Mô tả |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Mã công cụ tài chính cần đánh giá |
| `tf` | string | `"1H"` | `--tf` | Khung thời gian backtest |
| `label` | string | `"label_10"` | `--label` | Cột tín hiệu dùng để backtest |
| `tp_r` | float | `1.5` | `--tp` | Mức chốt lời theo đơn vị `R` |
| `sl_r` | float | `1.0` | `--sl` | Mức dừng lỗ theo đơn vị `R` |
| `initial_capital` | float | `10000.0` | `--capital` | Vốn ban đầu |
| `risk_pct` | float | `1.0` | `--risk` | Phần trăm vốn rủi ro mỗi lệnh |
| `commission` | float | `0.1` | `--commission` | Chi phí hoa hồng mỗi lệnh |
| `slippage` | float | `0.0` | `--slippage` | Trượt giá giả lập |
| `eval_start` | string | `null` | `--eval-start` | Ngày bắt đầu đánh giá (định dạng YYYYMMDD) |
| `eval_end` | string | `null` | `--eval-end` | Ngày kết thúc đánh giá (định dạng YYYYMMDD) |
| `use_labels` | boolean | `false` | `--use-labels` | Backtest trực tiếp trên nhãn, bỏ qua mô hình |

### Ví dụ

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

## 2.11. `[profiles]` — Hồ sơ quy trình

Hồ sơ quy trình cho phép bạn xác định các cấu hình đặt trước cho các lệnh train, evaluate và benchmark. Mỗi hồ sơ có thể chứa các phần con cho từng loại lệnh.

### Cấu trúc hồ sơ

```toml
[profiles.{tên}.train]      # Cấu hình đặt trước cho huấn luyện
[profiles.{tên}.evaluate]   # Cấu hình đặt trước cho đánh giá
[profiles.{tên}.benchmark]  # Cấu hình đặt trước cho benchmark
```

### Phần train của hồ sơ

| Khóa | Kiểu | Mô tả |
|---|---|---|
| `symbol` | string | Mã công cụ tài chính |
| `tf` | string | Khung thời gian |
| `label` | string | Cột nhãn mục tiêu |
| `backend` | string | Bộ máy huấn luyện |
| `n_trials` | integer | Số lần thử siêu tham số |
| `n_splits` | integer | Số phần chia trong kiểm định chéo |
| `train_start` | string | Ngày bắt đầu huấn luyện (YYYYMMDD) |
| `train_end` | string | Ngày kết thúc huấn luyện (YYYYMMDD) |

### Phần evaluate của hồ sơ

| Khóa | Kiểu | Mô tả |
|---|---|---|
| `symbol` | string | Mã công cụ tài chính |
| `tf` | string | Khung thời gian |
| `label` | string | Cột tín hiệu |
| `tp_r` | float | Mức chốt lời theo R |
| `sl_r` | float | Mức dừng lỗ theo R |
| `initial_capital` | float | Vốn ban đầu |
| `risk_pct` | float | Phần trăm rủi ro mỗi lệnh |
| `commission` | float | Hoa hồng mỗi lệnh |
| `slippage` | float | Trượt giá giả lập |
| `eval_start` | string | Ngày bắt đầu đánh giá (YYYYMMDD) |
| `eval_end` | string | Ngày kết thúc đánh giá (YYYYMMDD) |

### Phần benchmark của hồ sơ

| Khóa | Kiểu | Mô tả |
|---|---|---|
| `symbol` | string | Mã công cụ tài chính |
| `tf` | string | Khung thời gian |
| `label` | string | Cột nhãn mục tiêu |
| `backends` | list | Danh sách bộ máy cần so sánh |
| `n_trials` | integer | Số lần thử cho mỗi bộ máy |
| `n_splits` | integer | Số phần chia trong kiểm định chéo |
| `train_start` | string | Ngày bắt đầu huấn luyện (YYYYMMDD) |
| `train_end` | string | Ngày kết thúc huấn luyện (YYYYMMDD) |

### Ví dụ

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

### Sử dụng hồ sơ

```bash
# Huấn luyện sử dụng hồ sơ
pixi run mlfx train --profile research

# Đánh giá sử dụng hồ sơ
pixi run mlfx evaluate --profile research

# Benchmark sử dụng hồ sơ
pixi run mlfx benchmark --profile benchmark_fast

# Chạy train + evaluate từ hồ sơ
pixi run mlfx run-profile --profile research
```

---

## 2.12. `[mlflow]` — Cấu hình MLflow (tùy chọn)

MLflow được cấu hình chủ yếu qua biến môi trường thay vì `config.toml`. Điều này cho phép triển khai linh hoạt trên các môi trường khác nhau.

### Biến môi trường

| Biến | Mặc định | Mô tả |
|---|---|---|
| `MLFLOW_TRACKING_URI` | `sqlite:///mlflow.db` | URI máy chủ theo dõi MLflow |
| `MLFLOW_ARTIFACT_ROOT` | `outputs/mlflow_artifacts/` | Thư mục gốc lưu artifact |
| `MLFLOW_REGISTRY_URI` | (giống tracking URI) | URI sổ đăng ký mô hình |

### Các định dạng Tracking URI được hỗ trợ

- **SQLite (khuyến nghị)**: `sqlite:///mlflow.db`
- **Thư mục cục bộ**: `file:///path/to/mlruns`
- **Máy chủ HTTP**: `http://localhost:5000`
- **Databricks**: `databricks`

### Ví dụ

```bash
# Thiết lập biến môi trường
export MLFLOW_TRACKING_URI="http://mlflow.example.com:5000"
export MLFLOW_ARTIFACT_ROOT="/mnt/shared/artifacts"

# Chạy huấn luyện với theo dõi MLflow
pixi run mlfx train --symbol XAUUSD --tf 1H
```

---

## 3. Tham chiếu biến môi trường

Ngoài `config.toml`, MLFX hỗ trợ biến môi trường cho cấu hình thời gian chạy:

### Biến môi trường dự án

| Biến | Mô tả |
|---|---|
| `MLFX_DATA_ROOT` | Ghi đè thư mục dữ liệu |
| `MLFX_OUTPUTS_ROOT` | Ghi đè thư mục outputs |

### Biến môi trường MLflow

| Biến | Mặc định | Mô tả |
|---|---|---|
| `MLFLOW_TRACKING_URI` | `sqlite:///mlflow.db` | URI máy chủ theo dõi MLflow |
| `MLFLOW_ARTIFACT_ROOT` | `outputs/mlflow_artifacts/` | Thư mục gốc lưu artifact |
| `MLFLOW_REGISTRY_URI` | (giống tracking URI) | URI sổ đăng ký mô hình |

---

## 4. Ví dụ `config.toml` hoàn chỉnh

```toml
# Cấu hình MLFX
# File này được CLI `mlfx` tự động đọc.
# Hãy chỉnh các giá trị mặc định để phù hợp quy trình của bạn.

[download]
symbol      = "XAUUSD"
asset_class = "fx"
start_year  = 2015
start_month = 1
concurrency = 20

[pipeline]
symbol       = "XAUUSD"
tf           = "1H"
pivot_type   = "traditional"
pivot_anchor = "daily"
atr_period   = 14
atr_mult     = 0.5

[train]
symbol       = "XAUUSD"
tf           = "1H"
label        = "label_10"
backend      = "mlf"
n_trials     = 15
n_splits     = 5
random_seed  = 42
train_start  = null
train_end    = null
force        = false

[benchmark]
symbol      = "XAUUSD"
tf          = "1H"
label       = "label_10"
backends    = ["mlf", "sgd", "stats"]
n_trials    = 5
n_splits    = 3
train_start = null
train_end   = null
force       = false

[features]
rsi_period  = 14
atr_period  = 14
ema_periods = [20, 50, 200]
macd_fast   = 12
macd_slow   = 26
macd_signal = 9
avg_range_n = 5

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
symbol        = "XAUUSD"
tf            = "1H"
label         = "label_10"
threshold_ks  = 0.1
threshold_psi = 0.2
min_samples   = 30

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
eval_start      = null
eval_end        = null
use_labels      = false

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

---

## 5. Tham chiếu các cờ dòng lệnh

## 5.1. Cờ dùng chung

Các lệnh chính đều hỗ trợ:

| Cờ | Mô tả |
|---|---|
| `--help` | Hiển thị trợ giúp của lệnh |
| `--version` | Hiển thị phiên bản hiện tại |

---

## 5.2. `download`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ cấu hình | Mã công cụ tài chính |
| `--asset-class` | từ cấu hình | Nhóm tài sản |
| `--start-year` | từ cấu hình | Năm bắt đầu |
| `--start-month` | từ cấu hình | Tháng bắt đầu |
| `--end-year` | năm hiện tại | Năm kết thúc |
| `--end-month` | tháng hiện tại | Tháng kết thúc |
| `--concurrency` | từ cấu hình | Số tiến trình song song |
| `--force` | `false` | Tải lại tháng đã tồn tại |
| `--skip-current-month` | `false` | Bỏ qua kiểm tra tháng hiện tại |

---

## 5.3. `pipeline`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ cấu hình | Mã cần xử lý |
| `--tf` | từ cấu hình | Khung thời gian, có thể truyền nhiều giá trị |
| `--pivot` | từ cấu hình | Phương pháp tính điểm xoay |
| `--anchor` | từ cấu hình | Chu kỳ neo điểm xoay |
| `--atr-period` | từ cấu hình | Chu kỳ ATR |
| `--atr-mult` | từ cấu hình | Hệ số ATR dùng để tạo nhãn |
| `--force` | `false` | Ghi đè tệp đã tồn tại |
| `--skip-resample` | `false` | Bỏ qua bước tạo OHLCV |
| `--skip-features` | `false` | Bỏ qua bước xây dựng đặc trưng |
| `--skip-labels` | `false` | Bỏ qua bước tạo nhãn |

---

## 5.4. `train`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ cấu hình | Mã dùng để huấn luyện |
| `--tf` | từ cấu hình | Khung thời gian |
| `--label` | từ cấu hình | Cột nhãn |
| `--backend` | từ cấu hình | Bộ máy huấn luyện |
| `--n-trials` | từ cấu hình | Số lần thử siêu tham số |
| `--n-splits` | từ cấu hình | Số phần chia trong kiểm định chéo |
| `--train-start` | từ cấu hình | Ngày bắt đầu huấn luyện (YYYYMMDD) |
| `--train-end` | từ cấu hình | Ngày kết thúc huấn luyện (YYYYMMDD) |
| `--profile` | không có | Tên hồ sơ cấu hình để sử dụng |
| `--force` | `false` | Huấn luyện lại dù tệp đầu ra đã tồn tại |

---

## 5.5. `evaluate`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ cấu hình | Mã cần đánh giá |
| `--tf` | từ cấu hình | Khung thời gian |
| `--label` | từ cấu hình | Cột tín hiệu |
| `--capital` | từ cấu hình | Vốn ban đầu |
| `--risk` | từ cấu hình | Phần trăm rủi ro mỗi lệnh |
| `--commission` | từ cấu hình | Hoa hồng mỗi lệnh |
| `--tp` | từ cấu hình | Mức chốt lời theo `R` |
| `--sl` | từ cấu hình | Mức dừng lỗ theo `R` |
| `--slippage` | từ cấu hình | Mức trượt giá giả lập |
| `--eval-start` | từ cấu hình | Ngày bắt đầu đánh giá (YYYYMMDD) |
| `--eval-end` | từ cấu hình | Ngày kết thúc đánh giá (YYYYMMDD) |
| `--profile` | không có | Tên hồ sơ cấu hình để sử dụng |
| `--use-labels` | `false` | Chỉ kiểm định trực tiếp trên nhãn, bỏ qua mô hình |

---

## 5.6. `benchmark`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ cấu hình | Mã công cụ tài chính |
| `--tf` | từ cấu hình | Khung thời gian |
| `--label` | từ cấu hình | Cột nhãn mục tiêu |
| `--backends` | từ cấu hình | Danh sách bộ máy cần so sánh |
| `--n-trials` | từ cấu hình | Số lần thử cho mỗi bộ máy |
| `--n-splits` | từ cấu hình | Số phần chia trong kiểm định chéo |
| `--train-start` | từ cấu hình | Ngày bắt đầu huấn luyện (YYYYMMDD) |
| `--train-end` | từ cấu hình | Ngày kết thúc huấn luyện (YYYYMMDD) |
| `--profile` | không có | Tên hồ sơ cấu hình để sử dụng |
| `--force` | `false` | Huấn luyện lại tất cả bộ máy |

---

## 5.7. `serve`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--host` | `0.0.0.0` | Địa chỉ kết nối cho máy chủ API |
| `--port` | `8000` | Cổng chạy API suy luận |
| `--reload` | `false` | Bật tự động tải lại cho phát triển |

---

## 5.8. `batch-predict`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ cấu hình | Mã cần dự đoán |
| `--tf` | từ cấu hình | Khung thời gian |
| `--label` | từ cấu hình | Cột nhãn tương ứng với mô hình |

---

## 5.9. `drift`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ cấu hình | Mã cần kiểm tra độ lệch |
| `--tf` | từ cấu hình | Khung thời gian |
| `--label` | từ cấu hình | Cột nhãn |
| `--threshold-ks` | `0.1` | Ngưỡng kiểm định KS |
| `--threshold-psi` | `0.2` | Ngưỡng PSI |
| `--min-samples` | `30` | Số mẫu tối thiểu cho mỗi đặc trưng |

---

## 5.10. `drift-retrain`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ cấu hình | Mã công cụ tài chính |
| `--tf` | từ cấu hình | Khung thời gian |
| `--label` | từ cấu hình | Cột nhãn |
| `--backend` | từ cấu hình | Bộ máy huấn luyện |
| `--n-trials` | từ cấu hình | Số lần thử siêu tham số |
| `--n-splits` | từ cấu hình | Số phần chia trong kiểm định chéo |
| `--train-start` | từ cấu hình | Ngày bắt đầu huấn luyện (YYYYMMDD) |
| `--train-end` | từ cấu hình | Ngày kết thúc huấn luyện (YYYYMMDD) |
| `--profile` | không có | Tên hồ sơ cấu hình để sử dụng |
| `--force` | `false` | Huấn luyện lại nếu phát hiện độ lệch |
| `--threshold-ks` | `0.1` | Ngưỡng kiểm định KS |
| `--threshold-psi` | `0.2` | Ngưỡng PSI |
| `--min-samples` | `30` | Số mẫu tối thiểu cho mỗi đặc trưng |

---

## 5.11. `models`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | không có | Lọc theo mã |
| `--tf` | không có | Lọc theo khung thời gian |
| `--backend` | không có | Lọc theo bộ máy |

---

## 5.12. `profiles`

Liệt kê tất cả hồ sơ quy trình có sẵn trong cấu hình.

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--profile` | không có | Hiển thị chi tiết một hồ sơ cụ thể |

---

## 5.13. `run-profile`

Chạy train + evaluate từ một hồ sơ cấu hình.

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--profile` | bắt buộc | Tên hồ sơ cấu hình để sử dụng |
| `--skip-train` | `false` | Bỏ qua bước huấn luyện |
| `--skip-evaluate` | `false` | Bỏ qua bước đánh giá |
| `--skip-benchmark` | `false` | Bỏ qua bước benchmark (nếu có trong hồ sơ) |
| `--json` | `false` | Xuất tóm tắt chạy dạng JSON |

---

## 5.14. `run-all`

Chạy toàn bộ quy trình từ đầu đến cuối: download → pipeline → train → evaluate.

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--profile` | không có | Sử dụng hồ sơ cấu hình cho train/evaluate/benchmark |
| `--skip-download` | `false` | Bỏ qua bước tải dữ liệu |
| `--skip-qa` | `false` | Bỏ qua bước QA |
| `--skip-pipeline` | `false` | Bỏ qua bước xử lý dữ liệu |
| `--skip-train` | `false` | Bỏ qua bước huấn luyện |
| `--skip-evaluate` | `false` | Bỏ qua bước đánh giá |
| `--skip-benchmark` | `false` | Bỏ qua bước benchmark |
| `--skip-serve` | `false` | Bỏ qua bước serve placeholder |
| `--skip-batch` | `false` | Bỏ qua bước dự đoán theo lô |
| `--skip-drift-retrain` | `false` | Bỏ qua bước phát hiện độ lệch và huấn luyện lại |
| `--continue-on-error` | `false` | Tiếp tục chạy ngay cả khi có bước thất bại |
| `--json` | `false` | Xuất kết quả dưới dạng JSON |

---

## 5.15. `mlflow`

Quản lý máy chủ theo dõi MLflow và di chuyển artifact.

### Lệnh con `mlflow ui`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--host` | `127.0.0.1` | Địa chỉ bind cho máy chủ MLflow |
| `--port` | `5000` | Cổng cho MLflow UI |
| `--backend-store-uri` | `sqlite:///mlflow.db` | URI cho backend store (SQLite, PostgreSQL, v.v.) |
| `--default-artifact-root` | `outputs/mlflow_artifacts/` | Vị trí lưu artifact mặc định |

### Lệnh con `mlflow migrate`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | bắt buộc | Ký hiệu cần di chuyển artifact |
| `--tf` | bắt buộc | Khung thời gian cần di chuyển artifact |
| `--backend` | không có | Lọc theo bộ máy huấn luyện |
| `--dry-run` | `false` | Xem trước di chuyển mà không thực hiện |
| `--register-models` | `false` | Đăng ký mô hình đã di chuyển vào MLflow Model Registry |

---

## 6. Quy tắc ưu tiên cấu hình

Thứ tự ưu tiên từ cao xuống thấp:

1. Giá trị truyền trực tiếp trên dòng lệnh
2. Giá trị trong `config.toml`
3. Giá trị mặc định của chương trình

Ví dụ:

- Trong `config.toml`, `tf = "1H"`
- Nhưng bạn chạy:
  - `pixi run mlfx pipeline --symbol XAUUSD --tf 4H`

thì khung thời gian thực tế được dùng sẽ là `4H`.

---

## 7. Những điều nên nhớ khi chỉnh cấu hình

### 7.1. Chỉnh trong file khi nào?

Nên chỉnh `config.toml` khi:

- Bạn thường xuyên lặp lại cùng một quy trình
- Bạn muốn đặt sẵn giá trị mặc định cho bản thân hoặc cho nhóm
- Bạn muốn giảm độ dài câu lệnh phải gõ

### 7.2. Ghi đè trên dòng lệnh khi nào?

Nên ghi đè bằng cờ dòng lệnh khi:

- Bạn chỉ đang thử nhanh một cấu hình
- Bạn muốn so sánh nhiều biến thể khác nhau
- Bạn đang gỡ lỗi và cần kiểm soát chặt giá trị đang dùng

### 7.3. Lỗi thường gặp

- Quên rằng giá trị trên dòng lệnh sẽ ghi đè cấu hình trong file
- Chỉnh `config.toml` nhưng lại không chạy đúng lệnh mong muốn
- Dùng nhầm `label`
- Dùng nhầm `tf`
- Dùng bộ máy không phù hợp với mục tiêu thử nghiệm

---

## 8. Gợi ý cấu hình cho người mới

Nếu bạn mới bắt đầu, đây là bộ giá trị an toàn và dễ chạy:

- `symbol = "XAUUSD"`
- `tf = "1H"`
- `label = "label_10"`
- `backend = "mlf"`
- `pivot_type = "traditional"`
- `pivot_anchor = "daily"`
- `tp_r = 1.5`
- `sl_r = 1.0`

Lý do:

- `XAUUSD` là dữ liệu quen thuộc trong kho mã hiện tại
- `1H` nhẹ hơn các khung thời gian quá nhỏ
- `mlf` là bộ máy thực dụng và dễ bắt đầu
- `label_10` là mốc trung gian hợp lý cho lần chạy đầu

---

## 9. Ví dụ cấu hình theo mục tiêu

### 9.1. Muốn chạy nhanh lần đầu

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

### 9.2. Muốn so sánh nhiều mô hình

```toml
[train]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
backend = "mlf"
n_trials = 15
n_splits = 5
```

### 9.3. Muốn thử khung thời gian lớn hơn

```toml
[pipeline]
symbol = "XAUUSD"
tf = "4H"
```

---

## 10. Danh sách kiểm tra sau khi đổi cấu hình

Sau khi chỉnh `config.toml`, nên kiểm tra:

- Giá trị bạn sửa có nằm đúng phần hay không
- Tên khóa có đúng chính tả hay không
- Kiểu dữ liệu có đúng không
- Nếu cần, hãy chạy:
  - `pixi run mlfx --help`
  - `pixi run mlfx pipeline --help`
- Nếu nghi cấu hình chưa được áp dụng như mong đợi, hãy truyền trực tiếp tham số trên dòng lệnh để đối chiếu

---

## 11. Xem thêm

- [Bắt đầu nhanh](../getting-started/QUICKSTART.md)
- [Hướng dẫn cấu hình và sử dụng](../guides/USAGE_GUIDE.md)
- [Hướng dẫn đánh giá](../guides/EVALUATION_GUIDE.md)
- [Tham chiếu đặc trưng](FEATURE_REFERENCE.md)
- [Kiến trúc hệ thống](../architecture/ARCHITECTURE.md)
