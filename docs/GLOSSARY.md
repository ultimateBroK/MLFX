# ML_FX - Thuật ngữ

Tài liệu này gom các thuật ngữ thường gặp trong repo.

## 1. Dữ liệu thị trường

- `Tick data`: dữ liệu ở mức từng thay đổi giá nhỏ nhất
- `OHLCV`: Open, High, Low, Close, Volume của một cây nến
- `Timeframe` hoặc `TF`: độ dài của một cây nến như `1m`, `5m`, `1H`
- `Spread`: chênh lệch giữa giá bid và ask

## 2. Khái niệm giao dịch

- `Support/Resistance`: vùng giá mà xu hướng thường chững lại hoặc phản ứng mạnh
- `Pivot Points`: các mức giá tham chiếu được tính từ dữ liệu phiên trước
- `Killzone`: các khung giờ thanh khoản cao theo cách tiếp cận ICT
- `LONG`: tín hiệu kỳ vọng giá tăng
- `SHORT`: tín hiệu kỳ vọng giá giảm
- `NEUTRAL`: không có tín hiệu đủ mạnh
- `R-multiple` hoặc `R`: đơn vị lợi nhuận và rủi ro chuẩn hóa theo mức risk mỗi lệnh
- `Commission`: chi phí giao dịch được trừ vào PnL giả lập
- `Slippage`: trượt giá giả lập khi vào hoặc thoát lệnh

## 3. Feature engineering

- `Feature`: biến đầu vào đưa vào model
- `ATR`: Average True Range, đo mức biến động
- `RSI`: Relative Strength Index
- `MACD`: Moving Average Convergence Divergence
- `EMA`: Exponential Moving Average
- `Order Block`: vùng giá thường được dùng như một tín hiệu cấu trúc
- `Fair Value Gap` hoặc `FVG`: khoảng trống giá trị giữa các nến

## 4. Label và huấn luyện

- `Label`: cột mục tiêu để model học, ví dụ `label_5`, `label_10`, `label_20`
- `Look-ahead horizon`: số nến nhìn trước để tạo label
- `ATR multiplier`: hệ số ATR dùng để tránh gắn nhãn quá nhiễu
- `Backend`: loại model hoặc pipeline huấn luyện
- `TimeSeriesSplit`: cách chia dữ liệu theo thời gian cho bài toán chuỗi thời gian
- `Optuna`: thư viện tìm kiếm siêu tham số

## 5. Đánh giá và report

- `Profit Factor`: tổng lãi chia tổng lỗ
- `Sharpe Ratio`: lợi nhuận trung bình so với độ biến động tổng thể
- `Sortino Ratio`: lợi nhuận trung bình so với downside volatility
- `Calmar Ratio`: lợi nhuận so với drawdown tối đa
- `Heatmap`: biểu đồ hiệu suất theo giờ UTC và ngày trong tuần

## 6. Các backend hiện có

- `mlf`: pipeline `MLForecast + LightGBM`
- `lstm`: model LSTM
- `transformer`: model Transformer cho chuỗi thời gian
- `cnn_lstm`: mô hình kết hợp CNN và LSTM
- `sgd`: online SGD baseline
- `stats`: baseline thống kê
- `neuralforecast`: backend NeuralForecast
- `bilstm`: backend có trong codebase nhưng chưa nằm trong CLI/TUI

## 7. Đầu ra của repo

- `data/raw/`: dữ liệu tick gốc
- `data/ohlcv/`: dữ liệu nến sau resample
- `data/features/`: dữ liệu đã thêm feature
- `data/labels/`: dữ liệu đã gắn nhãn
- `outputs/models/`: model artifacts, metrics và metadata train
- `outputs/reports/`: báo cáo backtest và biểu đồ
