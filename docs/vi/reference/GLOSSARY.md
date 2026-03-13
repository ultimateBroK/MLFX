# MLFX - Thuật ngữ

Tài liệu này tập hợp các thuật ngữ thường gặp trong dự án MLFX.  
Mục tiêu là giúp bạn đọc tài liệu, dùng giao diện dòng lệnh và hiểu kết quả đầu ra mà không bị lẫn giữa các khái niệm kỹ thuật.

---

## 1. Dữ liệu thị trường

- `Dữ liệu tick`: Dữ liệu ở mức thay đổi giá nhỏ nhất, thường ghi lại từng lần giá cập nhật.
- `OHLCV`: Viết tắt của `Open`, `High`, `Low`, `Close`, `Volume`; tức giá mở cửa, cao nhất, thấp nhất, đóng cửa và khối lượng của một cây nến.
- `Khung thời gian` hoặc `TF`: Độ dài của một cây nến, ví dụ `1m`, `5m`, `15m`, `1H`, `4H`, `1D`.
- `Giá bid`: Giá bên mua trên thị trường.
- `Giá ask`: Giá bên bán trên thị trường.
- `Chênh lệch giá` (`spread`): Khoảng chênh giữa giá bid và giá ask.
- `Giá mid`: Giá trung điểm, thường tính bằng `(bid + ask) / 2`.
- `Dấu thời gian` (`timestamp`): Mốc thời gian gắn với từng dòng dữ liệu hoặc từng cây nến.
- `Parquet`: Định dạng tệp cột, thường dùng để lưu dữ liệu phân tích với hiệu năng tốt.
- `Khoảng trống dữ liệu`: Vùng thời gian bị thiếu dữ liệu so với kỳ vọng.
- `Dữ liệu thô`: Dữ liệu chưa qua xử lý, thường nằm trong `data/raw/`.
- `Dữ liệu đã xử lý`: Dữ liệu đã đi qua các bước chuyển đổi, tạo đặc trưng hoặc gắn nhãn.

---

## 2. Khái niệm giao dịch

- `Hỗ trợ` (`support`): Vùng giá mà lực mua thường xuất hiện mạnh hơn, khiến giá có xu hướng chững lại hoặc bật lên.
- `Kháng cự` (`resistance`): Vùng giá mà lực bán thường xuất hiện mạnh hơn, khiến giá có xu hướng chững lại hoặc quay đầu.
- `Điểm xoay` (`pivot point`): Các mức giá tham chiếu được tính từ dữ liệu phiên trước để làm mốc hỗ trợ / kháng cự.
- `Khung giờ trọng điểm`: Các khung giờ có thanh khoản cao theo cách tiếp cận ICT, ví dụ phiên London hoặc New York.
- `LONG`: Tín hiệu kỳ vọng giá tăng.
- `SHORT`: Tín hiệu kỳ vọng giá giảm.
- `TRUNG LẬP` (`neutral`): Không có tín hiệu đủ mạnh để vào lệnh.
- `Chốt lời` (`take-profit`, `TP`): Mức giá hoặc mức lợi nhuận mục tiêu để đóng lệnh có lãi.
- `Dừng lỗ` (`stop-loss`, `SL`): Mức giá hoặc mức rủi ro tối đa chấp nhận để đóng lệnh thua.
- `Lệnh vào`: Thời điểm mở vị thế.
- `Lệnh ra`: Thời điểm đóng vị thế.
- `Backtest`: Mô phỏng giao dịch trên dữ liệu lịch sử để đánh giá chiến lược hoặc mô hình.
- `Bộ mô phỏng giao dịch`: Thành phần dùng để biến tín hiệu thành lệnh giả lập và tính kết quả.
- `Đơn vị R` hoặc `R-multiple`: Đơn vị lợi nhuận / rủi ro chuẩn hóa theo mức rủi ro ban đầu của một lệnh.
- `Hoa hồng giao dịch` (`commission`): Chi phí giao dịch bị trừ vào kết quả mô phỏng.
- `Trượt giá` (`slippage`): Chênh lệch giữa giá kỳ vọng và giá khớp lệnh giả lập.
- `Đường vốn` (`equity curve`): Đường biểu diễn tăng trưởng hoặc suy giảm vốn theo thời gian.
- `Sụt giảm vốn` (`drawdown`): Mức giảm từ đỉnh vốn xuống đáy vốn trong một giai đoạn.

