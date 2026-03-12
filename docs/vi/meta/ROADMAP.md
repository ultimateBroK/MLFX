# MLFX – Lộ trình & Kế hoạch Phát triển

> **Phiên bản kế hoạch:** 2026.02.08-v2
>
> Tài liệu nội bộ.  
> Tham khảo: [TODO.md](TODO.md) (danh sách công việc chi tiết), [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) (giải thích kiến trúc hệ thống).

---

## I. BỨC TRANH THỊ TRƯỜNG & LỢI THẾ CẠNH TRANH

Vì sao MLFX đáng để tiếp tục đầu tư và mở rộng? Dự án này nằm ở giao điểm giữa công cụ nghiên cứu định lượng, quy trình học máy và tư duy MLOps cho dữ liệu thị trường.

| Tiêu chí | Script nghiên cứu rời rạc | Framework giao dịch / bot mã nguồn mở | MLFX |
| -------- | -------------------------- | ------------------------------------- | ---- |
| **Tổ chức hệ thống** | **Thấp.** Mã nguồn thường rời rạc, khó tái sử dụng. | **Trung bình đến cao.** Có cấu trúc, nhưng thường nghiêng về khâu thực thi lệnh. | **Cao.** Luồng rõ ràng từ thu thập dữ liệu → kiểm tra → xử lý → huấn luyện → đánh giá → phục vụ mô hình. |
| **Khả năng tái lập** | **Thấp.** Khó chuẩn hóa môi trường và quy trình chạy. | **Trung bình.** Có quy trình tương đối ổn định, nhưng hay phụ thuộc mạnh vào framework. | **Cao.** Dùng `pixi`, cấu hình tập trung và giao diện dòng lệnh thống nhất. |
| **Chiều sâu học máy / MLOps** | **Thấp đến trung bình.** Thường dừng ở notebook hoặc backtest đơn giản. | **Trung bình.** Mạnh ở luật giao dịch hoặc bot, nhưng không phải lúc nào cũng mạnh về pipeline học máy. | **Cao.** Tập trung vào dữ liệu, xây dựng đặc trưng, huấn luyện, so sánh mô hình, đánh giá, phát hiện độ lệch dữ liệu và phục vụ mô hình. |
| **Khả năng mở rộng bộ máy** | **Thấp.** Thêm mô hình mới thường phải sửa nhiều nơi. | **Trung bình.** Tùy thuộc vào thiết kế khung làm việc. | **Cao.** Đã có nhiều bộ máy: `mlf`, `lstm`, `bilstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`. |
| **Khả năng đánh giá** | **Trung bình.** Có thể có kiểm định nhưng thiếu chuẩn hóa. | **Cao.** Nhiều khung làm việc có kiểm định tốt. | **Cao.** Đã có đánh giá, báo cáo, so sánh đa bộ máy và ghi lại chỉ số tổng hợp. |
| **Khả năng đưa vào vận hành** | **Thấp.** Script khó triển khai ổn định. | **Trung bình.** Thường tốt ở phần thực thi nhưng không phải lúc nào cũng tốt ở phần phục vụ mô hình học máy. | **Trung bình đến cao.** Đã có `serve`, `batch-predict`, `drift`, nhưng vẫn cần tăng độ ổn định ở tầng phục vụ, cơ chế thử lại, ngắt mạch và ghi nhật ký. |
| **Phù hợp nghiên cứu dài hạn** | **Thấp.** Dễ vỡ cấu trúc khi dự án lớn lên. | **Trung bình.** Có thể bị giới hạn bởi triết lý của khung làm việc. | **Cao.** Phù hợp để nghiên cứu mô hình, so sánh bộ máy, mở rộng bộ kết nối dữ liệu và tiến tới vận hành ổn định hơn. |

