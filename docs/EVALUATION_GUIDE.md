# MLFX - Hướng dẫn đánh giá

Tài liệu này mô tả cách chạy `mlfx evaluate`, cách đọc metrics, và cách hiểu các artifact được sinh ra.

## 1. Backtest Model vs Labels

**Mặc định**: `evaluate` backtest **model** đã train. Nếu chưa train model, backtest **labels** (baseline).

- **Backtest Model**: Dùng predictions của model để mô phỏng giao dịch. Đây là kết quả thực tế của chiến lược ML.
- **Backtest Labels**: Dùng nhãn gốc (ground truth) làm tín hiệu. Dùng để so sánh baseline hoặc khi chưa có model.

**So sánh baseline**: Khi backtest model, CLI tự động in dòng so sánh với labels, ví dụ:
`So với labels: model +12.5R vs labels +8.2R → model tốt hơn +4.3R`

**Chỉ backtest labels**: Thêm `--use-labels` để bỏ qua model và chỉ backtest labels.

## 2. Dữ liệu đầu vào

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

## 3. Lệnh chạy backtest

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
- `--use-labels`: chỉ backtest labels (bỏ qua model)

## 4. Naming convention của report

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

thì prefix labels là `XAUUSD_1H_label_10_R15`, prefix model là `model_label_10_R15`.

## 5. Các file được sinh ra

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

## 7. Cách đọc từng loại report

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

## 8. Failure modes thường gặp

Evaluation thường fail hoặc cho kết quả rỗng khi:
- không có parquet trong `data/labels/{symbol}/{tf}/`
- cột `--label` không tồn tại
- cột `atr_14` không tồn tại
- dữ liệu quá ít khiến gần như không có trade
- signal không có giá trị `1` hoặc `-1`

## 9. Checklist xác minh sau khi evaluate

Sau khi chạy, nên kiểm tra:
- CLI có in ra summary metrics hay không
- `outputs/reports/{symbol}/{tf}/` có 3 artifact mới hay không
- tên file có đúng prefix kỳ vọng hay không
- số trade có đủ lớn để kết luận hay chỉ là một mẫu quá nhỏ

## 10. Ví dụ Python tối thiểu

```python
from mlfx.evaluation.runner import run_full_eval, run_model_backtest

# Backtest model (nếu đã train) hoặc labels
results = run_model_backtest(
    symbol="XAUUSD", tf="1H", label_col="label_10",
    tp_r=1.5, sl_r=1.0, commission=0.1, slippage=0.0,
)
if results is None:
    results = run_full_eval(
        symbol="XAUUSD", tf="1H", label_col="label_10",
        tp_r=1.5, sl_r=1.0, commission=0.1, slippage=0.0,
    )
print(results)
```
