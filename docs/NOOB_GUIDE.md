# Cấu phẫu Hệ thống: Hướng dẫn cho Người Mới 🧠

Chào mừng! Thay vì làm bạn bối rối với dòng mã dày đặc ngay lập tức, tài liệu này giải thích **cách bot hoạt động ở hậu trường**. Bằng cách hiểu bức tranh toàn cảnh, bạn sẽ dễ dàng làm chủ dự án hơn.

Hãy nghĩ việc tạo ra một bot giao dịch AI giống như chế biến hạt cà phê thô thành một ly espresso hoàn hảo. Nó yêu cầu một Đường ống Dữ liệu (Data Pipeline) cấu trúc 4 bước.

---

## 🔧 4 Giai Đoạn Lõi

### 1️⃣ Trích Xuất Dữ Liệu Thô (Từ Tick sang Nến)
Thị trường ghi lại dữ liệu bằng các "Tick" (mọi biến động giá đơn lẻ). Máy tính không thể học dễ dàng từ dữ liệu tick thô này bởi có quá nhiều độ nhiễu.
Tệp lệnh `resample.py` nén lại hàng triệu dữ liệu tick thô thành dữ liệu cấu trúc gọi là Nến - Candlesticks (như nến 1 Giờ, 5 Phút, hoặc 15 Phút).

### 2️⃣ Trích Xuất Đặc Trưng (Bổ Sung Chi Tiết Cho AI)
Nếu bạn chỉ cung cấp cho AI hàng loạt nến màu xanh và đỏ, nó không thể xác định đâu là đỉnh đâu là đáy.
Tệp lệnh `features.py` tính toán và gán trên 133 chỉ báo kỹ thuật vào các biểu đồ nến này.
*   **Ví dụ:** Một cây nến cụ thể mới sẽ có một mác nhận diện "RSI là 30 (quá bán)" hoặc "Giá đang cách đỉnh kháng cự tuần vùng 5 pip." Quá trình này giúp biểu đồ cung cấp bối cảnh chuẩn xác để con AI cảm nhận được thị trường.

### 3️⃣ Gắn Nhãn (Chấm Điểm Bài Tập)
Trong huấn luyện hệ thống trí tuệ, bạn cần cung cấp các trải nghiệm học hỏi quá khứ đã đi kèm với kết quả điền trước.
Tệp lệnh `labels.py` có nhiệm vụ "nhìn trước" tương lai. Nếu nó thấy biểu đồ Vàng nhảy vọt 10 nến sau ngày xuất phát, nó ghi nhận sự bắt đầu này là "LONG". Quá trình sẽ lặp đên khi các nến lên tới tỷ chiếc trong quá khứ 10 năm.

### 4️⃣ Khởi Tạo Thuật Toán Học Máy (Máy Thông Minh Truy Tìm Dữ Liệu Lịch Sử)
Nhập các tính toán này lại (Đặc Trưng và Nhãn). Truyền dữ liệu vào công nghệ máy học tân tiến như XGBoost hay cấu trúc mạng Nơ-ron nhân tạo LSTM.
Hệ AI đọc phân tích dữ liệu và ra quy định luật mới:
> *"Ôi! Mình vừa thu được một chi tiết, bất kì khi nào đường chỉ chuẩn MACD chéo lên VÀ RSI đã vượt qua quá 30 tại Khung thị trường London... cơ hội nhận lệnh LONG thành công tính đạt mốc 70%!"*

### 5️⃣ Backtesting (Thiết Bị Giả Lập Môi Trường Giao Dịch)
Đừng bao giờ bật trực tiếp hệ thống ứng dụng khi vừa thiết lập thành công.
Hệ cài chức năng `backtest.py` chạy phần điều phối với AI bằng dữ kiện hoàn toàn có tính mù định vị - thực thi quản lý tiền bảo hộ khắt khe - Ví dụ (đổi $100 rủi ro vì thu 150$).
Khi máy hoàn thiện bộ mô phỏng giả lặp đó, báo cáo sẽ ghi nhận % Giao Lãi & Đường Dữ Liệu Tiền Thưởng Tài Sản Của Người Theo (Equity curve).

Hãy coi chi tiết phần này ở [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) để học phân tích các con tỉ số này.

---

## 🎯 Góc Phân Tích Của Hệ AI ML_FX

Bạn mới thử dùng ư, nên nhớ những yếu tố sau:

1. **Bot Này Không Phải Quả Cầu Pha Lê:** Hệ thống AI không dự đoán mọi nước tỷ chuẩn xác cao. Nó thuần tùy cấu hình toán học dựa trên lịch sử - cần bảo trợ chốt stop loss cực chuẩn xác - tránh thảm họa đánh mất dòng tài chính
2. **Hãy Theo Quy Tắc Quy Trình 1 Trượt Nhẹ Sẽ Đền To:** Phải liên kết Pipeline lần lượt **Dữ liệu thô -> Chế vào loại Nến Thời Gián -> Đưa phần Chỉ báo thông tin -> Quản lý điểm đến kết cục => Chấp thuận Dữ Kiện Chạy Máy Học Train**. Rối bước huấn luận hệ AI bạn sẽ vấp cự phải Lỗi báo tập tin thất lạc "File Missing". Xem kĩ cấu hình theo lịch thao tác của `[USAGE_GUIDE.md](USAGE_GUIDE.md)`.
3. **Tra cứu ở thuật ngữ Glossary:** Chập chờn ngôn nhãn loại `Tick, Parquet, OHLCV, Optuna` => Hãy lùi tra về thư pháp tiếng từ trong file gốc [`GLOSSARY.md`](GLOSSARY.md).
4. **Đừng Nên Quá Cứng Cú Nhác Có Trục Trặc**: Quản lý thiết bị terminal có ra bảng lỗi đi thì mở bài [TROUBLESHOOTING.md](TROUBLESHOOTING.md). Cứ thế giải mã 99% các hố chết rào máy trạm từ cơ bản tới nâng cao độ chiêu.

---

Sẵn tới đâu rồi! Di chuyển đọc đến bài Hướng Dẫn Sử Dụng [USAGE_GUIDE.md](USAGE_GUIDE.md) và gõ lệnh xem sao!