**Kết luận:** MLFX không cố trở thành một bot giao dịch “làm mọi thứ” ngay từ đầu. Điểm mạnh của nó là một **quy trình nghiên cứu dữ liệu thị trường theo phong cách MLOps**, nơi bạn có thể tải dữ liệu, chuẩn hóa dữ liệu, huấn luyện nhiều bộ máy, so sánh mô hình, đánh giá và phục vụ dự đoán trong cùng một hệ thống nhất quán.

---

## II. LỘ TRÌNH PHÁT TRIỂN

**Phụ thuộc giữa các sprint:** Sprint 1 → Sprint 2 → Sprint 3 → Sprint 4 → Sprint 5.  
Không nên triển khai song song; mỗi sprint đều dựa trên đầu ra và độ ổn định của sprint trước đó.

**Vòng đời hệ thống xuyên suốt:**

```text
Thu thập dữ liệu → Kiểm tra → Biến đổi → Huấn luyện → Đánh giá → Phục vụ → Giám sát → Cải tiến
```

### SPRINT 1: NỀN TẢNG

- **Mục tiêu:** Đặt nền móng để dự án có thể chạy đầu-cuối ở mức cơ bản.
- **Phụ thuộc:** Không.
- **Thời gian ước tính:** 1–2 tuần.
- **Công nghệ chính:** Python, Pixi, Parquet, cấu trúc CLI, tài liệu cơ bản.
- **Nhiệm vụ:**
  1. Khởi tạo dự án Python với `pixi`.
  2. Thiết lập cấu trúc thư mục chính cho `mlfx`, `tests`, `data`, `outputs`, `docs`.
  3. Tạo `pyproject.toml`, `config.toml`, `.gitignore`, `README.md`.
  4. Chuẩn hóa giao diện dòng lệnh thống nhất `mlfx`.
  5. Bổ sung `Dockerfile` và `docker-compose.yml` cơ bản.
  6. Thiết lập khung tài liệu song ngữ.
- **Tiêu chí hoàn thành:** Kho mã có thể chạy quy trình cơ bản bằng CLI, cấu trúc dự án ổn định, môi trường phát triển có thể tái lập.
- **Tiêu chí chấp nhận:** Người mới có thể sao chép kho mã, cài môi trường và chạy lệnh cơ bản bằng `pixi run`.
- **Rủi ro kỹ thuật:** Nếu cấu trúc ban đầu thiếu rõ ràng, các sprint sau sẽ phát sinh liên kết chặt quá mức và nợ kỹ thuật.

### SPRINT 2: THU THẬP & XỬ LÝ DỮ LIỆU

- **Mục tiêu:** Biến dữ liệu thị trường thô thành dữ liệu chuẩn hóa có thể dùng để huấn luyện và đánh giá.
- **Phụ thuộc:** Sprint 1.
- **Thời gian ước tính:** 1–2 tuần.
- **Công nghệ chính:** `mlfx.ingestion`, `mlfx.pipeline`, Parquet, chuyển đổi khung thời gian, gắn nhãn.
- **Nhiệm vụ:**
  1. Xây dựng bộ tải dữ liệu trong `mlfx.ingestion`.
  2. Tải dữ liệu tick từ Dukascopy.
  3. Lưu dữ liệu thô theo từng tháng.
  4. Theo dõi trạng thái tải bằng tệp trạng thái.
  5. Kiểm tra chất lượng dữ liệu, phát hiện khoảng trống và bất thường.
  6. Chuyển dữ liệu tick thành OHLCV theo khung thời gian.
  7. Xây dựng đặc trưng và gắn nhãn.
  8. Chuẩn hóa dữ liệu đầu ra cho huấn luyện và đánh giá.
- **Tiêu chí hoàn thành:** Từ dữ liệu thô có thể sinh ra OHLCV, đặc trưng, nhãn và dữ liệu đã xử lý một cách nhất quán.
- **Tiêu chí chấp nhận:** Bước kiểm tra, chuyển đổi khung thời gian, xây dựng đặc trưng và gắn nhãn chạy được trong một quy trình thống nhất.
- **Rủi ro kỹ thuật:** Dữ liệu tài chính rất dễ có khoảng trống, sai lệch dấu thời gian hoặc không đồng nhất định dạng; nếu xử lý không chặt chẽ, các bước huấn luyện sẽ sai lệch theo.

