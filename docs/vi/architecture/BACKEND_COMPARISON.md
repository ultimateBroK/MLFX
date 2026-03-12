# So sánh backend huấn luyện trong MLFX

Tài liệu này giúp bạn chọn backend phù hợp khi chạy:

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend <backend>
```

Các backend hiện có trong MLFX:

- `mlf`
- `lstm`
- `bilstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

---

## 1. Tóm tắt nhanh: nên chọn backend nào?

Nếu bạn chỉ cần một khuyến nghị ngắn gọn:

- Chọn `mlf` nếu bạn muốn **điểm khởi đầu tốt nhất cho hầu hết workflow tabular/time-series feature-based**
- Chọn `lstm` hoặc `bilstm` nếu bạn muốn **thử deep learning cho dữ liệu chuỗi**
- Chọn `transformer` nếu bạn muốn **thử mô hình sequence hiện đại hơn**, chấp nhận train nặng hơn
- Chọn `cnn_lstm` nếu bạn muốn **mô hình lai** cho local patterns + temporal sequence
- Chọn `sgd` nếu bạn cần **baseline rất nhẹ, train nhanh**
- Chọn `stats` nếu bạn cần **baseline cổ điển / đối chứng đơn giản**
- Chọn `neuralforecast` nếu bạn muốn **mở rộng theo hướng neural forecasting ecosystem**

Nếu chưa chắc, hãy bắt đầu bằng:

1. `stats` hoặc `sgd` để lấy baseline nhẹ
2. `mlf` để có baseline mạnh thực dụng
3. Sau đó mới so với `lstm` / `bilstm` / `transformer` / `cnn_lstm`

---

## 2. Bảng so sánh tổng quan

| Backend | Loại mô hình | Mức độ train | Tài nguyên | Tốc độ thử nghiệm | Khả năng làm baseline | Khả năng mở rộng | Khi nào nên dùng |
|---|---|---:|---:|---:|---:|---:|---|
| `mlf` | MLForecast + LightGBM | Trung bình | Thấp–vừa | Nhanh | Tốt | Tốt | Lựa chọn mặc định cho phần lớn bài toán |
| `lstm` | Deep learning chuỗi | Trung bình–cao | Vừa–cao | Chậm hơn | Trung bình | Tốt | Khi muốn học temporal dependencies trực tiếp |
| `bilstm` | Bidirectional LSTM | Cao | Vừa–cao | Chậm | Trung bình | Tốt | Khi muốn thử sequence model mạnh hơn LSTM thường |
| `transformer` | Sequence transformer | Cao | Cao | Chậm | Trung bình | Rất tốt | Khi muốn thử kiến trúc sequence hiện đại |
| `cnn_lstm` | Hybrid CNN + LSTM | Cao | Cao | Chậm | Trung bình | Tốt | Khi nghi ngờ local motif + sequence đều quan trọng |
| `sgd` | Online / linear baseline | Thấp | Thấp | Rất nhanh | Rất tốt | Hạn chế | Khi cần baseline nhẹ và lặp nhanh |
| `stats` | Baseline thống kê | Thấp | Thấp | Rất nhanh | Rất tốt | Hạn chế | Khi cần mốc so sánh đơn giản, dễ giải thích |
| `neuralforecast` | Neural forecasting backend | Trung bình–cao | Vừa–cao | Chậm hơn | Trung bình | Tốt | Khi muốn tích hợp nhóm model kiểu forecasting |

---

## 3. So sánh theo tiêu chí thực tế

## 3.1 Độ dễ bắt đầu

| Backend | Độ dễ bắt đầu | Ghi chú |
|---|---|---|
| `mlf` | Rất dễ | Phù hợp nhất để chạy sớm và đo chất lượng thực tế |
| `sgd` | Rất dễ | Cấu hình nhẹ, dễ debug |
| `stats` | Dễ | Baseline đơn giản, dễ làm đối chứng |
| `lstm` | Trung bình | Cần hiểu sequence data và chi phí train |
| `bilstm` | Trung bình | Giống `lstm` nhưng phức tạp hơn |
| `transformer` | Khó hơn | Nhạy với cấu hình và tài nguyên |
| `cnn_lstm` | Khó hơn | Kiến trúc lai, chi phí thử nghiệm cao hơn |
| `neuralforecast` | Trung bình | Hữu ích nếu bạn muốn đi sâu hệ sinh thái forecasting |

