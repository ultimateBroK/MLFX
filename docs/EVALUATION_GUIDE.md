# ML_FX Evaluation Guide

Tài liệu này hướng dẫn cách đọc các kết quả Backtest và các biểu đồ phân tích hiệu suất (Visualization) của dự án ML_FX.

Hệ thống Evaluation (đặt trong folder `eval/` và `viz/`) cung cấp cái nhìn chi tiết về cách mô hình Machine Learning sẽ hoạt động nếu giao dịch thực tế trên thị trường. Chúng tôi không sử dụng "tỉ lệ phần trăm chiến thắng" (accuracy) thuần túy của Machine Learning mà chuyển hóa chúng thành **Mô phỏng Giao dịch theo R-multiple** (walk-forward simulation).

---

## 1. Hiểu Về Metrics Giao Dịch

Báo cáo sẽ in ra một từ điển Metrics như sau:
`Metrics: {'total_trades': 139, 'win_rate': 73.38, 'total_r': 118.0, 'max_drawdown_r': 3.0, 'profit_factor': 4.37}`

Ý nghĩa của các con số:
*   **total_trades**: Tổng số lệnh giao dịch được mô phỏng.
*   **win_rate (%)**: Tỉ lệ lệnh chạm Take Profit (TP) trước khi chạm Stop Loss (SL). Tuy nhiên, win_rate không phải là tất cả nếu R:R không tốt.
*   **total_r (Cumulative R-multiple)**: Thay vì tính theo USD, ta tính theo R (Risk). Nếu mỗi lệnh bạn rủi ro 1% tài khoản (1R = 1%), tổng lợi nhuận `118.0` nghĩa là bạn lãi 118% tài khoản. Metric này độc lập với kích thước tài khoản.
*   **max_drawdown_r**: Chuỗi thua lỗ liên tiếp lớn nhất tính theo R. Drawdown `3.0` nghĩa là tài khoản của bạn từng suy giảm tối đa 3R (3% nếu rủi ro 1%) từ đỉnh. Đây là thước đo rủi ro quan trọng nhất.
*   **profit_factor**: Tỷ lệ *Tổng Số Tiền Thắng / Tổng Số Tiền Thua*. Từ 1.0 trở lên là có lãi. Mức `2.0+` của các quỹ Prop Firm là rất cao, mức `4.37` như trên là cực kì lý tưởng.

---

## 2. Cách Đọc Biểu Đồ Hiệu Suất

Hệ thống sinh ra 3 file báo cáo trực quan trong thư mục `reports/`.

### 2.1 Interactive Candlestick Chart (`candlestick.html`)
Mở file này bằng trình duyệt web. Nó sử dụng Plotly mượt mà.
- **Biểu đồ nến**: OHLCV truyền thống.
- **RSI / Indicator**: Các chỉ báo phụ nằm ở Panel phía dưới.
- **Markers (Ký hiệu)**:
  - 🔼 **Tam giác xanh**: Vị trí mô hình vào lệnh LONG.
  - 🔽 **Tam giác đỏ/hồng**: Vị trí mô hình vào lệnh SHORT.
> *Mẹo*: Hãy phóng to vào các khu vực xuất hiện marker để xem xét tính hợp lý (price action) mà mô hình thực hiện. Mô hình có đang bán ở ngọn nến S/R không? Có đang mua khi RSI quá bán?

### 2.2 Equity & Drawdown Curve (`*_equity.png`)
Mở file ảnh này để có cái nhìn tổng quan về đường dài.
- **Panel trên (Màu Vàng)**: Đường cong tài sản `Cumulative R`. Đường cong lý tưởng sẽ đi lên tuyến tính từ góc dưới bên trái lên góc trên bên phải. Nếu đường đi ngang quá lâu, chiến lược rơi vào chu kỳ Sideway.
- **Panel dưới (Màu Đỏ)**: Under-water curve (Drawdown). Hiển thị mức độ sụt giảm so với đỉnh gần nhất. Nếu vùng đỏ chạm các mức như `-10R` hay sâu hơn, chiến lược của bạn có rủi ro cháy tài khoản nếu không quản lý vốn chặt (chẳng hạn hạ Risk xuống 0.5%).

### 2.3 Session Performance Heatmap (`*_heatmap.png`)
Đây là công cụ quan trọng để tinh chỉnh theo phong cách **ICT Killzones**.
- **Trục Y (Dọc)**: Khung giờ UTC (0 đến 23).
- **Trục X (Ngang)**: Thứ trong tuần (Mon → Fri).
- **Màu sắc**: Màu xanh (Lãi), màu đỏ (Lỗ), màu vàng/nhạt (Hoà vốn).
> *Cách dùng*: Nếu bạn nhận thấy từ 13:00 UTC đến 16:00 UTC (Tương ứng New York Killzone) có màu anh đậm, hãy lọc Bot AI chỉ giao dịch vào khung giờ đó và báo nó bỏ qua các Asian/London sessions nhiều rủi ro.

---

## 3. Cách chạy mô phỏng sau khi Train Model

Sau khi chạy xong model ML (ví dụ KNN ở `models/knn.py`) và trích xuất dự đoán `predictions.parquet`. Hoặc thậm chí là từ Label thô ở quá khứ:

```bash
# Chạy Python CLI
cd /home/ultimatebrok/Downloads/ML_FX
pixi run python -c "
import polars as pl
from eval.backtest import simulate_trades, compute_metrics
from viz.charts import generate_full_report
from pathlib import Path

# Đọc data đã có Label (hoặc predict)
df = pl.read_parquet('data/labels/XAUUSD/1H/2026-02.parquet')

# Cấu hình R:R = 1.5 (TP 1.5R, SL 1.0R)
trades = simulate_trades(df, signal_col='label_5', tp_r=1.5, sl_r=1.0)
metrics = compute_metrics(trades)

print('Metrics:', metrics)

# Tạo báo cáo ở folder /reports/
generate_full_report('XAUUSD', '1H', df, trades, 'label_5_R15', Path('reports'))
"
```
