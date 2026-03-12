# MLFX - Tham chiếu cấu hình

Tài liệu này là bản tham chiếu đầy đủ cho `config.toml` và các CLI flags tương ứng trong MLFX.

---

## Tài liệu liên quan

- [Docs Hub tiếng Việt](../README.md)
- [Quickstart](../getting-started/QUICKSTART.md)
- [Hướng dẫn cấu hình và sử dụng](../guides/USAGE_GUIDE.md)
- [Hướng dẫn đánh giá](../guides/EVALUATION_GUIDE.md)
- [Kiến trúc hệ thống](../architecture/ARCHITECTURE.md)
- [Tham chiếu Feature](FEATURE_REFERENCE.md)

---

## 1. Tổng quan

MLFX sử dụng mô hình cấu hình hai lớp:

1. **`config.toml`** — nơi khai báo giá trị mặc định cho toàn dự án
2. **CLI flags** — dùng để ghi đè các giá trị mặc định cho từng lần chạy

CLI tự động đọc `config.toml` ở thư mục gốc của project. Nếu bạn truyền tham số trực tiếp trên CLI, giá trị đó sẽ **ưu tiên cao hơn** cấu hình trong file.

---

## 2. Các section trong `config.toml`

## 2.1. `[download]` — Tải dữ liệu đầu vào

| Khóa | Kiểu | Mặc định | CLI Override | Mô tả |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Mã instrument cần tải |
| `asset_class` | string | `"fx"` | `--asset-class` | Nhóm tài sản: `"fx"`, `"crypto"` |
| `start_year` | integer | `2015` | `--start-year` | Năm bắt đầu tải |
| `start_month` | integer | `1` | `--start-month` | Tháng bắt đầu tải (`1-12`) |
| `end_year` | integer | năm hiện tại | `--end-year` | Năm kết thúc tải |
| `end_month` | integer | tháng hiện tại | `--end-month` | Tháng kết thúc tải |
| `concurrency` | integer | `20` | `--concurrency` | Số worker tải song song |

### Ví dụ

```/dev/null/config.toml#L1-7
[download]
symbol = "XAUUSD"
asset_class = "fx"
start_year = 2015
start_month = 1
end_year = 2025
concurrency = 20
```

---

## 2.2. `[pipeline]` — Cấu hình pipeline feature và label

| Khóa | Kiểu | Mặc định | CLI Override | Mô tả |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Mã instrument cần xử lý |
| `timeframe` | string | `"1H"` | `--tf` | Timeframe mục tiêu |
| `pivot_type` | string | `"traditional"` | `--pivot` | Phương pháp tính pivot |
| `pivot_anchor` | string | `"daily"` | `--anchor` | Chu kỳ neo pivot |
| `atr_period` | integer | `14` | `--atr-period` | Chu kỳ tính ATR |
| `atr_mult` | float | `0.5` | `--atr-mult` | Hệ số ATR dùng khi tạo label |

### Pivot types hỗ trợ

- `traditional`
- `fibonacci`
- `woodie`
- `classic`
- `demark`
- `camarilla`

### Pivot anchors hỗ trợ

- `daily`
- `weekly`
- `monthly`

### Timeframes thường dùng

- `1m`
- `5m`
- `15m`
- `30m`
- `1H`
- `2H`
- `4H`
- `1D`

### Ví dụ

```/dev/null/config.toml#L1-5
[pipeline]
symbol = "XAUUSD"
timeframe = "1H"
pivot_type = "traditional"
pivot_anchor = "daily"
atr_mult = 0.5
```

---

## 2.3. `[train]` — Cấu hình huấn luyện

| Khóa | Kiểu | Mặc định | CLI Override | Mô tả |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Mã instrument để train |
| `timeframe` | string | `"1H"` | `--tf` | Timeframe dùng để train |
| `label_col` | string | `"label_10"` | `--label` | Cột label mục tiêu |
| `backend` | string | `"mlf"` | `--backend` | Backend huấn luyện |
| `n_trials` | integer | `30` | `--n-trials` | Số lần Optuna trial, chủ yếu áp dụng cho `mlf` |
| `n_splits` | integer | `5` | `--n-splits` | Số fold cross-validation |

### Backends hỗ trợ

- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

### Labels hỗ trợ

- `label_5`
- `label_10`
- `label_20`

### Ví dụ

```/dev/null/config.toml#L1-7
[train]
symbol = "XAUUSD"
timeframe = "1H"
label_col = "label_10"
backend = "mlf"
n_trials = 15
n_splits = 5
```

---