---

## 3.2 Tốc độ train tương đối

| Backend | Tốc độ tương đối | Nhận xét |
|---|---|---|
| `stats` | Rất nhanh | Phù hợp để lấy baseline ban đầu |
| `sgd` | Rất nhanh | Tốt cho loop thử nghiệm ngắn |
| `mlf` | Nhanh | Cân bằng tốt giữa tốc độ và chất lượng |
| `lstm` | Trung bình | Chậm hơn mô hình tabular |
| `bilstm` | Trung bình–chậm | Nặng hơn `lstm` |
| `neuralforecast` | Trung bình–chậm | Phụ thuộc kiến trúc bên dưới |
| `cnn_lstm` | Chậm | Hybrid model thường tốn thời gian hơn |
| `transformer` | Chậm | Thường là backend nặng nhất trong nhóm |

---

## 3.3 Mức tiêu thụ tài nguyên

| Backend | CPU | RAM | GPU | Ghi chú |
|---|---|---|---|---|
| `stats` | Thấp | Thấp | Không cần | Nhẹ nhất |
| `sgd` | Thấp | Thấp | Không cần | Phù hợp máy yếu |
| `mlf` | Thấp–vừa | Vừa | Không bắt buộc | Thực dụng nhất cho đa số máy dev |
| `lstm` | Vừa | Vừa | Có lợi | Deep learning backend |
| `bilstm` | Vừa–cao | Vừa–cao | Có lợi | Nặng hơn `lstm` |
| `cnn_lstm` | Cao | Cao | Rất có lợi | Hybrid DL |
| `transformer` | Cao | Cao | Rất có lợi | Sequence model nặng |
| `neuralforecast` | Vừa–cao | Vừa–cao | Có lợi | Tùy model cụ thể |

---

## 4. Phân tích từng backend

## 4.1 `mlf`

### Bản chất
`mlf` là backend thực dụng nhất cho workflow hiện tại. Nó phù hợp khi dữ liệu đã được chuyển thành bảng feature rõ ràng như:

- RSI
- MACD
- ATR
- EMA
- Pivot points
- Killzone/session features
- FVG / order block features
- Label columns như `label_10`

### Ưu điểm
- Mạnh trên dữ liệu feature-based
- Train nhanh hơn deep learning
- Thường là lựa chọn mặc định hợp lý nhất
- Dễ benchmark
- Dễ dùng với Optuna / CV hơn trong thực tế
- Không đòi GPU để có kết quả tốt

### Nhược điểm
- Phụ thuộc mạnh vào chất lượng feature engineering
- Không “học sequence thô” theo kiểu DL backend
- Nếu feature không tốt, trần hiệu năng có thể bị giới hạn

### Nên dùng khi
- Bạn muốn một backend mạnh, ổn định, dễ lặp nhanh
- Bạn đang làm research có nhiều feature thủ công
- Bạn cần baseline “nghiêm túc”, không quá tốn tài nguyên

### Không phải lựa chọn đầu tiên khi
- Bạn muốn ưu tiên mô hình sequence end-to-end
- Bạn đang nghiên cứu mạnh về kiến trúc deep learning hơn là feature pipeline

---

## 4.2 `lstm`

### Bản chất
`lstm` là backend deep learning tuần tự cổ điển, phù hợp khi bạn tin rằng thứ tự thời gian và trạng thái chuỗi đóng vai trò quan trọng.

### Ưu điểm
- Mô hình hóa temporal dependencies tốt hơn baseline tuyến tính
- Dễ hiểu hơn transformer
- Là điểm bắt đầu hợp lý trong nhóm DL sequence

