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

```/dev/null/config-reference-pipeline.toml#L1-6
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

```/dev/null/config-reference-train.toml#L1-7
[train]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
backend = "mlf"
n_trials = 15
n_splits = 5
```

---

## 2.4. `[features]` — Cấu hình xây dựng đặc trưng

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

## 2.5. `[backtest]` — Cấu hình đánh giá và mô phỏng giao dịch

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

### Ví dụ

```/dev/null/config-reference-backtest.toml#L1-9
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
```

---

## 3. Ví dụ `config.toml` hoàn chỉnh

```/dev/null/config-reference-full.toml#L1-38
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
tf    = "1H"
pivot_type   = "traditional"
pivot_anchor = "daily"
atr_period   = 14
atr_mult     = 0.5

[train]
symbol     = "XAUUSD"
tf  = "1H"
label  = "label_10"
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
tf       = "1H"
label       = "label_10"
tp_r            = 1.5
sl_r            = 1.0
initial_capital = 10000.0
risk_pct        = 1.0
commission      = 0.1
slippage        = 0.0
```

---

## 4. Tham chiếu các cờ dòng lệnh

## 4.1. Cờ dùng chung

Các lệnh chính đều hỗ trợ:

| Cờ | Mô tả |
|---|---|
| `--help` | Hiển thị trợ giúp của lệnh |
| `--version` | Hiển thị phiên bản hiện tại |

---

## 4.2. `download`

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

## 4.3. `pipeline`

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

## 4.4. `train`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ cấu hình | Mã dùng để huấn luyện |
| `--tf` | từ cấu hình | Khung thời gian |
| `--label` | từ cấu hình | Cột nhãn |
| `--backend` | từ cấu hình | Bộ máy huấn luyện |
| `--n-trials` | từ cấu hình | Số lần thử siêu tham số |
| `--n-splits` | từ cấu hình | Số phần chia trong kiểm định chéo |
| `--force` | `false` | Huấn luyện lại dù tệp đầu ra đã tồn tại |

---

## 4.5. `evaluate`

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
| `--use-labels` | `false` | Chỉ kiểm định trực tiếp trên nhãn, bỏ qua mô hình |

---

## 4.6. `serve`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--port` | `8000` | Cổng chạy API suy luận |

---

## 4.7. `batch-predict`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ cấu hình | Mã cần dự đoán |
| `--tf` | từ cấu hình | Khung thời gian |
| `--label` | từ cấu hình | Cột nhãn tương ứng với mô hình |

---

## 4.8. `drift`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ cấu hình | Mã cần kiểm tra độ lệch |
| `--tf` | từ cấu hình | Khung thời gian |
| `--threshold-ks` | `0.1` | Ngưỡng kiểm định KS |
| `--threshold-psi` | `0.2` | Ngưỡng PSI |

---

## 4.9. `models`

| Cờ | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | không có | Lọc theo mã |
| `--tf` | không có | Lọc theo khung thời gian |

---

## 5. Quy tắc ưu tiên cấu hình

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

## 6. Những điều nên nhớ khi chỉnh cấu hình

### 6.1. Chỉnh trong file khi nào?

Nên chỉnh `config.toml` khi:

- Bạn thường xuyên lặp lại cùng một quy trình
- Bạn muốn đặt sẵn giá trị mặc định cho bản thân hoặc cho nhóm
- Bạn muốn giảm độ dài câu lệnh phải gõ

### 6.2. Ghi đè trên dòng lệnh khi nào?

Nên ghi đè bằng cờ dòng lệnh khi:

- Bạn chỉ đang thử nhanh một cấu hình
- Bạn muốn so sánh nhiều biến thể khác nhau
- Bạn đang gỡ lỗi và cần kiểm soát chặt giá trị đang dùng

### 6.3. Lỗi thường gặp

- Quên rằng giá trị trên dòng lệnh sẽ ghi đè cấu hình trong file
- Chỉnh `config.toml` nhưng lại không chạy đúng lệnh mong muốn
- Dùng nhầm `label`
- Dùng nhầm `tf`
- Dùng bộ máy không phù hợp với mục tiêu thử nghiệm

---

## 7. Gợi ý cấu hình cho người mới

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

## 8. Ví dụ cấu hình theo mục tiêu

### 8.1. Muốn chạy nhanh lần đầu

```/dev/null/config-reference-starter.toml#L1-9
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

### 8.2. Muốn so sánh nhiều mô hình

```/dev/null/config-reference-benchmark.toml#L1-8
[train]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
backend = "mlf"
n_trials = 15
n_splits = 5
```

### 8.3. Muốn thử khung thời gian lớn hơn

```/dev/null/config-reference-higher-tf.toml#L1-4
[pipeline]
symbol = "XAUUSD"
tf = "4H"
```

---

## 9. Danh sách kiểm tra sau khi đổi cấu hình

Sau khi chỉnh `config.toml`, nên kiểm tra:

- Giá trị bạn sửa có nằm đúng phần hay không
- Tên khóa có đúng chính tả hay không
- Kiểu dữ liệu có đúng không
- Nếu cần, hãy chạy:
  - `pixi run mlfx --help`
  - `pixi run mlfx pipeline --help`
- Nếu nghi cấu hình chưa được áp dụng như mong đợi, hãy truyền trực tiếp tham số trên dòng lệnh để đối chiếu

---

## 10. Xem thêm

- [Bắt đầu nhanh](../getting-started/QUICKSTART.md)
- [Hướng dẫn cấu hình và sử dụng](../guides/USAGE_GUIDE.md)
- [Hướng dẫn đánh giá](../guides/EVALUATION_GUIDE.md)
- [Tham chiếu đặc trưng](FEATURE_REFERENCE.md)
- [Kiến trúc hệ thống](../architecture/ARCHITECTURE.md)
