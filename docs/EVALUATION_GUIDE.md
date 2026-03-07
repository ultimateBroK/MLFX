# ML_FX - Hướng dẫn đánh giá

Tài liệu này mô tả cách chạy `mlfx evaluate`, cách đọc metrics, và cách hiểu các artifact được sinh ra.

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

## 2. Lệnh chạy backtest

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

Ý nghĩa tham số:
- `--symbol`: mã instrument
- `--tf`: timeframe đang evaluate
- `--label`: cột tín hiệu dùng để vào lệnh
- `--capital`: vốn ban đầu để quy đổi từ `R` sang dollar
- `--risk`: % vốn rủi ro trên mỗi lệnh
- `--commission`: chi phí commission trên mỗi lệnh
- `--tp`: take-profit theo đơn vị `R`
- `--sl`: stop-loss theo đơn vị `R`
- `--slippage`: trượt giá giả lập

## 3. Naming convention của report

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

thì prefix là:

```text
XAUUSD_1H_label_10_R15
```

## 4. Các file được sinh ra

Mỗi lần chạy thường sinh 3 artifact trong `outputs/reports/`:
- `{prefix}_candlestick.html`
- `{prefix}_equity.png`
- `{prefix}_heatmap.png`

Ví dụ:

```text
outputs/reports/XAUUSD_1H_label_10_R15_candlestick.html
outputs/reports/XAUUSD_1H_label_10_R15_equity.png
outputs/reports/XAUUSD_1H_label_10_R15_heatmap.png
```

## 5. Các metric chính

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

Diễn giải nhanh:
- `Total Trades`: số lệnh được mô phỏng
- `Win Rate (%)`: tỷ lệ lệnh lãi; không nên dùng độc lập
- `Profit Factor`: tổng lãi chia tổng lỗ; `> 1` mới là mức tối thiểu
- `Net Profit (R)`: lợi nhuận chuẩn hóa, rất hữu ích để so sánh nhiều cấu hình
- `Net Profit ($)`: quy đổi theo `capital` và `risk`
- `Sharpe Ratio`: lợi nhuận trung bình so với độ biến động tổng thể
- `Sortino Ratio`: tương tự Sharpe nhưng chỉ phạt downside volatility
- `Calmar Ratio`: tổng lợi nhuận so với drawdown tối đa
- `Final Capital ($)`: vốn cuối cùng sau khi áp chi phí và kết quả giao dịch

## 6. Cách đọc từng loại report

### 6.1 Candlestick HTML

Hiển thị:
- nến giá
- marker vào lệnh LONG/SHORT
- panel RSI nếu dataset có `rsi_14`

Phù hợp để:
- kiểm tra điểm vào lệnh có hợp lý không
- xem signal có bị dồn vào một đoạn ngắn bất thường không

### 6.2 Equity curve PNG

Hiển thị:
- cumulative PnL theo đơn vị `R`
- drawdown ở panel dưới

Phù hợp để:
- nhìn nhịp tăng trưởng vốn
- so sánh độ “mượt” giữa nhiều cấu hình

### 6.3 Heatmap PNG

Hiển thị hiệu suất trung bình theo:
- giờ UTC
- ngày trong tuần

Phù hợp để:
- xác định xem nên thêm time filter hay session filter hay không

## 7. Failure modes thường gặp

Evaluation thường fail hoặc cho kết quả rỗng khi:
- không có parquet trong `data/labels/{symbol}/{tf}/`
- cột `--label` không tồn tại
- cột `atr_14` không tồn tại
- dữ liệu quá ít khiến gần như không có trade
- signal không có giá trị `1` hoặc `-1`

## 8. Checklist xác minh sau khi evaluate

Sau khi chạy, nên kiểm tra:
- CLI có in ra summary metrics hay không
- `outputs/reports/` có 3 artifact mới hay không
- tên file có đúng prefix kỳ vọng hay không
- số trade có đủ lớn để kết luận hay chỉ là một mẫu quá nhỏ

## 9. Ví dụ Python tối thiểu

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
metrics = compute_metrics(trades, initial_capital=10000.0, risk_pct=1.0)
print(metrics)
generate_full_report("XAUUSD", "1H", df, trades, "label_10_R15", Path("outputs/reports"))
```