### Nhược điểm
- Train chậm hơn `mlf`
- Tuning khó hơn baseline tabular
- Cần chuẩn bị sequence data đúng cách
- Có thể không vượt `mlf` nếu feature engineering đã rất mạnh

### Nên dùng khi
- Bạn muốn kiểm tra giả thuyết “sequence learning có ích hơn tabular feature-based”
- Bạn có đủ tài nguyên để train nhiều vòng
- Bạn muốn một baseline DL trước khi thử mô hình nặng hơn

---

## 4.3 `bilstm`

### Bản chất
`bilstm` là biến thể bidirectional của LSTM, cho phép mô hình mạnh hơn về mặt biểu diễn chuỗi trong nhiều bài toán sequence.

### Ưu điểm
- Thường mạnh hơn `lstm` thường trong một số cấu hình
- Vẫn giữ họ recurrent nên dễ so sánh với `lstm`
- Phù hợp khi muốn thử “nâng cấp vừa phải” từ LSTM

### Nhược điểm
- Tốn tài nguyên hơn `lstm`
- Chậm hơn `lstm`
- Độ phức tạp tuning tăng
- Không phải lúc nào cũng thắng rõ rệt

### Nên dùng khi
- Bạn đã thử `lstm` và muốn một biến thể mạnh hơn
- Bạn muốn benchmark họ recurrent kỹ hơn

---

## 4.4 `transformer`

### Bản chất
`transformer` là backend sequence hiện đại hơn, phù hợp khi bạn muốn mô hình hóa quan hệ thời gian phức tạp hơn recurrent model truyền thống.

### Ưu điểm
- Kiến trúc hiện đại, linh hoạt
- Tiềm năng tốt với pattern dài và quan hệ phức tạp
- Hữu ích trong nghiên cứu sequence modeling nâng cao

### Nhược điểm
- Train nặng
- Nhạy với cấu hình
- Khó tuning hơn
- Không phải lựa chọn tối ưu nếu bạn chỉ cần kết quả nhanh và ổn định

### Nên dùng khi
- Bạn có GPU hoặc tài nguyên đủ tốt
- Bạn đang benchmark kiến trúc sequence hiện đại
- Bạn chấp nhận chi phí thử nghiệm cao để đổi lấy tiềm năng tốt hơn

### Không nên dùng đầu tiên nếu
- Bạn chưa có baseline `mlf`
- Bạn đang debug pipeline dữ liệu
- Bạn cần vòng lặp experiment rất nhanh

---

## 4.5 `cnn_lstm`

### Bản chất
`cnn_lstm` là mô hình lai giữa CNN và LSTM, thường được dùng khi muốn vừa trích xuất local temporal motifs vừa giữ khả năng học theo chuỗi.

### Ưu điểm
- Hữu ích khi dữ liệu có pattern cục bộ lặp lại
- Là lựa chọn research tốt nếu nghi ngờ local structures quan trọng
- Cho phép so sánh với recurrent thuần và transformer

### Nhược điểm
- Cấu trúc phức tạp hơn
- Train chậm hơn
- Tuning khó
- Lợi ích không phải lúc nào cũng rõ trên mọi dataset

### Nên dùng khi
- Bạn đã có baseline từ `mlf` và `lstm`
- Bạn muốn mở rộng nghiên cứu kiến trúc
- Bạn quan tâm đến pattern ngắn hạn trong chuỗi

---

## 4.6 `sgd`

### Bản chất
`sgd` là baseline nhẹ, thường đóng vai trò mô hình tuyến tính / online-friendly để kiểm tra nhanh độ học được của feature set.

### Ưu điểm
- Rất nhẹ
- Train rất nhanh
- Dễ debug
- Tốt để kiểm tra xem feature hiện tại có signal cơ bản hay không

### Nhược điểm
- Trần hiệu năng thường thấp hơn backend mạnh hơn
- Ít phù hợp cho pattern phi tuyến phức tạp
- Không nên là mô hình duy nhất để kết luận chất lượng pipeline