### SPRINT 3: HUẤN LUYỆN & CHUẨN HÓA BỘ MÁY ✅

- **Mục tiêu:** Huấn luyện được nhiều bộ máy và chuẩn hóa quy trình huấn luyện để so sánh mô hình công bằng hơn.
- **Phụ thuộc:** Sprint 2.
- **Thời gian ước tính:** 1–2 tuần.
- **Công nghệ chính:** `mlfx.training`, MLflow tùy chọn, cấu hình huấn luyện qua CLI.
- **Nhiệm vụ:**
  1. Xây dựng mô-đun huấn luyện dùng chung.
  2. Tích hợp các bộ máy: `mlf`, `lstm`, `bilstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`.
  3. Chuẩn hóa cách chia tập huấn luyện / xác thực / kiểm tra theo chuỗi thời gian.
  4. Tránh rò rỉ dữ liệu.
  5. Lưu tệp đầu ra và chỉ số huấn luyện vào `outputs/`.
  6. Tích hợp MLflow theo chế độ tùy chọn.
  7. Chuẩn hóa siêu dữ liệu cho mỗi lần chạy.
- **Tiêu chí hoàn thành:** Có thể huấn luyện ít nhất một bộ máy từ đầu đến cuối; tệp đầu ra và chỉ số được lưu nhất quán; nhiều bộ máy có thể so sánh trong cùng hệ thống.
- **Trạng thái:** ✅ Hoàn thành.

### SPRINT 4: ĐÁNH GIÁ, BACKTEST & SO SÁNH MÔ HÌNH ✅

- **Mục tiêu:** Đánh giá chất lượng mô hình một cách tái lập được và tạo nền tảng so sánh giữa các bộ máy.
- **Phụ thuộc:** Sprint 3.
- **Thời gian ước tính:** 1–2 tuần.
- **Công nghệ chính:** `mlfx.evaluation`, báo cáo, luồng so sánh mô hình.
- **Nhiệm vụ:**
  1. Xây dựng mô-đun đánh giá.
  2. Hỗ trợ kiểm định.
  3. Tính các chỉ số đánh giá cơ bản và ngoài mẫu.
  4. Lưu kết quả đánh giá vào `outputs/`.
  5. Sinh báo cáo và chỉ số tổng hợp.
  6. Bổ sung luồng so sánh mô hình thống nhất qua `mlfx benchmark`.
  7. Bổ sung `metrics_log.jsonl`.
  8. Thêm độ phủ kiểm thử đầu-cuối cho huấn luyện và đánh giá.
- **Tiêu chí hoàn thành:** Sau khi huấn luyện có thể đánh giá và kiểm định; so sánh đa bộ máy hoạt động; kết quả được lưu và có thể đối chiếu.
- **Trạng thái:** ✅ Hoàn thành.
- **Tiêu chí chấp nhận:** Có thể dùng cùng một quy trình để so sánh nhiều bộ máy trên cùng dữ liệu và cùng bộ chỉ số.

### SPRINT 5: PHỤC VỤ MÔ HÌNH, GIÁM SÁT & TĂNG ĐỘ ỔN ĐỊNH

- **Mục tiêu:** Đưa hệ thống vào trạng thái vận hành ổn định hơn cho suy luận, dự đoán theo lô và giám sát.
- **Phụ thuộc:** Sprint 4.
- **Thời gian ước tính:** 1–2 tuần.
- **Công nghệ chính:** FastAPI, tầng phục vụ mô hình, quy trình phát hiện độ lệch dữ liệu, ghi nhật ký, cơ chế thử lại / ngắt mạch.
- **Nhiệm vụ:**
  1. Hoàn thiện tầng phục vụ cho `serve` và `batch-predict`.
  2. Chuẩn hóa hợp đồng đầu vào / đầu ra cho suy luận.
  3. Cải thiện kiểm tra sức khỏe và chẩn đoán khi chạy.
  4. Hoàn thiện quy trình `drift`.
  5. Bổ sung cơ chế thử lại cho các thao tác không ổn định.
  6. Bổ sung cơ chế ngắt mạch cho các tích hợp dễ lỗi.
  7. Cải thiện ghi nhật ký và xử lý lỗi ở thời gian chạy.
  8. Viết rõ hơn tài liệu triển khai theo kiểu gần môi trường vận hành thực tế.