## 2.4. `[features]` — Cấu hình feature engineering

| Khóa | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| `rsi_period` | integer | `14` | Chu kỳ tính RSI |
| `atr_period` | integer | `14` | Chu kỳ tính ATR |
| `ema_periods` | list | `[20, 50, 200]` | Danh sách EMA cần tạo |
| `macd_fast` | integer | `12` | Chu kỳ EMA nhanh của MACD |
| `macd_slow` | integer | `26` | Chu kỳ EMA chậm của MACD |
| `macd_signal` | integer | `9` | Chu kỳ signal của MACD |
| `avg_range_n` | integer | `5` | Số phiên dùng để tính trung bình biên độ killzone |

### Ví dụ

```/dev/null/config.toml#L1-8
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

## 2.5. `[backtest]` — Cấu hình evaluate và mô phỏng giao dịch

| Khóa | Kiểu | Mặc định | CLI Override | Mô tả |
|---|---|---|---|---|
| `symbol` | string | `"XAUUSD"` | `--symbol` | Mã instrument cần evaluate |
| `timeframe` | string | `"1H"` | `--tf` | Timeframe backtest |
| `label_col` | string | `"label_10"` | `--label` | Cột tín hiệu dùng để backtest |
| `tp_r` | float | `1.5` | `--tp` | Take-profit theo đơn vị `R` |
| `sl_r` | float | `1.0` | `--sl` | Stop-loss theo đơn vị `R` |
| `initial_capital` | float | `10000.0` | `--capital` | Vốn ban đầu |
| `risk_pct` | float | `1.0` | `--risk` | % vốn rủi ro mỗi lệnh |
| `commission` | float | `0.1` | `--commission` | Chi phí commission mỗi lệnh |
| `slippage` | float | `0.0` | `--slippage` | Trượt giá giả lập |

### Ví dụ

```/dev/null/config.toml#L1-9
[backtest]
symbol = "XAUUSD"
timeframe = "1H"
label_col = "label_10"
tp_r = 1.5
sl_r = 1.0
initial_capital = 10000.0
risk_pct = 1.0
commission = 0.1
slippage = 0.0
```

---

## 3. Ví dụ `config.toml` hoàn chỉnh

```/dev/null/config.toml#L1-38
# MLFX Configuration
# File này được CLI `mlfx` tự động đọc.
# Hãy chỉnh các giá trị mặc định để phù hợp workflow của bạn.

[download]
symbol      = "XAUUSD"
asset_class = "fx"
start_year  = 2015
start_month = 1
concurrency = 20

[pipeline]
symbol       = "XAUUSD"
timeframe    = "1H"
pivot_type   = "traditional"
pivot_anchor = "daily"
atr_period   = 14
atr_mult     = 0.5