### Nên dùng khi
- Bạn cần baseline cực nhanh
- Bạn đang debug feature set
- Bạn muốn benchmark sơ bộ nhiều symbol / timeframe

---

## 4.7 `stats`

### Bản chất
`stats` là baseline thống kê. Vai trò chính là tạo mốc đối chứng đơn giản, rẻ, dễ diễn giải.

### Ưu điểm
- Nhanh
- Nhẹ
- Phù hợp làm baseline
- Giúp tránh việc so sánh các mô hình DL/ML mà không có mốc nền

### Nhược điểm
- Năng lực biểu diễn hạn chế
- Không kỳ vọng là backend mạnh nhất
- Giá trị lớn nhất nằm ở vai trò đối chứng

### Nên dùng khi
- Bắt đầu benchmark
- Viết báo cáo so sánh model
- Muốn có “điểm 0” trước khi thử backend nặng hơn

---

## 4.8 `neuralforecast`

### Bản chất
`neuralforecast` phù hợp khi bạn muốn khai thác nhóm mô hình neural forecasting chuyên biệt thay vì chỉ các backend sequence tự triển khai trực tiếp.

### Ưu điểm
- Hữu ích cho research theo hướng forecasting
- Mở rộng không gian thử nghiệm
- Phù hợp khi muốn tận dụng ecosystem forecasting neural

### Nhược điểm
- Thường không phải backend đơn giản nhất để bắt đầu
- Chi phí train và tuning có thể cao
- Nên dùng sau khi đã có baseline rõ ràng

### Nên dùng khi
- Bạn đang nghiên cứu forecasting-oriented models
- Bạn muốn mở rộng beyond baseline ML và recurrent models
- Bạn đã có quy trình benchmark ổn định

---

## 5. Khuyến nghị theo mục tiêu

## 5.1 Muốn kết quả tốt nhanh, ít đau đầu
Ưu tiên:

1. `mlf`
2. `sgd`
3. `stats`

Lý do:
- Dễ chạy
- Dễ benchmark
- Ít phụ thuộc GPU
- Đủ thực dụng cho đa số workflow research

---

## 5.2 Muốn benchmark bài bản
Ưu tiên:

1. `stats`
2. `sgd`
3. `mlf`
4. `lstm`
5. `bilstm`
6. `transformer`
7. `cnn_lstm`
8. `neuralforecast`

Lý do:
- Đi từ nhẹ đến nặng
- Dễ phát hiện sớm liệu dataset/feature có signal thật hay không
- Tránh đốt thời gian vào backend nặng trước khi có baseline

---

## 5.3 Muốn nghiên cứu deep learning cho chuỗi
Ưu tiên:

1. `lstm`
2. `bilstm`
3. `transformer`
4. `cnn_lstm`

Lý do:
- Tiến từ recurrent cơ bản đến kiến trúc phức tạp hơn
- Dễ hiểu đường đi nghiên cứu hơn
- Dễ phân tích xem lợi ích đến từ đâu

---

## 5.4 Máy yếu hoặc muốn loop thử nghiệm rất ngắn
Ưu tiên:

1. `stats`
2. `sgd`
3. `mlf`

Tránh bắt đầu bằng:
- `transformer`
- `cnn_lstm`

---

## 5.5 Muốn productionize sớm
Ưu tiên tương đối:

1. `mlf`
2. `sgd`
3. `lstm`

Lý do:
- Thường dễ quản trị hơn
- Chi phí inference và vận hành dễ kiểm soát hơn nhóm quá nặng
- Quy trình debug đơn giản hơn

> Lưu ý: “production-ready” thực tế còn phụ thuộc artifact format, tốc độ inference, monitoring, reproducibility, và quy trình deploy của bạn.

---

## 6. Thứ tự benchmark khuyến nghị

Một workflow benchmark hợp lý:

### Bước 1 — Baseline nhẹ
- `stats`
- `sgd`

### Bước 2 — Baseline mạnh thực dụng
- `mlf`

### Bước 3 — DL sequence cơ bản
- `lstm`
- `bilstm`

