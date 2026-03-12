# MLFX – Danh sách công việc

> **Phiên bản:** đồng bộ với [ROADMAP.md](ROADMAP.md).  
> Danh sách đầu việc theo sprint; xem [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) để hiểu kiến trúc hệ thống.

## SPRINT 1: NỀN TẢNG

> **Mục tiêu:** Thiết lập nền móng để pipeline MLFX có thể tải dữ liệu, xử lý dữ liệu và chạy end-to-end trên máy cục bộ.
>
> **Phụ thuộc:** Không.
>
> **Thời lượng ước tính:** 1–2 tuần.

### Thiết lập môi trường

- [x] Khởi tạo dự án Python với `pixi`
- [x] Thiết lập cấu trúc thư mục chính: `mlfx/`, `tests/`, `data/`, `outputs/`, `docs/`
- [x] Tạo và cấu hình `pyproject.toml`
- [x] Thiết lập `.gitignore`
- [x] Viết README gốc của dự án
- [x] Tạo cấu hình mặc định `config.toml`

### Hạ tầng phát triển

- [x] Tạo CLI thống nhất `mlfx`
- [x] Chuẩn hóa các điểm vào cho những quy trình chính
- [x] Thiết lập ghi nhật ký cơ bản cho CLI và pipeline
- [x] Tạo `Dockerfile` cơ bản
- [x] Tạo `docker-compose.yml` cho môi trường phát triển
- [x] Bổ sung cấu trúc tài liệu song ngữ trong `docs/en` và `docs/vi`

### Dữ liệu đầu vào

- [x] Xây dựng bộ tải dữ liệu trong `mlfx.ingestion`
- [x] Hỗ trợ tải dữ liệu tick từ Dukascopy
- [x] Lưu dữ liệu thô theo từng tháng vào `data/raw/`
- [x] Theo dõi trạng thái tải bằng `completed_months.json`
- [x] Hỗ trợ giải nén định dạng `bi5`

### Tiêu chí hoàn thành Sprint 1

- [x] Chạy được quy trình tải dữ liệu thô đầu tiên
- [x] CLI hoạt động cục bộ qua `pixi run`
- [x] Cấu trúc dự án sẵn sàng cho các sprint tiếp theo

---

## SPRINT 2: XỬ LÝ DỮ LIỆU & PIPELINE

> **Mục tiêu:** Biến dữ liệu thô thành dữ liệu có thể dùng để huấn luyện và đánh giá mô hình.
>
> **Phụ thuộc:** Sprint 1.
>
> **Thời lượng ước tính:** 1–2 tuần.

### Chất lượng dữ liệu

- [x] Xây dựng bước kiểm tra chất lượng dữ liệu trong `mlfx.pipeline`
- [x] Phát hiện khoảng trống dữ liệu theo thời gian
- [x] Phát hiện dữ liệu bất thường hoặc lỗi cấu trúc
- [x] Sinh báo cáo kiểm tra chất lượng cơ bản

### Chuyển đổi dữ liệu và xây dựng đặc trưng

- [x] Chuyển dữ liệu tick thành OHLCV theo khung thời gian
- [x] Hỗ trợ chuyển đổi nhiều khung thời gian
- [x] Xây dựng bước tạo đặc trưng cơ bản
- [x] Hỗ trợ gắn nhãn cho bài toán dự báo hoặc phát tín hiệu
- [x] Chuẩn hóa dữ liệu đầu ra cho bước huấn luyện và đánh giá

### Lưu trữ dữ liệu đã xử lý

- [x] Ghi dữ liệu pipeline vào `data/processed/`
- [x] Chuẩn hóa định dạng lưu trữ dạng `parquet`
- [x] Tổ chức dữ liệu theo mã, khung thời gian và tập chia

### Tiêu chí hoàn thành Sprint 2

- [x] Từ dữ liệu thô có thể sinh ra OHLCV và đặc trưng
- [x] Kiểm tra chất lượng, chuyển đổi và gắn nhãn chạy được trong một quy trình thống nhất
- [x] Dữ liệu đầu ra sẵn sàng cho bước huấn luyện mô hình

---

## SPRINT 3: HUẤN LUYỆN MÔ HÌNH

> **Mục tiêu:** Huấn luyện được các bộ máy dự báo và chuẩn hóa quy trình huấn luyện.
>
> **Phụ thuộc:** Sprint 2.
>
> **Thời lượng ước tính:** 1–2 tuần.

### Bộ máy huấn luyện

- [x] Xây dựng mô-đun `mlfx.training`
- [x] Hỗ trợ bộ máy `mlf`
- [x] Hỗ trợ bộ máy `lstm`
- [x] Hỗ trợ bộ máy `bilstm`
- [x] Hỗ trợ bộ máy `transformer`
- [x] Hỗ trợ bộ máy `cnn_lstm`
- [x] Hỗ trợ bộ máy `sgd`
- [x] Hỗ trợ bộ máy `stats`
- [x] Hỗ trợ bộ máy `neuralforecast`

### Quy trình huấn luyện