- **Tiêu chí hoàn thành:** Hệ thống có thể phục vụ dự đoán qua API hoặc theo lô, có khả năng phát hiện độ lệch dữ liệu và đạt mức sẵn sàng vận hành cơ bản.
- **Tiêu chí chấp nhận:** Lỗi khi chạy được hiển thị rõ ràng, API có kiểm tra sức khỏe ổn định và người vận hành có thể làm theo tài liệu.
- **Rủi ro kỹ thuật:** Nếu tầng phục vụ mô hình không được tăng độ ổn định đúng mức, nó sẽ trở thành điểm yếu lớn nhất khi chuyển từ nghiên cứu sang vận hành.

---

## III. TRẠNG THÁI HIỆN TẠI & ƯU TIÊN TIẾP THEO

### Những gì đã có

- Giao diện dòng lệnh thống nhất `mlfx`
- Bộ tải dữ liệu trong `mlfx.ingestion`
- Kiểm tra chất lượng, chuyển đổi khung thời gian, xây dựng đặc trưng và gắn nhãn trong `mlfx.pipeline`
- Nhiều bộ máy huấn luyện trong `mlfx.training`
- Đánh giá, backtest và báo cáo trong `mlfx.evaluation`
- Đóng gói khi chạy qua `mlfx`
- Luồng so sánh mô hình thống nhất
- Độ phủ kiểm thử đầu-cuối cho huấn luyện và đánh giá
- Xuất chỉ số tổng hợp qua `metrics_log.jsonl`
- Các lệnh `serve`, `batch-predict`, `drift`

### Ưu tiên kế tiếp

1. Chuẩn hóa chỉ số giữa các backend để so sánh công bằng hơn.
2. Mở rộng độ phủ kiểm thử với bộ dữ liệu mẫu nhỏ hơn để chạy nhanh và ổn định hơn.
3. Tổ chức lại tầng phục vụ mô hình để dễ bảo trì hơn.
4. Bổ sung cơ chế thử lại và ngắt mạch.
5. Thêm bộ kết nối dữ liệu thời gian thực ngoài Dukascopy.
6. Mở rộng thêm các kiến trúc bộ máy mới, đặc biệt là nhóm dựa trên attention.

### Cách ưu tiên

- Nếu mục tiêu là **so sánh mô hình**: ưu tiên luồng so sánh, tính nhất quán của chỉ số và báo cáo.
- Nếu mục tiêu là **độ tin cậy khi vận hành**: ưu tiên kiểm thử, thử lại, ngắt mạch và ghi nhật ký.
- Nếu mục tiêu là **mở rộng nghiên cứu**: ưu tiên backend mới và bộ kết nối dữ liệu thời gian thực.
- Nếu mục tiêu là **sớm đưa vào vận hành**: ưu tiên tổ chức lại tầng phục vụ và chuẩn hóa hợp đồng suy luận.

---

## IV. THÔNG TIN BỔ SUNG

### Rủi ro kỹ thuật tổng quát