### Bước 4 — Kiến trúc nâng cao
- `transformer`
- `cnn_lstm`
- `neuralforecast`

Điều này giúp bạn:
- Tiết kiệm thời gian
- Tránh over-engineer quá sớm
- Hiểu rõ backend nào thực sự tạo giá trị tăng thêm

---

## 7. Cách ra quyết định chọn backend

Bạn có thể dùng checklist sau:

### Chọn `mlf` nếu:
- Bạn đã có feature pipeline khá tốt
- Bạn muốn baseline mạnh, thực dụng
- Bạn cần tốc độ thử nghiệm hợp lý

### Chọn `sgd` nếu:
- Bạn muốn benchmark cực nhanh
- Bạn chỉ cần kiểm tra signal cơ bản
- Máy dev hạn chế

### Chọn `stats` nếu:
- Bạn cần một baseline đối chứng rõ ràng
- Bạn muốn so sánh công bằng với các mô hình phức tạp hơn

### Chọn `lstm` / `bilstm` nếu:
- Bạn tin sequence structure quan trọng
- Bạn muốn nghiên cứu DL nhưng chưa muốn vào transformer ngay

### Chọn `transformer` nếu:
- Bạn có tài nguyên
- Bạn muốn thử mô hình hiện đại hơn
- Benchmark hiện tại cho thấy recurrent model còn giới hạn

### Chọn `cnn_lstm` nếu:
- Bạn nghi ngờ local patterns + sequence đều quan trọng
- Bạn chấp nhận tuning phức tạp hơn

### Chọn `neuralforecast` nếu:
- Bạn đang nghiêng về forecasting ecosystem
- Bạn muốn mở thêm hướng nghiên cứu ngoài pipeline hiện tại

---

## 8. Cảnh báo khi so sánh backend

Khi so sánh kết quả, đừng chỉ nhìn một metric.

Nên so sánh đồng thời:
- Chất lượng CV
- Chất lượng test
- Kết quả `evaluate`
- `Net Profit (R)`
- `Profit Factor`
- `Sharpe / Sortino / Calmar`
- Độ ổn định qua nhiều timeframe hoặc symbol

Một backend có metric train đẹp nhưng backtest xấu thì chưa chắc hữu ích.

Ngoài ra:
- Backend nặng hơn không đồng nghĩa tốt hơn
- Feature engineering mạnh có thể làm `mlf` vượt DL
- Dataset nhỏ thường không thân thiện với model quá phức tạp
- Nếu pipeline chưa ổn định, benchmark DL thường gây nhiễu kết luận

---

## 9. Ma trận quyết định ngắn

| Tình huống | Backend nên thử đầu tiên |
|---|---|
| Mới vào repo | `mlf` |
| Muốn baseline nhẹ | `stats`, `sgd` |
| Muốn baseline mạnh | `mlf` |
| Muốn so recurrent models | `lstm`, `bilstm` |
| Muốn nghiên cứu sequence hiện đại | `transformer` |
| Muốn thử hybrid sequence | `cnn_lstm` |
| Muốn theo hướng forecasting | `neuralforecast` |

---

## 10. Khuyến nghị mặc định của tài liệu này

Nếu bạn chưa có lý do kỹ thuật rõ ràng để chọn backend khác, hãy dùng trình tự sau:

1. `stats`
2. `sgd`
3. `mlf`
4. `lstm`
5. `bilstm`
6. `transformer`
7. `cnn_lstm`
8. `neuralforecast`

Với hầu hết workflow nghiên cứu trong MLFX, `mlf` là lựa chọn mặc định thực dụng nhất, còn các backend deep learning nên được xem là bước benchmark mở rộng sau khi bạn đã có baseline rõ ràng.

---

## 11. Xem thêm

- [USAGE_GUIDE.md](../guides/USAGE_GUIDE.md)
- [EVALUATION_GUIDE.md](../guides/EVALUATION_GUIDE.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [FEATURE_REFERENCE.md](../reference/FEATURE_REFERENCE.md)
- [GLOSSARY.md](../reference/GLOSSARY.md)