---

## 3. Xây dựng đặc trưng

- `Đặc trưng` (`feature`): Biến đầu vào được dùng để huấn luyện hoặc suy luận mô hình.
- `Xây dựng đặc trưng`: Quá trình tạo thêm các cột mang thông tin hữu ích từ dữ liệu giá gốc.
- `Chuẩn hóa`: Biến đổi dữ liệu để các giá trị có cùng thang đo hoặc dễ so sánh hơn.
- `RSI`: Chỉ số sức mạnh tương đối, đo động lượng tăng giảm của giá.
- `MACD`: Chỉ báo hội tụ / phân kỳ trung bình động.
- `EMA`: Đường trung bình động lũy thừa.
- `ATR`: Biên độ thực trung bình, dùng để đo độ biến động.
- `Khối lệnh` (`order block`): Vùng giá thường được xem là nơi có dấu vết của dòng tiền lớn theo cách nhìn cấu trúc thị trường.
- `Vùng mất cân bằng giá trị hợp lý` (`fair value gap`, `FVG`): Khoảng mất cân bằng giữa các cây nến, thường được dùng làm ngữ cảnh giá.
- `Đặc trưng theo phiên`: Các cột phản ánh phiên giao dịch hoặc khung giờ thị trường.
- `Đặc trưng theo ngữ cảnh`: Các cột không chỉ phản ánh giá, mà còn phản ánh cấu trúc hoặc trạng thái thị trường.

---

## 4. Nhãn và huấn luyện

- `Nhãn` (`label`): Cột mục tiêu để mô hình học, ví dụ `label_5`, `label_10`, `label_20`.
- `Nhãn thứ bậc`: Loại nhãn có nhiều mức tăng / giảm khác nhau, ví dụ `-2`, `-1`, `0`, `1`, `2`.
- `Khoảng nhìn trước` (`look-ahead horizon`): Số cây nến nhìn về phía trước để tạo nhãn.
- `Hệ số ATR`: Hệ số dùng cùng ATR để tránh gắn nhãn quá nhiễu.
- `Bộ máy huấn luyện`: Một kiểu mô hình hoặc quy trình huấn luyện cụ thể.
- `Huấn luyện`: Quá trình cho mô hình học từ dữ liệu đã gắn nhãn.
- `Tập huấn luyện`: Phần dữ liệu dùng để dạy mô hình.
- `Tập xác thực`: Phần dữ liệu dùng để điều chỉnh mô hình trong quá trình huấn luyện.
- `Tập kiểm tra`: Phần dữ liệu dùng để đánh giá sau cùng.
- `Rò rỉ dữ liệu`: Tình huống thông tin từ tương lai vô tình lọt vào quá trình huấn luyện, làm kết quả đẹp giả tạo.
- `TimeSeriesSplit`: Cách chia dữ liệu theo thời gian cho bài toán chuỗi thời gian.
- `Kiểm định chéo`: Cách chia và lặp đánh giá mô hình nhiều lần để có kết quả ổn định hơn.
- `Tinh chỉnh siêu tham số`: Quá trình thử nhiều cấu hình của mô hình để tìm cấu hình tốt hơn.
- `Optuna`: Thư viện hỗ trợ tìm kiếm siêu tham số tự động.
- `Tệp đầu ra mô hình`: Các tệp đầu ra của quá trình huấn luyện, như mô hình đã lưu, cấu hình và chỉ số.
- `Sổ đăng ký mô hình` (`model registry`): Nơi lưu thông tin về các mô hình đã huấn luyện.
- `Theo dõi thí nghiệm`: Quá trình ghi lại tham số, chỉ số và đầu ra của từng lần huấn luyện.

---

## 5. Đánh giá và báo cáo

