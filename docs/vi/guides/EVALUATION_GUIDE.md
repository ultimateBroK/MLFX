# MLFX - Hướng dẫn đánh giá

Tài liệu này mô tả cách chạy `mlfx evaluate`, cách đọc metrics, và cách hiểu các artifact được sinh ra.

## Tài liệu liên quan

- [Docs Hub tiếng Việt](../README.md)
- [Quickstart](../getting-started/QUICKSTART.md)
- [Hướng dẫn cấu hình và sử dụng](USAGE_GUIDE.md)
- [Tham chiếu Feature](../reference/FEATURE_REFERENCE.md)
- [Tham chiếu cấu hình](../reference/CONFIG_REFERENCE.md)
- [Khắc phục sự cố](TROUBLESHOOTING.md)

---

## 1. Dữ liệu đầu vào

Evaluation đọc toàn bộ dữ liệu đã gắn nhãn trong:

```text
data/labels/{symbol}/{tf}/*.parquet
```

Dataset đầu vào cần có tối thiểu:

- cột `timestamp`
- cột OHLC như `open`, `high`, `low`, `close`
- cột ATR mặc định là `atr_14`
- cột tín hiệu bạn truyền qua `--label`

Các cột tín hiệu thường dùng:

- `label_5`
- `label_10`
- `label_20`

---

## 2. Chạy backtest

```bash
pixi run mlfx evaluate \
  --symbol XAUUSD \
  --tf 1H \
  --label label_10 \
  --capital 10000 \
  --risk 1.0 \
  --commission 0.1 \
  --tp 1.5 \
  --sl 1.0 \
  --slippage 0.0
```

### 2.1. Quy tắc khớp lệnh

Với mỗi cây nến có tín hiệu, simulator sẽ:

1. Mở vị thế tại **giá open của cây nến kế tiếp**
2. Kiểm tra các cây nến tiếp theo xem có chạm TP hoặc SL không
3. Nếu không chạm TP hoặc SL trong vòng **10 cây nến** (`horizon_limit`), lệnh sẽ bị force-exit ở cây nến thứ 10

TP và SL được biểu diễn theo đơn vị **R** — tức bội số của khoảng rủi ro ban đầu, được suy ra từ `atr_14`.

### 2.2. Mapping từ label sang tín hiệu giao dịch

Các giá trị label ordinal được ánh xạ sang tín hiệu như sau:

| Label | Signal | Ý nghĩa |
|---|---|---|
| `2` | LONG | Tăng mạnh |
| `1` | LONG | Tăng |
| `0` | Skip | Không vào lệnh |
| `-1` | SHORT | Giảm |
| `-2` | SHORT | Giảm mạnh |

> **Lưu ý**: Label `1` và `2` hiện đều tạo cùng một loại lệnh LONG; mức độ mạnh/yếu (`±2` so với `±1`) chưa làm thay đổi position sizing trong implementation hiện tại.

### 2.3. Ý nghĩa tham số

- `--symbol`: mã instrument
- `--tf`: timeframe đang evaluate
- `--label`: cột tín hiệu dùng để vào lệnh
- `--capital`: vốn ban đầu để quy đổi từ `R` sang dollar
- `--risk`: % vốn rủi ro trên mỗi lệnh
- `--commission`: chi phí commission trên mỗi lệnh
- `--tp`: take-profit theo đơn vị `R`
- `--sl`: stop-loss theo đơn vị `R`
- `--slippage`: trượt giá giả lập
- `--use-labels`: chỉ backtest labels, bỏ qua model predictions

---

## 3. Chế độ backtest: Model và Labels

### 3.1. Mặc định

Theo mặc định, `mlfx evaluate` sẽ dùng **model tốt nhất đã đăng ký** để sinh prediction, sau đó backtest prediction đó.

Nếu chưa có model phù hợp, workflow sẽ fallback sang **labels**.

### 3.2. Backtest labels

