# So sánh các bộ máy huấn luyện trong MLFX

Tài liệu này so sánh các bộ máy huấn luyện hiện đang được cung cấp qua CLI `mlfx train` để bạn chọn đúng bộ máy cho nhu cầu của mình.

---

## 1. Khuyến nghị nhanh

Nếu bạn muốn con đường ngắn nhất để có một mốc nền mạnh:

- Bắt đầu với `mlf`
- So sánh thêm với `stats` và `sgd`
- Chỉ chuyển sang các bộ máy học sâu nếu bạn có lý do rõ ràng, chẳng hạn:
  - Cần mô hình hóa mẫu chuỗi
  - Cần cửa sổ huấn luyện dài hơn
  - Có đủ khối lượng dữ liệu
  - Có đủ ngân sách tính toán

Thứ tự thực tế nên đi là:

1. `stats`
2. `sgd`
3. `mlf`
4. `lstm`
5. `bilstm`
6. `cnn_lstm`
7. `transformer`
8. `neuralforecast`

---

## 2. Các bộ máy hiện có

CLI hiện hỗ trợ:

- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

---

## 3. Bảng so sánh tổng quan

| Bộ máy | Họ mô hình | Điểm mạnh | Điểm yếu | Yêu cầu dữ liệu | Chi phí tính toán | Khả năng diễn giải | Trường hợp dùng tốt nhất |
|---|---|---|---|---|---|---|---|
| `stats` | Mốc nền thống kê | nhanh, đơn giản, chi phí thấp | hạn chế trong mô hình hóa phi tuyến | thấp | rất thấp | cao | kiểm tra chuẩn, so sánh với mốc nền |
| `sgd` | ML tuyến tính / trực tuyến | nhanh, nhẹ, mở rộng tốt | yếu hơn với tương tác đặc trưng phức tạp | thấp đến trung bình | thấp | trung bình | dữ liệu bảng lớn, thí nghiệm rẻ |
| `mlf` | Tăng cường độ dốc / dự báo dạng bảng | mốc nền mạnh, xử lý tốt mẫu phi tuyến | không “thuần chuỗi” như học sâu | trung bình | trung bình | trung bình | mốc nền mặc định theo hướng vận hành thực dụng |
| `lstm` | Mô hình chuỗi học sâu | mô hình hóa phụ thuộc thời gian trực tiếp | chậm hơn, nhạy với tinh chỉnh | trung bình đến cao | cao | thấp | mẫu chuỗi theo rolling window |
| `bilstm` | Mô hình chuỗi hai chiều | ngữ cảnh phong phú hơn `lstm` thường | tốn hơn, có thể kém thực tế cho suy luận nhân quả nghiêm ngặt nếu dùng sai thiết lập | cao | cao | thấp | thí nghiệm offline với biểu diễn chuỗi giàu ngữ cảnh |
| `cnn_lstm` | DL lai | tốt cho trích xuất mẫu cục bộ + mô hình chuỗi | kiến trúc phức tạp hơn | cao | cao | thấp | mẫu nến / motif cục bộ kết hợp ngữ cảnh thời gian |
| `transformer` | DL dựa trên attention | linh hoạt cho phụ thuộc dài hạn | rất tốn tài nguyên, khó tinh chỉnh, cần nhiều dữ liệu | cao | rất cao | thấp | dữ liệu lớn, mô hình hóa ngữ cảnh dài |
| `neuralforecast` | Hệ sinh thái dự báo học sâu | mạnh cho thí nghiệm dự báo chuỗi thời gian | độ phức tạp thư viện và tinh chỉnh cao | trung bình đến cao | cao | thấp | thí nghiệm dự báo nâng cao |

---

## 4. Phân tích chi tiết từng bộ máy

## 4.1 `stats`

### Bản chất
`stats` là mốc nền thống kê đơn giản nhất. Nó hữu ích như một điểm tham chiếu trước khi thử các mô hình nâng cao hơn.

