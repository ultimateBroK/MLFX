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

---

## 2. Các bộ máy hiện có

CLI hiện hỗ trợ:

- `mlf`
- `lstm`
- `sgd`
- `stats`

---

## 3. Bảng so sánh tổng quan

| Bộ máy | Họ mô hình | Điểm mạnh | Điểm yếu | Yêu cầu dữ liệu | Chi phí tính toán | Khả năng diễn giải | Trường hợp dùng tốt nhất |
|---|---|---|---|---|---|---|---|
| `stats` | Mốc nền thống kê | Nhanh, đơn giản, chi phí thấp | Hạn chế trong mô hình hóa phi tuyến | Thấp | Rất thấp | Cao | Kiểm tra chuẩn, so sánh với mốc nền |
| `sgd` | ML tuyến tính / trực tuyến | Nhanh, nhẹ, mở rộng tốt | Yếu hơn với tương tác đặc trưng phức tạp | Thấp đến trung bình | Thấp | Trung bình | Dữ liệu bảng lớn, thí nghiệm rẻ |
| `mlf` | Tăng cường độ dốc / dự báo dạng bảng | Mốc nền mạnh, xử lý tốt mẫu phi tuyến | Không “thuần chuỗi” như học sâu | Trung bình | Trung bình | Trung bình | Mốc nền mặc định theo hướng vận hành thực dụng |
| `lstm` | Mô hình chuỗi học sâu | Mô hình hóa phụ thuộc thời gian trực tiếp | Chậm hơn, nhạy với tinh chỉnh | Trung bình đến cao | Cao | Thấp | Mẫu chuỗi theo rolling window |

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

## 6. Chiến lược so sánh chuẩn thực tế

Một bậc thang thí nghiệm hợp lý là:

### Giai đoạn 1 — Mốc nền chi phí thấp
- `stats`
- `sgd`

### Giai đoạn 2 — Mốc so sánh chuẩn mặc định mạnh
- `mlf`

### Giai đoạn 3 — Mô hình chuỗi
- `lstm`

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

---

## 8. Heuristic về mức sẵn sàng cho vận hành thực tế

Đây là một bộ kinh nghiệm thực dụng, không phải quy tắc cứng.

| Bộ máy | Độ đơn giản khi vận hành | Độ ổn định khi huấn luyện | Độ đơn giản khi triển khai | Mức thân thiện tổng thể với vận hành thực tế |
|---|---|---|---|---|
| `stats` | Cao | Cao | Cao | Cao |
| `sgd` | Cao | Cao | Cao | Cao |
| `mlf` | Cao | Cao | Trung bình đến Cao | Cao |
| `lstm` | Trung bình | Trung bình | Trung bình | Trung bình |

Với phần lớn nhóm phát triển, `mlf` là điểm khởi đầu thực tế nhất theo định hướng vận hành thực dụng.

---

## 9. Quy trình mặc định được khuyến nghị

Nếu bạn chưa chắc, hãy làm như sau:

```text
1. Chạy `stats`
2. Chạy `sgd`
3. Chạy `mlf`
4. So sánh các chỉ số đánh giá
5. Chỉ sau đó mới thử `lstm`
```

Điều này giúp tránh đầu tư quá nhiều vào mô hình phức tạp trước khi chứng minh rằng chúng thực sự cần thiết.

---

## 10. Những sai lầm thường gặp

- Bắt đầu bằng `lstm` trước khi có mốc nền
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
Hãy bắt đầu bằng `lstm`.

---

## 12. Xem thêm

- [Kiến trúc hệ thống](ARCHITECTURE.md)
- [Hướng dẫn sử dụng](../guides/USAGE_GUIDE.md)
- [Hướng dẫn đánh giá](../guides/EVALUATION_GUIDE.md)
- [Tham chiếu cấu hình](../reference/CONFIG_REFERENCE.md)
- [Thuật ngữ](../reference/GLOSSARY.md)