- **Dữ liệu thị trường:** Khoảng trống dữ liệu, sai lệch dấu thời gian hoặc thay đổi định dạng có thể làm hỏng pipeline nếu bước kiểm tra không chặt.
- **Bộ máy học máy / học sâu:** Một số bộ máy học sâu đòi hỏi tài nguyên lớn hoặc thời gian huấn luyện dài; cần chuẩn hóa so sánh để tránh kết luận thiếu công bằng.
- **Tầng phục vụ mô hình:** Nếu giao diện đầu vào / đầu ra không ổn định, việc tích hợp suy luận vào hệ thống bên ngoài sẽ khó bảo trì.
- **Giám sát độ lệch dữ liệu:** Nếu dữ liệu tham chiếu không được quản lý rõ ràng, cảnh báo độ lệch sẽ dễ nhiễu và khó diễn giải.
- **Phụ thuộc bên ngoài:** Nguồn dữ liệu hoặc bộ kết nối thời gian thực có thể thay đổi API, giới hạn tốc độ hoặc chính sách truy cập.

### Chi phí & thực hành tốt

- **Chi phí ban đầu:** Thấp; chủ yếu là chi phí máy tính cục bộ hoặc máy chủ nghiên cứu cơ bản.
- Dùng `pixi` để giữ môi trường có thể tái lập.
- Giữ dữ liệu thô và dữ liệu đã xử lý tách biệt rõ ràng.
- Không trộn logic nghiên cứu với logic phục vụ mô hình trong cùng một tầng.
- Ưu tiên các phép so sánh có thể lặp lại hơn là các phép thử nhanh nhưng khó kiểm chứng.
- Mỗi bộ máy mới nên đi kèm tài liệu, bộ chỉ số tối thiểu và kiểm thử phù hợp.

### Vì sao không chỉ dùng notebook hoặc script rời?

Notebook rất tốt cho việc thử nhanh, nhưng rất khó duy trì khi dự án mở rộng. MLFX cung cấp một cấu trúc nhất quán hơn để nghiên cứu lâu dài, so sánh mô hình và tiến gần hơn tới chuẩn MLOps thực tế.

### Cách nhìn hệ thống

MLFX nên được xem như một vòng lặp cải tiến liên tục:

```text
Dữ liệu mới → Kiểm tra chất lượng → Biến đổi → Huấn luyện → Đánh giá → Phục vụ → Theo dõi độ lệch → Điều chỉnh
```

---

## V. KẾ HOẠCH TƯƠNG LAI

- **Giai đoạn 1 – Mở rộng nghiên cứu mô hình:**
  - Bổ sung thêm bộ máy dựa trên attention và các biến thể mô hình chuỗi.
  - Mở rộng tự động tinh chỉnh hoặc quy trình tìm kiếm siêu tham số.
  - Chuẩn hóa sâu hơn việc so sánh giữa mô hình thống kê và mô hình học sâu.

- **Giai đoạn 2 – Mở rộng dữ liệu & vận hành:**
  - Hỗ trợ thêm các bộ kết nối dữ liệu thời gian thực ngoài Dukascopy.
  - Tăng khả năng xử lý dữ liệu khối lượng lớn.
  - Hoàn thiện hợp đồng khi chạy và tầng phục vụ theo phong cách gần môi trường vận hành thực tế.

- **Giai đoạn 3 – Quan sát hệ thống & trải nghiệm người dùng:**
  - Bổ sung bảng điều khiển trực quan cho huấn luyện, đánh giá và phục vụ mô hình.
  - Cải thiện ghi nhật ký, kiểm tra sức khỏe, chẩn đoán và khả năng quan sát độ lệch dữ liệu.
  - Cải thiện trải nghiệm sử dụng CLI và tài liệu vận hành.

---

## Tài liệu

| Tài liệu | Mô tả |
| -------- | ----- |
| [../../README.md](../../README.md) | Tổng quan hệ thống tài liệu |
| [../README.md](../README.md) | Điểm vào chính của tài liệu tiếng Việt |
| [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) | Giải thích kiến trúc hệ thống |
| [TODO.md](TODO.md) | Danh sách công việc theo sprint |
| [ROADMAP.md](ROADMAP.md) | Lộ trình & kế hoạch phát triển |
| [../en/meta/ROADMAP.md](../../en/meta/ROADMAP.md) | Phiên bản tiếng Anh |

---