Nếu bạn muốn backtest trực tiếp nhãn gốc, hãy thêm `--use-labels`:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --use-labels --tp 1.5 --sl 1.0
```

### 3.3. Backtest model

Nếu không truyền `--use-labels`, hệ thống sẽ cố gắng:

1. Đọc `outputs/models/registry.json`
2. Chọn model tốt nhất dựa trên metric đã đăng ký
3. Chạy inference trên dataset đầy đủ
4. Backtest prediction của model đó

Ví dụ:

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

### 3.4. Workflow so sánh baseline

Một workflow hợp lý để so sánh giá trị model:

```bash
# Bước 1: Baseline — backtest labels
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --use-labels --tp 1.5 --sl 1.0

# Bước 2: Train model
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf

# Bước 3: Backtest model
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

Khi đó bạn có thể so sánh:

- Equity curve
- Profit Factor
- Sharpe Ratio
- Net Profit (R)
- Độ ổn định của kết quả

---

## 4. Quy ước đặt tên report

Runner tạo `out_name` theo công thức:

```text
{label_col}_R{int(tp_r * 10)}
```

Sau đó reporting tạo prefix đầy đủ:

```text
{symbol}_{tf}_{out_name}
```

Ví dụ với:

- `symbol = XAUUSD`
- `tf = 1H`
- `label = label_10`
- `tp = 1.5`

thì prefix sẽ là:

```text
XAUUSD_1H_label_10_R15
```

---

## 5. Các artifact được sinh ra

Mỗi lần chạy thường sinh 3 artifact trong `outputs/reports/{symbol}/{tf}/`:

- `{prefix}_candlestick.html`
- `{prefix}_equity.png`
- `{prefix}_heatmap.png`

Ví dụ:

```text
outputs/reports/XAUUSD/1H/XAUUSD_1H_label_10_R15_candlestick.html
outputs/reports/XAUUSD/1H/XAUUSD_1H_label_10_R15_equity.png
outputs/reports/XAUUSD/1H/XAUUSD_1H_label_10_R15_heatmap.png
```

---

## 6. Các metric chính

Output tóm tắt thường gồm:

- `Total Trades`
- `Win Rate (%)`
- `Profit Factor`
- `Net Profit (R)`
- `Net Profit ($)`
- `Sharpe Ratio`
- `Sortino Ratio`
- `Calmar Ratio`
- `Final Capital ($)`

### 6.1. Diễn giải nhanh

- `Total Trades`: số lệnh được mô phỏng
- `Win Rate (%)`: tỷ lệ lệnh lãi; không nên dùng độc lập
- `Profit Factor`: tổng lãi chia tổng lỗ; giá trị `> 1` mới là mức tối thiểu có ý nghĩa
- `Net Profit (R)`: lợi nhuận chuẩn hóa, rất hữu ích để so sánh nhiều cấu hình công bằng
- `Net Profit ($)`: lợi nhuận quy đổi theo `capital` và `risk`
- `Sharpe Ratio`: lợi nhuận trung bình so với độ biến động tổng thể
- `Sortino Ratio`: tương tự Sharpe nhưng chỉ phạt downside volatility
- `Calmar Ratio`: tổng lợi nhuận ròng chia cho drawdown tối đa
- `Final Capital ($)`: vốn cuối cùng sau khi áp chi phí và kết quả giao dịch

### 6.2. Lưu ý khi đọc metrics

- Đừng dùng `Win Rate` một mình để kết luận chiến lược tốt hay xấu
- `Profit Factor`, `Net Profit (R)` và `Sharpe/Sortino` thường hữu ích hơn khi so sánh cấu hình
- Số lượng trade quá ít có thể làm metric đẹp nhưng thiếu ý nghĩa thống kê
- Luôn so sánh model với baseline labels nếu có thể

---

## 7. Cách đọc từng loại report

### 7.1. Candlestick HTML

Hiển thị:

- Bến giá
- Marker vào lệnh LONG/SHORT
- Panel RSI nếu dataset có `rsi_14`

