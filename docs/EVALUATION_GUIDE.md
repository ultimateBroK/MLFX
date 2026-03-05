# ML_FX — Hướng dẫn Đánh giá (Evaluation)

Tài liệu này giải thích cách đọc kết quả Backtest và các biểu đồ phân tích hiệu suất (Visualization) của dự án ML_FX.

Hệ thống Evaluation (nằm trong thư mục `eval/` và `viz/`) cung cấp một cái nhìn chi tiết về cách mô hình Machine Learning sẽ hoạt động nếu giao dịch trên thị trường thực. Chúng tôi không sử dụng "độ chính xác" (accuracy) lý thuyết đơn thuần của Machine Learning; thay vào đó, chúng tôi chuyển đổi chúng thành một **Mô phỏng Walk-forward sử dụng R-multiples**.

---

## 1. Hiểu các chỉ số giao dịch (Trading Metrics)

Báo cáo sẽ xuất ra một từ điển Metrics như sau:
`Metrics: {'total_trades': 139, 'win_rate': 73.38, 'total_r': 118.0, 'max_drawdown_r': 3.0, 'profit_factor': 4.37}`

Ý nghĩa của các con số:
*   **total_trades (Tổng số lệnh)**: Tổng số lệnh giao dịch được mô phỏng.
*   **win_rate (%) (Tỷ lệ thắng)**: Phần trăm số lệnh chạm mức Chốt lời (TP) trước khi chạm mức Dừng lỗ (SL). Tuy nhiên, tỷ lệ thắng không phải là tất cả nếu tỷ lệ R:R không tốt.
*   **total_r (Tổng R tích lũy)**: Thay vì tính toán bằng đô la (USD), chúng tôi tính toán bằng R (Risk - Rủi ro). Nếu mỗi lệnh rủi ro 1% tài khoản của bạn (1R = 1%), tổng lợi nhuận `118.0` có nghĩa là bạn đã kiếm được 118% lợi nhuận trên tài khoản của mình. Chỉ số này độc lập với quy mô tài khoản.
*   **max_drawdown_r (Mức sụt giảm tối đa)**: Chuỗi thua lỗ liên tiếp lớn nhất tính bằng R. Một drawdown là `3.0` có nghĩa là mức sụt giảm tối đa của tài khoản tại bất kỳ thời điểm nào là 3R (hoặc 3% nếu rủi ro là 1%) từ đỉnh tài sản. Đây là chỉ số rủi ro quan trọng nhất.
*   **profit_factor (Hệ số lợi nhuận)**: Tỷ lệ giữa *Tổng lợi nhuận / Tổng thua lỗ*. Bất cứ giá trị nào trên 1.0 đều có lãi. Mức `2.0+` cho các quy tắc đánh giá của quỹ đầu tư (Prop Firm) là rất cao, mức `4.37` như trên là cực kỳ lý tưởng.

---

## 2. Cách đọc Biểu đồ Khảo sát Hiệu suất

Hệ thống tạo ra 3 tệp báo cáo trực quan trong thư mục `reports/`.

### 2.1 Biểu đồ Nến Tương tác (`candlestick.html`)
Mở tệp này bằng trình duyệt web của bạn. Nó tận dụng tính tương tác mượt mà của Plotly.
- **Biểu đồ nến**: OHLCV truyền thống.
- **RSI / Indicator**: Các chỉ báo phụ nằm ở Panel dưới cùng.
- **Markers (Đánh dấu)**:
  - 🔼 **Tam giác Xanh**: Mô hình đã thực hiện lệnh LONG (Mua).
  - 🔽 **Tam giác Đỏ/Hồng**: Mô hình đã thực hiện lệnh SHORT (Bán).
> *Mẹo*: Phóng to nhiều vào các khu vực có đánh dấu để kiểm tra các điều kiện hành động giá (price action) đằng sau các giao dịch của mô hình. Có phải nó đã bán ở đỉnh S/R? Có phải nó đã mua khi RSI đang quá bán?

### 2.2 Biểu đồ Vốn & Sụt giảm (`*_equity.png`)
Mở tệp hình ảnh này để xem tổng quan dài hạn.
- **Panel Trên (Màu vàng)**: Đường cong vốn (equity curve) `Cumulative R`. Một đường cong lý tưởng sẽ tăng đều đặn từ góc dưới bên trái lên góc trên bên phải. Nếu đường này đi ngang quá lâu, chiến lược đã rơi vào chu kỳ Sideway.
- **Panel Dưới (Màu đỏ)**: Đường cong sụt giảm (Drawdown). Hiển thị độ lớn của sự sụt giảm so với đỉnh gần nhất. Nếu các vùng màu đỏ chạm đến các mức sâu như `-10R` hoặc thấp hơn, chiến lược của bạn có rủi ro cháy tài khoản cao nếu không quản lý vốn chặt chẽ (như hạ Rủi ro xuống 0.5%).

### 2.3 Bản đồ Nhiệt Hiệu suất Theo Phiên (`*_heatmap.png`)
Đây là một công cụ quan trọng để tinh chỉnh chiến lược theo phong cách **ICT Killzones**.
- **Trục Y (Dọc)**: Khung giờ UTC (0 đến 23).
- **Trục X (Ngang)**: Ngày trong tuần (Thứ Hai → Thứ Sáu).
- **Màu sắc**: Xanh lá (Lãi), Đỏ (Lỗ), Vàng/Sáng (Hòa vốn).
> *Cách dùng*: Nếu bạn nhận thấy từ 13:00 UTC đến 16:00 UTC (Tương ứng với New York Killzone) có nhiều vùng màu xanh lá đậm, hãy lọc Bot AI để chỉ giao dịch trong khung thời gian này và khuyên nó bỏ qua các phiên Châu Á/Luân Đôn đầy rủi ro.

---

## 3. Cách Mô phỏng Sau khi Huấn luyện Mô hình

Sau khi mô hình ML đã huấn luyện xong (ví dụ: KNN trong `models/knn.py`) và tạo ra các dự đoán bên trong `predictions.parquet`. Hoặc thậm chí trực tiếp từ các nhãn lịch sử gốc:

```bash
# Chạy Python CLI
cd /home/ultimatebrok/Downloads/ML_FX
pixi run python -c "
import polars as pl
from eval.backtest import simulate_trades, compute_metrics
from viz.charts import generate_full_report
from pathlib import Path

# Đọc dữ liệu kèm Labels (hoặc predictions)
df = pl.read_parquet('data/labels/XAUUSD/1H/2026-02.parquet')

# Cấu hình R:R = 1.5 (TP 1.5R, SL 1.0R)
trades = simulate_trades(df, signal_col='label_5', tp_r=1.5, sl_r=1.0)
metrics = compute_metrics(trades)

print('Metrics:', metrics)

# Tạo báo cáo trong thư mục /reports/
generate_full_report('XAUUSD', '1H', df, trades, 'label_5_R15', Path('reports'))
"
```
