# ML_FX - Hướng dẫn đánh giá

Tài liệu này giải thích cách chạy backtest và đọc các báo cáo được sinh ra bởi [eval/run_eval.py](../eval/run_eval.py) và [viz/charts.py](../viz/charts.py).

## 1. Dữ liệu đầu vào

Luồng đánh giá hiện tại đọc trực tiếp một file parquet đã gắn nhãn, ví dụ:

```text
data/labels/XAUUSD/1H/2024-01.parquet
```

Thông thường bạn sẽ dùng một trong các cột:
- `label_5`
- `label_10`
- `label_20`

Backtest không phụ thuộc vào một file `predictions.parquet` riêng. Nếu dữ liệu đầu vào đã có cột tín hiệu phù hợp, [eval/run_eval.py](../eval/run_eval.py) có thể dùng trực tiếp cột đó.

## 2. Chạy backtest

```bash
pixi run python eval/run_eval.py \
  --data data/labels/XAUUSD/1H/2024-01.parquet \
  --symbol XAUUSD \
  --tf 1H \
  --label label_10 \
  --tp 1.5 \
  --sl 1.0 \
  --slippage 0.0 \
  --outdir outputs/reports
```

Ý nghĩa tham số:
- `--data`: file parquet đầu vào
- `--symbol`: tên symbol để đặt tiêu đề biểu đồ
- `--tf`: timeframe để gắn vào output
- `--label`: cột tín hiệu sẽ dùng khi mô phỏng giao dịch
- `--tp`: take-profit theo đơn vị R
- `--sl`: stop-loss theo đơn vị R
- `--slippage`: độ trượt giá
- `--outdir`: thư mục xuất báo cáo, mặc định là `outputs/reports`

## 3. Các chỉ số chính

Kết quả in ra terminal thường gồm:
- `Total Trades`: tổng số lệnh được mô phỏng
- `Win Rate (%)`: tỷ lệ lệnh chạm TP trước SL
- `Profit Factor`: tổng lãi chia tổng lỗ
- `Net Profit (R)`: tổng lợi nhuận tính theo đơn vị R
- `Net Profit ($)`: lợi nhuận quy đổi theo vốn ban đầu và mức rủi ro
- `Sharpe Ratio`
- `Sortino Ratio`
- `Calmar Ratio`
- `Final Capital ($)`

Diễn giải nhanh:
- `Profit Factor > 1` nghĩa là chiến lược có lãi trên tập dữ liệu đó
- `Max drawdown` và `Final Capital` giúp nhìn rủi ro thực tế, không chỉ nhìn tỷ lệ thắng
- `Net Profit (R)` hữu ích khi so sánh nhiều cấu hình khác nhau trên cùng một chuẩn rủi ro

## 4. Các file được sinh ra

[viz/charts.py](../viz/charts.py) hiện tạo 3 loại báo cáo trong `outputs/reports`:

- `{prefix}_candlestick.html`
- `{prefix}_equity.png`
- `{prefix}_heatmap.png`

Với `prefix = {label}_R{tp*10}`. Ví dụ:

```text
outputs/reports/label_10_R15_candlestick.html
outputs/reports/label_10_R15_equity.png
outputs/reports/label_10_R15_heatmap.png
```

## 5. Cách đọc từng biểu đồ

### 5.1 Candlestick

File HTML candlestick dùng Plotly để hiển thị:
- nến giá
- marker LONG/SHORT/NEUTRAL
- các panel indicator nếu có trong dataset

File này phù hợp khi bạn muốn soi từng tín hiệu tại đúng thời điểm xuất hiện.

### 5.2 Equity curve

File `*_equity.png` hiển thị:
- đường tích lũy lợi nhuận theo R
- phần drawdown phía dưới

Nếu đường equity tăng nhưng drawdown quá sâu, chiến lược có thể khó dùng trong vận hành thực tế.

### 5.3 Heatmap

File `*_heatmap.png` tóm tắt hiệu suất theo giờ UTC và ngày trong tuần.

Heatmap hữu ích khi bạn muốn trả lời các câu hỏi như:
- tín hiệu có mạnh hơn ở London hay New York không
- chiến lược có đang hoạt động kém ở một số khung giờ cụ thể không
- có nên lọc thêm theo phiên giao dịch không

## 6. Một ví dụ tối giản bằng Python

```bash
pixi run python -c "
import polars as pl
from eval.backtest import simulate_trades, compute_metrics
from viz.charts import generate_full_report
from pathlib import Path

df = pl.read_parquet('data/labels/XAUUSD/1H/2024-01.parquet')
trades = simulate_trades(df, signal_col='label_10', tp_r=1.5, sl_r=1.0, slippage=0.0)
metrics = compute_metrics(trades)
print(metrics)
generate_full_report('XAUUSD', '1H', df, trades, 'label_10_R15', Path('outputs/reports'))
"
```

## 7. Gợi ý kiểm tra kết quả

- so sánh nhiều `label_col` khác nhau trên cùng một symbol và timeframe
- không chỉ nhìn `Win Rate`; luôn đối chiếu thêm `Profit Factor`, `Net Profit (R)`, và drawdown
- nếu biểu đồ heatmap cho thấy tín hiệu yếu ngoài giờ thanh khoản cao, thử thêm bộ lọc theo session trong pipeline hoặc logic giao dịch
