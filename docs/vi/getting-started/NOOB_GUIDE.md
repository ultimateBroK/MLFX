# MLFX – Hướng dẫn nhập môn

Nếu bạn mới vào kho mã này, hãy đọc tài liệu này trước.  
Mục tiêu của file này là giúp bạn hiểu:

- Dự án này dùng để làm gì
- Dữ liệu đi qua những bước nào
- Vì sao phải chạy đúng thứ tự
- Sau mỗi bước bạn nên nhìn thấy kết quả gì
- Cách bắt đầu an toàn bằng `Pixi`

MLFX là môi trường **nghiên cứu, huấn luyện và đánh giá mô hình** trên dữ liệu thị trường. Đây **không phải** là một bot giao dịch trực tiếp hoàn chỉnh.

---

## 1. Dự án này dùng để làm gì?

MLFX là một quy trình học máy cho dữ liệu thị trường. Luồng cơ bản của dự án gồm:

- Tải dữ liệu tick lịch sử
- Chuyển dữ liệu đó thành OHLCV
- Tạo đặc trưng kỹ thuật và đặc trưng theo ngữ cảnh
- Tạo nhãn cho bài toán dự báo
- Huấn luyện mô hình
- Chạy đánh giá và xuất báo cáo

Hiểu ngắn gọn: MLFX giúp bạn đi từ **dữ liệu giá thô** đến **kết quả backtest có thể so sánh được** trong một quy trình nhất quán.

---

## 2. Luồng tổng quát của hệ thống

```text
1. Tải dữ liệu        → download
2. Chuẩn bị dữ liệu   → pipeline
3. Huấn luyện mô hình → train
4. Đánh giá kết quả   → evaluate
```

Nếu nói dễ hiểu hơn:

- `download` lấy dữ liệu giá lịch sử
- `pipeline` tạo nến, đặc trưng và nhãn
- `train` huấn luyện mô hình
- `evaluate` chạy backtest và sinh báo cáo

Sau bước `evaluate`, dòng lệnh sẽ in ra bảng chỉ số tổng hợp và đường dẫn tới các tệp báo cáo.

Mặc định:

- Nếu đã có mô hình phù hợp, hệ thống sẽ đánh giá **mô hình**
- Nếu chưa có mô hình, hệ thống có thể đánh giá **nhãn** như một mốc tham chiếu ban đầu

Các phần mã nguồn tương ứng nằm ở:

- `mlfx.ingestion`
- `mlfx.pipeline`
- `mlfx.training`
- `mlfx.evaluation`

---

## 3. Vì sao phải chạy đúng thứ tự?

Nhiều người mới thường muốn nhảy thẳng đến bước huấn luyện. Điều đó thường dẫn đến lỗi hoặc kết quả sai lệch. Mỗi bước trong MLFX tồn tại vì một lý do rõ ràng.

### Từ dữ liệu tick đến kiểm tra chất lượng

Sau khi tải dữ liệu, bạn nên kiểm tra dữ liệu thô để phát hiện:

- Khoảng trống dữ liệu
- Tháng bị lỗi
- Dữ liệu bất thường
- Tệp tải chưa đầy đủ

Bước này giúp tránh việc bạn huấn luyện trên dữ liệu có vấn đề mà không biết.

### Từ dữ liệu tick đến OHLCV

Dữ liệu tick rất dày và khó dùng trực tiếp cho phần lớn mô hình.  
Vì vậy hệ thống cần chuyển đổi chúng thành các cây nến như:

- `1m`
- `5m`
- `15m`
- `1H`

OHLCV là dạng dữ liệu gọn hơn, dễ phân tích hơn và phù hợp hơn cho các bước tiếp theo.

### Từ OHLCV đến đặc trưng

Sau khi có nến, hệ thống bổ sung ngữ cảnh bằng các đặc trưng như:

- RSI
- MACD
- ATR
- EMA
- Các mức điểm xoay
- Vùng hỗ trợ/kháng cự
- Phân phiên giao dịch
- Các đặc trưng theo ngữ cảnh ICT

Nói cách khác, thay vì đưa cho mô hình chỉ dữ liệu giá đơn thuần, bạn đưa cho nó dữ liệu giá **kèm ngữ cảnh đã được xử lý**.

### Từ đặc trưng đến nhãn

Các cột như:

- `label_5`
- `label_10`
- `label_20`

biến dữ liệu thành bài toán học có giám sát.  
Không có nhãn thì mô hình không biết cần học để dự báo điều gì.

### Từ nhãn đến huấn luyện mô hình

Sau khi dữ liệu đã sẵn sàng, bạn mới đến bước huấn luyện. Hiện tại CLI hỗ trợ các bộ máy:

- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

Mỗi bộ máy là một hướng tiếp cận khác nhau để học từ cùng một bộ dữ liệu.

### Từ huấn luyện đến đánh giá

Bước `evaluate` không chỉ đơn giản là “in ra vài con số”. Đây là nơi bạn kiểm tra:

- Mô hình có tạo ra tín hiệu dùng được hay không
- Backtest ra sao
- Lợi nhuận giả lập thế nào
- Rủi ro và độ ổn định có chấp nhận được không

Nói ngắn gọn: nếu chưa đánh giá thì chưa thể kết luận mô hình có ích.

---

## 4. Cách bắt đầu đúng

Nếu bạn muốn chạy nhanh toàn bộ quy trình theo lối ngắn nhất, hãy đọc:

- [Bắt đầu nhanh](QUICKSTART.md)

File này giữ vai trò **bắt đầu nhanh chuẩn**.  
Còn file hiện tại giữ vai trò **nhập môn**, nghĩa là giúp bạn hiểu:

- Dự án làm gì
- Thứ tự các bước có ý nghĩa gì
- Vì sao mỗi bước đều quan trọng
- Sau mỗi bước thì nên kiểm tra điều gì

Nếu bạn mới vào kho mã, cách đọc hợp lý nhất là:

1. Đọc file này
2. Chạy theo `QUICKSTART.md`
3. Sau đó mới sang tài liệu sử dụng chi tiết

---

## 5. Sau mỗi bước bạn nên thấy gì?

Khi mới làm quen, cách tốt nhất để không bị rối là kiểm tra “dấu hiệu thành công” sau từng bước.

### Sau `download`
Bạn nên thấy:

- Các tệp parquet trong `data/raw/{symbol}/`
- Tệp `completed_months.json`

Ví dụ:
- `data/raw/XAUUSD/YYYY-MM.parquet`
- `data/raw/XAUUSD/completed_months.json`

### Sau `qa`
Bạn nên thấy:

- Báo cáo kiểm tra chất lượng trong `data/raw/{symbol}/`

### Sau `pipeline`
Bạn nên thấy dữ liệu được sinh ở các khu vực:

- `data/ohlcv/`
- `data/features/`
- `data/labels/`

Đây là dấu hiệu cho thấy dữ liệu đã đi qua các bước chuyển đổi cần thiết.

### Sau `train`
Bạn nên thấy tệp đầu ra của mô hình trong:

- `outputs/models/{symbol}/{tf}/`

Thông thường nơi này sẽ chứa:
- Mô hình đã lưu
- Siêu dữ liệu
- Chỉ số huấn luyện

### Sau `evaluate`
Bạn nên thấy báo cáo trong:

- `outputs/reports/{symbol}/{tf}/`

Thường sẽ có:
- Báo cáo HTML biểu đồ nến
- Biểu đồ đường vốn
- Bản đồ nhiệt theo phiên hoặc theo thời gian

---

## 6. Những điều quan trọng nên nhớ

Khi mới dùng MLFX, hãy nhớ vài nguyên tắc đơn giản sau:

- Nếu bước huấn luyện báo thiếu tệp, nguyên nhân thường là bạn **chưa chạy `pipeline`**
- Nếu bước đánh giá không có gì để đọc, hãy kiểm tra xem bạn đã có:
  - Dữ liệu nhãn
  - Mô hình đã huấn luyện
  - Đúng tên cột nhãn
- `outputs/models/{symbol}/{tf}/` là nơi lưu mô hình
- `outputs/reports/{symbol}/{tf}/` là nơi lưu báo cáo đánh giá
- `pixi run clean-generated` dùng để dọn vùng nhớ đệm và đầu ra sinh tự động mà **không đụng vào dữ liệu thô**

---

## 7. Khi nào nên dùng bước kiểm tra chất lượng?

Nhiều người mới hỏi: “Có nhất thiết phải chạy `qa` ngay không?”

Câu trả lời là:

- **không bắt buộc** nếu bạn chỉ đang chạy thử nhanh lần đầu
- **nên dùng** khi:
  - Bạn nghi dữ liệu có lỗi
  - Bạn muốn kiểm tra độ tin cậy của dữ liệu trước khi huấn luyện
  - Bạn đang làm nghiên cứu nghiêm túc và cần loại trừ rủi ro từ đầu vào

Vì vậy, với người mới:
- Có thể bỏ qua `qa` trong lần chạy đầu tiên
- Nhưng nên biết bước này tồn tại để dùng khi cần

---

## 8. Một lộ trình học kho mã dễ chịu

Nếu bạn không muốn bị ngợp, hãy đi theo thứ tự sau:

### Bước 1 — Hiểu ý tưởng chung
Đọc file này để hiểu:
- Dự án làm gì
- Dữ liệu đi như thế nào
- Thứ tự các bước có ý nghĩa gì

### Bước 2 — Chạy thử một vòng hoàn chỉnh
Đọc và làm theo:
- [Bắt đầu nhanh](QUICKSTART.md)

### Bước 3 — Học cách điều khiển bằng dòng lệnh
Đọc:
- [../guides/USAGE_GUIDE.md](../guides/USAGE_GUIDE.md)

### Bước 4 — Học cách đọc kết quả
Đọc:
- [../guides/EVALUATION_GUIDE.md](../guides/EVALUATION_GUIDE.md)

### Bước 5 — Khi gặp lỗi
Đọc:
- [../guides/TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md)

### Bước 6 — Khi muốn hiểu sâu hơn
Đọc thêm:
- [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
- [../reference/GLOSSARY.md](../reference/GLOSSARY.md)
- [../reference/FEATURE_REFERENCE.md](../reference/FEATURE_REFERENCE.md)

---

## 9. Tóm tắt ngắn gọn

Nếu bạn chỉ cần nhớ một điều, hãy nhớ điều này:

MLFX không phải là nơi để chạy bừa một lệnh rồi mong có kết quả đúng ngay.  
Đây là một quy trình có thứ tự, và mỗi bước đều chuẩn bị cho bước tiếp theo.

Thứ tự an toàn nhất là:

```text
download → pipeline → train → evaluate
```

Nếu cần cẩn thận hơn với dữ liệu, hãy chèn thêm bước:

```text
download → qa → pipeline → train → evaluate
```

---

## 10. Đọc tiếp gì?

- [Bắt đầu nhanh](QUICKSTART.md) — cách chạy nhanh toàn bộ quy trình
- [../guides/USAGE_GUIDE.md](../guides/USAGE_GUIDE.md) — cách dùng từng lệnh
- [../guides/EVALUATION_GUIDE.md](../guides/EVALUATION_GUIDE.md) — cách đọc kết quả backtest
- [../guides/TROUBLESHOOTING.md](../guides/TROUBLESHOOTING.md) — xử lý lỗi môi trường và dữ liệu
- [../reference/GLOSSARY.md](../reference/GLOSSARY.md) — các thuật ngữ thường gặp
- [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) — kiến trúc hệ thống