- [x] Chuẩn hóa chương trình huấn luyện dùng chung
- [x] Hỗ trợ chia tập huấn luyện, kiểm định và kiểm tra theo chuỗi thời gian
- [x] Tránh rò rỉ dữ liệu trong quá trình chia tập
- [x] Lưu tệp đầu ra của quá trình huấn luyện vào `outputs/`
- [x] Ghi các chỉ số huấn luyện

### Theo dõi thí nghiệm

- [x] Tích hợp MLflow theo chế độ tùy chọn
- [x] Lưu nhật ký chỉ số dưới dạng `metrics_log.jsonl`
- [x] Chuẩn hóa siêu dữ liệu cho mỗi lần huấn luyện

### Tiêu chí hoàn thành Sprint 3

- [x] Có thể huấn luyện ít nhất một bộ máy theo quy trình đầu-cuối
- [x] Tệp đầu ra và chỉ số được lưu nhất quán
- [x] Nhiều bộ máy có thể được so sánh trong cùng một quy trình

---

## SPRINT 4: ĐÁNH GIÁ & BACKTEST

> **Mục tiêu:** Đo được chất lượng mô hình và giá trị sử dụng của nó trong bối cảnh dự báo hoặc giao dịch.
>
> **Phụ thuộc:** Sprint 3.
>
> **Thời lượng ước tính:** 1–2 tuần.

### Đánh giá mô hình

- [x] Xây dựng mô-đun `mlfx.evaluation`
- [x] Tính các chỉ số đánh giá cơ bản
- [x] Hỗ trợ đánh giá trên tập dữ liệu ngoài mẫu
- [x] Xuất báo cáo đánh giá

### Backtest

- [x] Tạo quy trình kiểm định dựa trên tín hiệu dự báo
- [x] Tính các chỉ số hiệu suất cơ bản
- [x] Lưu kết quả backtest vào `outputs/`
- [x] Tạo báo cáo tóm tắt cho từng lần đánh giá

### So sánh nhiều bộ máy

- [x] Bổ sung lệnh `mlfx benchmark`
- [x] So sánh nhiều bộ máy trong cùng một quy trình
- [x] Chuẩn hóa đầu ra so sánh chuẩn để dễ đối chiếu

### Tiêu chí hoàn thành Sprint 4

- [x] Có thể đánh giá và kiểm định mô hình sau khi huấn luyện
- [x] So sánh nhiều bộ máy hoạt động ổn định
- [x] Báo cáo giúp so sánh chất lượng bộ máy một cách rõ ràng

---

## SPRINT 5: PHỤC VỤ MÔ HÌNH & VẬN HÀNH

> **Mục tiêu:** Đưa mô hình vào trạng thái có thể phục vụ dự đoán và vận hành như một hệ thống nghiên cứu MLOps hoàn chỉnh.
>
> **Phụ thuộc:** Sprint 4.
>
> **Thời lượng ước tính:** 1–2 tuần.

### Phục vụ mô hình

- [x] Đóng gói lớp chạy thời gian thực thông qua `mlfx`
- [x] Hỗ trợ lệnh `serve`
- [x] Hỗ trợ lệnh `batch-predict`
- [x] Xây dựng lớp phục vụ mô hình bằng FastAPI ở mức cơ bản
- [x] Bổ sung điểm kiểm tra sức khỏe cơ bản

### Giám sát

- [x] Hỗ trợ quy trình `drift`
- [x] So sánh phân phối dữ liệu gần đây với dữ liệu tham chiếu
- [x] Sinh đầu ra phục vụ kiểm tra độ lệch mô hình

### Độ tin cậy khi vận hành

- [ ] Bổ sung cơ chế thử lại cho lớp phục vụ mô hình
- [ ] Bổ sung bộ ngắt mạch cho các tích hợp dễ lỗi
- [ ] Chuẩn hóa xử lý lỗi trong toàn bộ CLI và API
- [ ] Tăng mức độ chi tiết của ghi nhật ký thời gian chạy
- [ ] Bổ sung cấu hình triển khai rõ ràng hơn cho môi trường thực tế

### Tiêu chí hoàn thành Sprint 5

- [x] Có thể phục vụ dự đoán qua API hoặc theo lô
- [x] Có quy trình phát hiện độ lệch dữ liệu
- [ ] Hệ thống đạt mức sẵn sàng vận hành cơ bản

---

## CÔNG VIỆC TIẾP THEO ĐƯỢC KHUYẾN NGHỊ

> Phần này được đồng bộ với [ROADMAP.md](ROADMAP.md) và phản ánh các bước tiếp theo hợp lý nhất trong trạng thái hiện tại của dự án.

### Ưu tiên cao

- [x] Mở `bilstm` ra CLI thông qua `--backend bilstm`
- [x] Bổ sung quy trình benchmark thống nhất (`mlfx benchmark`)
- [x] Thêm độ bao phủ end-to-end cho huấn luyện và đánh giá (`test_training_e2e.py`)
- [x] Bổ sung xuất chỉ số tổng hợp (`metrics_log.jsonl`)

### Ưu tiên tiếp theo