### Điểm mạnh
- Chạy nhanh nhất
- Độ phức tạp vận hành thấp nhất
- Cho bạn một mốc nền dễ giải thích
- Hữu ích để kiểm tra xem mô hình phức tạp có thực sự tạo thêm giá trị hay không

### Điểm yếu
- Khả năng mô hình hóa quan hệ phi tuyến hạn chế
- Thường kém hơn trên các bộ đặc trưng phong phú
- Có thể bỏ lỡ các hiệu ứng phụ thuộc regime hoặc tương tác mạnh

### Nên dùng khi
- Bạn cần một mốc kiểm tra chuẩn
- Bạn đang so sánh chuẩn nhiều bộ máy
- Bạn muốn kiểm tra pipeline end-to-end với chi phí thấp

### Tránh dùng khi
- Bạn kỳ vọng có nhiều tương tác phi tuyến phức tạp
- Bạn muốn hiệu năng dự báo tốt nhất

---

## 4.2 `sgd`

### Bản chất
`sgd` là một mốc nền ML nhẹ dựa trên stochastic gradient descent.

### Điểm mạnh
- Huấn luyện nhanh
- Dùng ít bộ nhớ
- Phù hợp cho thử nghiệm lặp nhanh
- Thường mạnh hơn mốc nền thống kê thuần túy

### Điểm yếu
- Vẫn khá đơn giản nếu so với boosted trees hoặc học sâu
- Hiệu năng phụ thuộc nhiều vào chất lượng đặc trưng và chuẩn hóa
- Có thể gặp khó nếu bề mặt quyết định có độ phi tuyến cao

### Nên dùng khi
- Bạn muốn một mốc nền ML chi phí thấp
- Bạn có dữ liệu bảng lớn
- Bạn cần vòng lặp phản hồi nhanh

### Tránh dùng khi
- Bài toán phụ thuộc mạnh vào quan hệ phi tuyến
- Bạn đã biết cấu trúc chuỗi là yếu tố then chốt

---

## 4.3 `mlf`

### Bản chất
`mlf` là mốc nền mặc định mạnh nhất cho phần lớn người dùng MLFX. Đây là điểm bắt đầu thực dụng nhất cho các thí nghiệm nghiêm túc.

### Điểm mạnh
- Thường là mô hình đầu tiên tốt nhất để thử
- Mạnh trên dữ liệu bảng đã được feature engineering
- Xử lý quan hệ phi tuyến tốt hơn các mô hình tuyến tính
- Cân bằng thực dụng giữa hiệu năng, tốc độ và khả năng bảo trì
- Thường dễ đưa vào vận hành hơn các bộ máy học sâu

### Điểm yếu
- Không “thuần chuỗi” theo cùng cách với mô hình hồi tiếp hoặc attention
- Có thể chạm trần nếu tín hiệu phụ thuộc mạnh vào ngữ cảnh thời gian dài
- Tìm kiếm siêu tham số có thể làm tăng thời gian chạy

### Nên dùng khi
- Bạn muốn bộ máy mặc định tốt nhất
- Bạn huấn luyện trên bảng đặc trưng đã được tạo
- Bạn cần một mốc so sánh chuẩn vững cho mọi bộ máy khác

### Tránh dùng khi
- Bạn thật sự cần mô hình chuỗi sâu
- Câu hỏi nghiên cứu của bạn tập trung vào học biểu diễn thời gian dài

---

## 4.4 `lstm`

### Bản chất
`lstm` là bộ máy mạng nơ-ron hồi tiếp được thiết kế cho mô hình hóa chuỗi.

### Điểm mạnh
- Mô hình hóa ngữ cảnh thời gian có thứ tự trực tiếp
- Hữu ích cho học tuần tự theo rolling window
- Có thể bắt được những mẫu không lộ rõ trong các hàng dữ liệu bảng độc lập