Phù hợp để:

- Kiểm tra điểm vào lệnh có hợp lý không
- Xem signal có bị dồn vào một đoạn ngắn bất thường không
- Xác nhận xem chiến lược có “đánh đúng lúc” hay không

### 7.2. Equity Curve PNG

Hiển thị:

- Cumulative PnL theo đơn vị `R`
- Drawdown ở panel dưới

Phù hợp để:

- Nhìn nhịp tăng trưởng vốn
- So sánh độ “mượt” giữa nhiều cấu hình
- Đánh giá xem lợi nhuận có đến từ một vài trade may mắn hay từ cả chuỗi ổn định

### 7.3. Heatmap PNG

Hiển thị hiệu suất trung bình theo:

- Giờ UTC
- Ngày trong tuần

Phù hợp để:

- Xác định xem nên thêm time filter hay session filter hay không
- Nhận diện khung giờ có hiệu suất tốt hoặc kém bất thường

---

## 8. Failure Modes thường gặp

Evaluation thường fail hoặc cho kết quả rỗng khi:

- Không có parquet trong `data/labels/{symbol}/{tf}/`
- Cột `--label` không tồn tại
- Cột `atr_14` không tồn tại
- Dữ liệu quá ít khiến gần như không có trade
- Signal column không bao giờ phát ra tín hiệu LONG/SHORT hữu ích

### 8.1. Dấu hiệu lỗi phổ biến

- CLI không in ra summary metrics
- Không có file mới trong `outputs/reports/{symbol}/{tf}/`
- Trade count quá thấp hoặc bằng `0`
- Filename sinh ra không đúng prefix mong đợi

---

## 9. Checklist xác minh sau khi evaluate

Sau khi chạy, nên kiểm tra:

- CLI có in ra summary metrics hay không
- `outputs/reports/{symbol}/{tf}/` có 3 artifact mới hay không
- Tên file có đúng prefix kỳ vọng hay không
- Số trade có đủ lớn để kết luận hay chỉ là một mẫu quá nhỏ
- Nếu đang backtest model, model đó có thật sự tồn tại trong registry không

---

## 10. Ví dụ Python tối thiểu

```python
from pathlib import Path

import polars as pl

from mlfx.evaluation.backtest import compute_metrics, simulate_trades
from mlfx.evaluation.reporting import generate_full_report

df = pl.read_parquet("data/labels/XAUUSD/1H/2024-01.parquet")

trades = simulate_trades(
    df,
    signal_col="label_10",
    tp_r=1.5,
    sl_r=1.0,
    commission=0.1,
    slippage=0.0,
)

metrics = compute_metrics(
    trades,
    initial_capital=10000.0,
    risk_pct=1.0,
)

print(metrics)

generate_full_report(
    "XAUUSD",
    "1H",
    df,
    trades,
    "label_10_R15",
    Path("outputs/reports/XAUUSD/1H"),
)
```

---

## 11. Gợi ý quy trình đọc kết quả

Nếu bạn mới bắt đầu, hãy đọc kết quả theo thứ tự:

1. `Total Trades`
2. `Profit Factor`
3. `Net Profit (R)`
4. `Sharpe Ratio`
5. Equity curve
6. Heatmap
7. Candlestick HTML

Lý do:

- Metric tổng quan cho biết cấu hình có đáng xem tiếp hay không
- Equity curve cho biết chất lượng đường vốn
- Heatmap giúp gợi ý cải tiến chiến lược theo thời gian
- Candlestick giúp kiểm tra trực quan điểm vào lệnh

---

## 12. Xem thêm

- [Quickstart](../getting-started/QUICKSTART.md)
- [Hướng dẫn cấu hình và sử dụng](USAGE_GUIDE.md)
- [Tham chiếu Feature](../reference/FEATURE_REFERENCE.md)
- [Tham chiếu cấu hình](../reference/CONFIG_REFERENCE.md)
- [Khắc phục sự cố](TROUBLESHOOTING.md)