- `Tỷ lệ thắng` (`Win Rate`): Tỷ lệ phần trăm số lệnh có lãi.
- `Hệ số lợi nhuận` (`Profit Factor`): Tổng lãi chia cho tổng lỗ.
- `Lợi nhuận ròng` (`Net Profit`): Lợi nhuận cuối cùng sau khi trừ chi phí và lỗ.
- `Sharpe Ratio`: Chỉ số đo lợi nhuận so với mức biến động tổng thể.
- `Sortino Ratio`: Tương tự Sharpe nhưng chỉ tập trung vào biến động theo hướng bất lợi.
- `Calmar Ratio`: Lợi nhuận so với mức sụt giảm vốn lớn nhất.
- `Bản đồ nhiệt` (`heatmap`): Biểu đồ thể hiện hiệu suất theo giờ hoặc theo ngày trong tuần.
- `Báo cáo HTML biểu đồ nến`: Báo cáo trực quan hiển thị giá, tín hiệu và một số chỉ báo trên biểu đồ nến.
- `Mốc nền` (`baseline`): Kết quả đối chứng ban đầu để so sánh với các mô hình mạnh hơn.
- `Đánh giá ngoài mẫu`: Đánh giá trên dữ liệu mà mô hình chưa thấy trong huấn luyện.

---

## 6. Các bộ máy hiện có

- `mlf`: Quy trình `MLForecast + LightGBM`, thường là lựa chọn mặc định thực dụng.
- `lstm`: Mô hình LSTM dùng PyTorch.
- `sgd`: Mốc nền rất nhẹ dựa trên `SGDClassifier`.
- `stats`: Các mô hình thống kê cơ sở.

---

## 7. Đầu ra chính của kho mã

- `data/raw/`: Dữ liệu tick thô đã tải về.
- `data/ohlcv/`: Dữ liệu nến sau khi chuyển đổi từ dữ liệu tick.
- `data/features/`: Dữ liệu đã được bổ sung đặc trưng.
- `data/labels/`: Dữ liệu đã được gắn nhãn.
- `outputs/models/{symbol}/{tf}/{label}/`: Tệp đầu ra mô hình, chỉ số và siêu dữ liệu huấn luyện cho một nhãn cụ thể.
- `outputs/reports/{symbol}/{tf}/{label}/{mode}/{run}/`: Báo cáo backtest và hình ảnh liên quan, được nhóm theo nhãn, chế độ đánh giá và thư mục lần chạy như `R15`.
- `outputs/predictions/{symbol}/{tf}/{label}/`: Kết quả dự đoán theo lô cho một nhãn cụ thể.
- `outputs/monitoring/{symbol}/{tf}/`: Đầu ra phục vụ giám sát và phát hiện độ lệch dữ liệu.
- `outputs/runs/{symbol}/{tf}/`: Nhật ký các lần chạy khi dùng bộ theo dõi bằng tệp.

---

## 8. Giám sát và vận hành

- `Phục vụ mô hình` (`serving`): Quá trình đưa mô hình ra để nhận dữ liệu đầu vào và trả về kết quả dự đoán.
- `Suy luận` (`inference`): Quá trình dùng mô hình đã huấn luyện để tạo dự đoán mới.
- `Suy luận theo lô`: Chạy dự đoán cho một tập dữ liệu lớn rồi lưu thành tệp.
- `Suy luận thời gian thực`: Nhận yêu cầu qua API và trả dự đoán ngay.
- `FastAPI`: Khung làm việc web được dùng để tạo lớp phục vụ mô hình.
- `Kiểm tra sức khỏe` (`health check`): Điểm kiểm tra đơn giản để xác nhận dịch vụ còn hoạt động bình thường.
- `Độ lệch dữ liệu` (`data drift` / `feature drift`): Tình huống dữ liệu mới có phân phối khác đáng kể so với dữ liệu huấn luyện.
- `PSI`: Chỉ số ổn định dân số, một cách đo độ lệch phân phối.
- `KS test`: Phép kiểm định Kolmogorov–Smirnov, dùng để so sánh phân phối dữ liệu.
- `Ghi nhật ký có cấu trúc`: Ghi log theo định dạng máy có thể đọc dễ dàng, thường là JSON lines.

---

## 9. Tóm tắt ngắn

Nếu bạn mới vào kho mã, chỉ cần nhớ chuỗi khái niệm chính sau:

- dữ liệu tick → OHLCV → đặc trưng → nhãn → huấn luyện → đánh giá → báo cáo → phục vụ mô hình → giám sát

Đó là xương sống của toàn bộ MLFX.