### Điểm yếu
- Huấn luyện chậm hơn
- Nhạy với độ dài cửa sổ và các siêu tham số khác
- Khó gỡ lỗi hơn mô hình ML đơn giản
- Có thể overfit nếu dữ liệu không đủ lớn

### Nên dùng khi
- Thứ tự thời gian là yếu tố rất quan trọng
- Bạn có đủ dữ liệu cho bài toán học chuỗi
- Bạn sẵn sàng đổi sự đơn giản lấy tính linh hoạt mô hình hóa

### Tránh dùng khi
- Bạn cần thí nghiệm nhanh
- Bạn có tập dữ liệu nhỏ
- `mlf` đã đủ tốt cho mục tiêu của bạn

---

## 4.5 `bilstm`

### Bản chất
`bilstm` là biến thể LSTM hai chiều, mã hóa thông tin chuỗi theo cả hai hướng trong thiết lập huấn luyện.

### Điểm mạnh
- Biểu diễn chuỗi phong phú hơn `lstm` thường
- Có thể nắm bắt ngữ cảnh tốt hơn trong thí nghiệm offline
- Hữu ích khi ngữ cảnh cục bộ quanh mỗi điểm dữ liệu là quan trọng

### Điểm yếu
- Tốn tài nguyên hơn `lstm`
- Độ phức tạp tăng thêm có thể không mang lại cải thiện đáng kể
- Cần diễn giải rất cẩn thận trong quy trình chuỗi thời gian

### Nên dùng khi
- Bạn đang làm thí nghiệm mô hình hóa offline
- Bạn muốn kiểm tra xem mã hóa chuỗi phong phú hơn có giúp ích không
- Bạn đã xác nhận rằng mô hình chuỗi là hướng đáng đầu tư

### Tránh dùng khi
- Bạn muốn mô hình đơn giản nhất để triển khai
- Bạn vẫn đang xây mốc nền đầu tiên đủ mạnh

---

## 4.6 `cnn_lstm`

### Bản chất
`cnn_lstm` kết hợp trích xuất đặc trưng bằng tích chập với mô hình hóa chuỗi bằng hồi tiếp.

### Điểm mạnh
- Có thể học các motif cục bộ ngắn hạn trước khi tổng hợp theo chuỗi
- Hữu ích cho các cấu trúc giá lặp lại cục bộ
- Thường là điểm cân bằng tốt giữa mô hình hóa chuỗi thô và trích xuất mẫu phân cấp

### Điểm yếu
- Phức tạp hơn mô hình hồi tiếp thuần
- Khó tinh chỉnh hơn
- Chi phí huấn luyện vẫn cao
- Khả năng diễn giải thấp hơn

### Nên dùng khi
- Bạn nghi ngờ các mẫu cửa sổ cục bộ là quan trọng
- Bạn muốn kết hợp phát hiện motif với mô hình hóa thời gian
- `lstm` thuần không đủ biểu đạt

### Tránh dùng khi
- Bạn cần một mốc nền thí nghiệm đơn giản
- Ngân sách tính toán của bạn bị hạn chế

---

## 4.7 `transformer`

### Bản chất
`transformer` là bộ máy học sâu dựa trên cơ chế chú ý cho mô hình hóa chuỗi.

### Điểm mạnh
- Kiến trúc linh hoạt cho phụ thuộc dài hạn
- Năng lực biểu diễn mạnh
- Hấp dẫn với dữ liệu lớn và ngữ cảnh dài hơn

### Điểm yếu
- Gánh nặng tinh chỉnh cao nhất trong các lựa chọn phổ biến
- Tốn bộ nhớ và tính toán
- Có thể kém hơn bộ máy đơn giản trên tập dữ liệu vừa hoặc nhỏ
- Rất dễ bị dùng quá sớm trước khi có mốc nền mạnh

### Nên dùng khi
- Bạn có nhiều dữ liệu
- Bạn muốn mô hình hóa ngữ cảnh dài hạn hơn
- Bạn đang nghiên cứu rõ ràng về mô hình chuỗi dựa trên attention