[train]
symbol     = "XAUUSD"
timeframe  = "1H"
label_col  = "label_10"
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
timeframe       = "1H"
label_col       = "label_10"
tp_r            = 1.5
sl_r            = 1.0
initial_capital = 10000.0
risk_pct        = 1.0
commission      = 0.1
slippage        = 0.0
```

---

## 4. Tham chiếu CLI flags

## 4.1. Global flags

Các lệnh chính đều hỗ trợ:

| Flag | Mô tả |
|---|---|
| `--help` | Hiển thị trợ giúp của lệnh |
| `--version` | Hiển thị version hiện tại |

---

## 4.2. `download`

| Flag | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ config | Mã instrument |
| `--asset-class` | từ config | Nhóm tài sản |
| `--start-year` | từ config | Năm bắt đầu |
| `--start-month` | từ config | Tháng bắt đầu |
| `--end-year` | năm hiện tại | Năm kết thúc |
| `--end-month` | tháng hiện tại | Tháng kết thúc |
| `--concurrency` | từ config | Số worker song song |
| `--force` | `false` | Tải lại tháng đã tồn tại |
| `--skip-current-month` | `false` | Bỏ qua kiểm tra tháng hiện tại |

---

## 4.3. `pipeline`

| Flag | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ config | Symbol cần xử lý |
| `--tf` | từ config | Timeframe, có thể truyền nhiều giá trị |
| `--pivot` | từ config | Phương pháp pivot |
| `--anchor` | từ config | Chu kỳ neo pivot |
| `--atr-period` | từ config | Chu kỳ ATR |
| `--atr-mult` | từ config | Hệ số ATR dùng để tạo label |
| `--force` | `false` | Ghi đè file đã tồn tại |
| `--skip-resample` | `false` | Bỏ qua bước tạo OHLCV |
| `--skip-features` | `false` | Bỏ qua bước feature engineering |
| `--skip-labels` | `false` | Bỏ qua bước tạo label |

---

## 4.4. `train`

| Flag | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ config | Symbol để train |
| `--tf` | từ config | Timeframe |
| `--label` | từ config | Cột label |
| `--backend` | từ config | Backend huấn luyện |
| `--n-trials` | từ config | Số Optuna trials |
| `--n-splits` | từ config | Số fold CV |
| `--force` | `false` | Train lại dù artifact đã tồn tại |

---

## 4.5. `evaluate`

| Flag | Mặc định | Mô tả |
|---|---|---|
| `--symbol` | từ config | Symbol cần evaluate |
| `--tf` | từ config | Timeframe |
| `--label` | từ config | Cột tín hiệu |
| `--capital` | từ config | Vốn ban đầu |
| `--risk` | từ config | % rủi ro mỗi lệnh |
| `--commission` | từ config | Commission mỗi lệnh |
| `--tp` | từ config | Take-profit theo `R` |
| `--sl` | từ config | Stop-loss theo `R` |
| `--slippage` | từ config | Trượt giá giả lập |
| `--use-labels` | `false` | Chỉ backtest labels, bỏ qua model |

---

## 5. Quy tắc ưu tiên cấu hình

Thứ tự ưu tiên từ cao xuống thấp:

1. Giá trị truyền trực tiếp trên CLI
2. Giá trị trong `config.toml`
3. Giá trị mặc định trong code

### Ví dụ

```/dev/null/example.sh#L1-2
# config.toml đặt timeframe = "1H"
pixi run mlfx pipeline --symbol XAUUSD --tf 4H
```

Trong ví dụ trên, timeframe thực tế dùng sẽ là `4H`, không phải `1H`.

---

## 6. Khi nào nên chỉnh `config.toml`

### Nên chỉnh `config.toml` khi

- Bạn chạy đi chạy lại cùng một symbol hoặc timeframe
- Bạn muốn chuẩn hóa workflow cho cả team
- Bạn muốn giảm số lượng cờ CLI phải nhập mỗi lần

### Không nhất thiết phải chỉnh `config.toml` khi

- Bạn chỉ test nhanh một cấu hình tạm
- Bạn đang benchmark nhiều cấu hình khác nhau bằng CLI

---

## 7. Các lỗi cấu hình thường gặp

### 7.1. `label_col` không khớp dữ liệu đã sinh

Ví dụ bạn train với `label_20` nhưng pipeline trước đó không tạo hoặc bạn đang đọc nhầm dataset.

### Cách xử lý

- Kiểm tra file trong `data/labels/{symbol}/{tf}/`
- Xác nhận cột label tồn tại thật sự

### 7.2. `backend` không hợp lệ

Nếu backend không nằm trong danh sách hỗ trợ, lệnh train sẽ fail.

### Cách xử lý

Dùng một trong các giá trị hợp lệ:

- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

### 7.3. `timeframe` không phù hợp

Một số workflow có thể nặng hoặc ít ý nghĩa nếu chọn timeframe quá nhỏ với dữ liệu lớn.

### Gợi ý

- Bắt đầu với `1H`
- Chỉ giảm xuống `15m` hoặc `5m` khi bạn đã kiểm soát tốt tài nguyên và dữ liệu

### 7.4. `atr_mult` hoặc `tp/sl` không hợp lý

Ngưỡng quá nhỏ có thể làm label nhiễu hoặc backtest quá nhạy; ngưỡng quá lớn có thể làm ít tín hiệu.

### Gợi ý

- Giữ mặc định trước
- Chỉ tinh chỉnh khi bạn đã có baseline rõ ràng

---

## 8. Gợi ý sử dụng thực tế

- Giữ `config.toml` trong version control với các mặc định hợp lý
- Dùng CLI flags cho các thử nghiệm một lần
- Nếu team cùng làm việc trên một workflow chung, hãy thống nhất các giá trị mặc định trong `config.toml`
- Khi benchmark nhiều cấu hình, nên ghi đè bằng CLI thay vì sửa file liên tục

---

## 9. Xem thêm

- [Hướng dẫn cấu hình và sử dụng](../guides/USAGE_GUIDE.md)
- [Hướng dẫn đánh giá](../guides/EVALUATION_GUIDE.md)
- [Tham chiếu Feature](FEATURE_REFERENCE.md)
- [Kiến trúc hệ thống](../architecture/ARCHITECTURE.md)
- [Quickstart](../getting-started/QUICKSTART.md)