- [ ] Chuẩn hóa các chỉ số giữa nhiều bộ máy để so sánh công bằng hơn
- [ ] Mở rộng độ bao phủ kiểm thử với bộ dữ liệu mẫu nhỏ hơn để chạy nhanh và ổn định hơn
- [ ] Tách lớp phục vụ mô hình cho dễ bảo trì hơn
- [ ] Bổ sung cơ chế thử lại và bộ ngắt mạch để tăng mức sẵn sàng vận hành
- [ ] Thêm bộ kết nối dữ liệu thời gian thực ngoài Dukascopy
- [ ] Mở rộng thêm các kiến trúc bộ máy mới, đặc biệt là nhóm dựa trên attention

---

## CẢI TIẾN CHUNG

### Tầng dịch vụ và kiến trúc nội bộ

- [ ] Tách rõ tầng dịch vụ cho các phần: thu thập dữ liệu / pipeline / huấn luyện / đánh giá / phục vụ mô hình
- [ ] Giảm mức độ phụ thuộc chặt giữa CLI và logic nghiệp vụ
- [ ] Chuẩn hóa giao diện giữa các bộ máy
- [ ] Cải thiện khả năng thay thế bộ máy mà không phải sửa nhiều mã điều phối

### Ghi nhật ký và khả năng quan sát

- [ ] Chuẩn hóa ghi nhật ký theo các cấp `DEBUG`, `INFO`, `WARNING`, `ERROR`
- [ ] Ghi nhật ký ra tệp riêng cho từng quy trình
- [ ] Bổ sung bản tóm tắt thực thi cho mỗi lần chạy
- [ ] Hoàn thiện kiểm tra sức khỏe cho lớp chạy thời gian thực và lớp phục vụ mô hình

### Kiểm thử

- [ ] Mở rộng kiểm thử đơn vị cho phần thu thập dữ liệu
- [ ] Mở rộng kiểm thử đơn vị cho phần pipeline
- [ ] Mở rộng kiểm thử đơn vị cho phần đánh giá
- [ ] Bổ sung kiểm thử API cho lớp phục vụ mô hình
- [ ] Thêm báo cáo độ bao phủ kiểm thử
- [ ] Giảm thời gian chạy toàn bộ bộ kiểm thử

### DevOps & triển khai

- [ ] Hoàn thiện việc đóng gói container cho toàn hệ thống
- [ ] Tạo hướng dẫn triển khai rõ ràng cho môi trường thực tế
- [ ] Bổ sung quy trình CI/CD trên GitHub Actions
- [ ] Kiểm tra quy trình tự động cho build, test và lint
- [ ] Chuẩn hóa cấu hình môi trường phát triển / kiểm thử / vận hành

### Tài liệu

- [ ] Đồng bộ `TODO.md` tiếng Anh với bản tiếng Việt
- [ ] Tiếp tục hoàn thiện tài liệu song ngữ đối xứng
- [ ] Bổ sung breadcrumb và liên kết chéo thống nhất giữa các file tài liệu
- [ ] Cập nhật tài liệu khi thêm bộ máy hoặc quy trình mới
- [ ] Viết thêm hướng dẫn cho người đóng góp

---

## DỰ TÍNH TƯƠNG LAI

> Những hạng mục dưới đây nằm ngoài phạm vi công việc ngắn hạn, nhưng hữu ích cho định hướng dài hạn của MLFX.

### Dữ liệu và pipeline

- [ ] Hỗ trợ thêm nhiều nguồn dữ liệu thị trường
- [ ] Thêm pipeline phát trực tuyến gần thời gian thực
- [ ] Tăng khả năng xử lý dữ liệu khối lượng lớn
- [ ] Tối ưu bước tạo đặc trưng theo lô lớn

### Mô hình

- [ ] Thử nghiệm thêm các kiến trúc attention-based
- [ ] Thêm cơ chế tự động chọn mô hình
- [ ] Bổ sung tinh chỉnh siêu tham số tự động
- [ ] So sánh sâu hơn giữa mô hình thống kê và học sâu

### Phục vụ mô hình và giám sát

- [ ] Tăng cường khả năng mở rộng của lớp phục vụ mô hình
- [ ] Bổ sung xác thực cho API
- [ ] Thêm bảng điều khiển giám sát
- [ ] Theo dõi độ lệch mô hình và độ lệch dữ liệu với cảnh báo tốt hơn

### Trải nghiệm người dùng

- [ ] Xây dựng bảng điều khiển trực quan cho huấn luyện / đánh giá / phục vụ mô hình
- [ ] Cải thiện trải nghiệm sử dụng CLI
- [ ] Xuất báo cáo trực quan, dễ đọc hơn
- [ ] Tăng khả năng cấu hình mà không cần sửa mã nguồn

---

## Tài liệu liên quan

| Tài liệu | Mô tả |
| -------- | ----- |
| [../../README.md](../../README.md) | Tổng quan về hệ thống tài liệu |
| [../README.md](../README.md) | Điểm vào chính của tài liệu tiếng Việt |
| [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) | Giải thích kiến trúc hệ thống |
| [ROADMAP.md](ROADMAP.md) | Trạng thái hiện tại và bước tiếp theo |

---