### Tránh dùng khi
- Bạn đang ở giai đoạn đầu dự án
- Bạn cần chu kỳ huấn luyện nhanh
- Bạn chưa so sánh chuẩn `mlf` hoặc `lstm`

---

## 4.8 `neuralforecast`

### Bản chất
`neuralforecast` là bộ máy học sâu theo hướng dự báo, xây trên một hệ sinh thái chuyên biệt cho mô hình chuỗi thời gian.

### Điểm mạnh
- Tốt cho các thí nghiệm dự báo nâng cao
- Có thể cho phép tiếp cận nhiều kiến trúc hơn thay vì một mô hình tự cài đặt duy nhất
- Hữu ích khi quy trình của bạn gần với hướng nghiên cứu dự báo

### Điểm yếu
- Tăng độ phức tạp thư viện và tích hợp
- Tốn chi phí huấn luyện và tinh chỉnh
- Không phải lúc nào cũng là lựa chọn đơn giản nhất cho quy trình ra quyết định kiểu phân loại

### Nên dùng khi
- Bạn muốn khám phá các phương pháp nơ-ron được thiết kế sẵn cho bài toán dự báo
- Bạn đã quen với các thí nghiệm sâu hơn
- Bài toán của bạn hưởng lợi từ thiết lập thiên về dự báo

### Tránh dùng khi
- Bạn chỉ cần mô hình thực dụng đầu tiên
- Sự đơn giản trong vận hành quan trọng hơn độ rộng thí nghiệm

---

## 5. Hướng dẫn chọn theo mục tiêu

## 5.1 Tôi muốn mốc nền hữu ích nhanh nhất
Hãy chọn:

1. `stats`
2. `sgd`
3. `mlf`

Bắt đầu bằng `stats`, sau đó sang `sgd`, rồi đến `mlf`.

---

## 5.2 Tôi muốn bộ máy mặc định thực dụng nhất
Hãy chọn:

- `mlf`

Đây thường nên là lần so sánh chuẩn nghiêm túc đầu tiên của bạn.

---

## 5.3 Tôi muốn mô hình hóa chuỗi thời gian trực tiếp
Hãy chọn trong:

- `lstm`
- `bilstm`
- `cnn_lstm`
- `transformer`

Thứ tự khuyến nghị:

1. `lstm`
2. `bilstm`
3. `cnn_lstm`
4. `transformer`

---

## 5.4 Tôi muốn chi phí tính toán thấp nhất
Hãy chọn:

- `stats`
- `sgd`

---

## 5.5 Tôi muốn mô hình dễ giải thích nhất
Hãy chọn:

- `stats`
- `sgd`
- `mlf`

Các bộ máy học sâu kém minh bạch hơn.

---

## 5.6 Tôi muốn độ rộng thí nghiệm nâng cao
Hãy chọn:

- `transformer`
- `neuralforecast`
- `cnn_lstm`

Những lựa chọn này phù hợp nhất khi bạn đã có các mốc so sánh chuẩn đơn giản hơn đủ chắc.

---

## 6. Chiến lược so sánh chuẩn thực tế

Một bậc thang thí nghiệm hợp lý là:

### Giai đoạn 1 — Mốc nền chi phí thấp
- `stats`
- `sgd`

### Giai đoạn 2 — Mốc so sánh chuẩn mặc định mạnh
- `mlf`

### Giai đoạn 3 — Mô hình chuỗi
- `lstm`
- `bilstm`

### Giai đoạn 4 — Học sâu phức tạp hơn
- `cnn_lstm`
- `transformer`
- `neuralforecast`

Mục tiêu không phải là huấn luyện tất cả ngay lập tức. Mục tiêu là xây niềm tin từng bước.

---

## 7. Ma trận quyết định gợi ý

| Tình huống | Bộ máy khuyến nghị |
|---|---|
| Người mới vào kho mã, lần chạy nghiêm túc đầu tiên | `mlf` |
| Cần mốc sanity-check | `stats` |
| Cần mốc nền ML rẻ | `sgd` |
| Muốn cân bằng tốt nhất giữa tính thực dụng và sức mạnh | `mlf` |
| Nghi ngờ phụ thuộc chuỗi mạnh | `lstm` |
| Muốn biểu diễn chuỗi giàu ngữ cảnh hơn | `bilstm` |
| Muốn motif cục bộ + mô hình hóa chuỗi | `cnn_lstm` |
| Muốn thí nghiệm attention dài hạn | `transformer` |
| Muốn thí nghiệm nơ-ron theo hướng dự báo | `neuralforecast` |

---

## 8. Heuristic về mức sẵn sàng cho vận hành thực tế

Đây là một bộ kinh nghiệm thực dụng, không phải quy tắc cứng.

| Bộ máy | Độ đơn giản khi vận hành | Độ ổn định khi huấn luyện | Độ đơn giản khi triển khai | Mức thân thiện tổng thể với vận hành thực tế |
|---|---|---|---|---|
| `stats` | cao | cao | cao | cao |
| `sgd` | cao | cao | cao | cao |
| `mlf` | cao | cao | trung bình đến cao | cao |
| `lstm` | trung bình | trung bình | trung bình | trung bình |
| `bilstm` | trung bình | trung bình | trung bình | trung bình |
| `cnn_lstm` | thấp đến trung bình | trung bình | trung bình | trung bình |
| `transformer` | thấp | thấp đến trung bình | trung bình | thấp đến trung bình |
| `neuralforecast` | trung bình | trung bình | trung bình | trung bình |

Với phần lớn nhóm phát triển, `mlf` là điểm khởi đầu thực tế nhất theo định hướng vận hành thực dụng.

---

## 9. Quy trình mặc định được khuyến nghị

Nếu bạn chưa chắc, hãy làm như sau:

```text
1. Chạy `stats`
2. Chạy `sgd`
3. Chạy `mlf`
4. So sánh các chỉ số đánh giá
5. Chỉ sau đó mới thử `lstm` hoặc các bộ máy học sâu khác
```

Điều này giúp tránh đầu tư quá nhiều vào mô hình phức tạp trước khi chứng minh rằng chúng thực sự cần thiết.

---

## 10. Những sai lầm thường gặp

- Bắt đầu bằng `transformer` trước khi có mốc nền
- So sánh kết quả học sâu mà không có đối chứng
- Dùng bộ máy đắt đỏ khi dữ liệu quá ít
- Cho rằng mô hình phức tạp mặc định tốt hơn
- Bỏ qua chi phí vận hành khi chọn bộ máy
- Bỏ qua `stats` hoặc `sgd` và đánh mất một mốc kiểm tra chuẩn hữu ích
- Xem một lần backtest đẹp là đủ bằng chứng

---

## 11. Khuyến nghị cuối cùng

### Với phần lớn người dùng
Hãy dùng `mlf`.

### Với bài toán so sánh mốc nền
Hãy dùng `stats` và `sgd`.

### Với nghiên cứu chuỗi
Hãy bắt đầu bằng `lstm`, rồi thử `bilstm`.

### Với khám phá học sâu nâng cao
Hãy thử `cnn_lstm`, `transformer`, hoặc `neuralforecast` chỉ sau khi bạn đã hiểu rõ hành vi của các mốc nền đơn giản hơn.

---

## 12. Xem thêm

- [Kiến trúc hệ thống](ARCHITECTURE.md)
- [Hướng dẫn sử dụng](../guides/USAGE_GUIDE.md)
- [Hướng dẫn đánh giá](../guides/EVALUATION_GUIDE.md)
- [Tham chiếu cấu hình](../reference/CONFIG_REFERENCE.md)
- [Thuật ngữ](../reference/GLOSSARY.md)
