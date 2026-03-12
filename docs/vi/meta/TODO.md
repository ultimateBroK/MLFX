# MLFX – Danh sách công việc

> **Phiên bản:** đồng bộ với [ROADMAP.md](ROADMAP.md).  
> Danh sách task theo sprint; xem [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) để hiểu kiến trúc.

## SPRINT 1: NỀN TẢNG

> **Mục tiêu:** Thiết lập nền móng để pipeline MLFX có thể tải dữ liệu, xử lý dữ liệu, và chạy end-to-end cục bộ.
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
- [x] Chuẩn hóa entrypoints cho các workflow chính
- [x] Thiết lập logging cơ bản cho CLI và pipeline
- [x] Tạo file Docker cơ bản (`Dockerfile`)
- [x] Tạo `docker-compose.yml` cho môi trường phát triển
- [x] Bổ sung cấu trúc tài liệu song ngữ trong `docs/en` và `docs/vi`

### Dữ liệu đầu vào

- [x] Xây dựng downloader trong `mlfx.ingestion`
- [x] Hỗ trợ tải tick data từ Dukascopy
- [x] Lưu dữ liệu raw theo partition tháng vào `data/raw/`
- [x] Theo dõi trạng thái tải bằng `completed_months.json`
- [x] Hỗ trợ giải nén định dạng `bi5`

### DoD Sprint 1

- [x] Chạy được luồng tải dữ liệu raw đầu tiên
- [x] CLI hoạt động cục bộ qua `pixi run`
- [x] Cấu trúc dự án sẵn sàng cho các sprint tiếp theo

---

## SPRINT 2: XỬ LÝ DỮ LIỆU & PIPELINE

> **Mục tiêu:** Biến dữ liệu raw thành dữ liệu có thể dùng để huấn luyện và đánh giá mô hình.
>
> **Phụ thuộc:** Sprint 1.
>
> **Thời lượng ước tính:** 1–2 tuần.

### Chất lượng dữ liệu

- [x] Xây dựng bước kiểm tra chất lượng dữ liệu trong `mlfx.pipeline`
- [x] Phát hiện gap dữ liệu theo thời gian
- [x] Phát hiện dữ liệu bất thường / lỗi cấu trúc
- [x] Sinh báo cáo QA cơ bản

### Resampling và feature engineering

- [x] Chuyển đổi tick data sang OHLCV theo timeframe
- [x] Hỗ trợ resample nhiều timeframe
- [x] Xây dựng feature engineering cơ bản
- [x] Hỗ trợ labeling cho bài toán dự báo / tín hiệu
- [x] Chuẩn hóa dữ liệu đầu ra cho train/evaluate

### Lưu trữ dữ liệu xử lý

- [x] Ghi dữ liệu pipeline vào `data/processed/`
- [x] Chuẩn hóa định dạng lưu trữ dạng `parquet`
- [x] Tổ chức dữ liệu theo symbol / timeframe / split

### DoD Sprint 2

- [x] Từ dữ liệu raw có thể sinh OHLCV và feature
- [x] QA, resample, và labeling chạy được trong một workflow thống nhất
- [x] Dữ liệu đầu ra sẵn sàng cho huấn luyện mô hình

---

## SPRINT 3: HUẤN LUYỆN MÔ HÌNH

> **Mục tiêu:** Huấn luyện được các backend dự báo và chuẩn hóa quy trình train.
>
> **Phụ thuộc:** Sprint 2.
>
> **Thời lượng ước tính:** 1–2 tuần.

### Backend huấn luyện

- [x] Xây dựng module `mlfx.training`
- [x] Hỗ trợ backend `mlf`
- [x] Hỗ trợ backend `lstm`
- [x] Hỗ trợ backend `bilstm`
- [x] Hỗ trợ backend `transformer`
- [x] Hỗ trợ backend `cnn_lstm`
- [x] Hỗ trợ backend `sgd`
- [x] Hỗ trợ backend `stats`
- [x] Hỗ trợ backend `neuralforecast`

### Quy trình huấn luyện

- [x] Chuẩn hóa train script dùng chung
- [x] Hỗ trợ chia tập train/validation/test theo chuỗi thời gian
- [x] Tránh data leakage trong quá trình split
- [x] Lưu artifact huấn luyện vào `outputs/`
- [x] Ghi metrics huấn luyện

### Theo dõi thí nghiệm

- [x] Tích hợp MLflow tùy chọn cho tracking
- [x] Lưu log metrics dạng `metrics_log.jsonl`
- [x] Chuẩn hóa metadata cho lần chạy huấn luyện

### DoD Sprint 3

- [x] Có thể train ít nhất một backend end-to-end
- [x] Artifact và metrics được lưu nhất quán
- [x] Nhiều backend có thể so sánh được trên cùng workflow

---

## SPRINT 4: ĐÁNH GIÁ & BACKTEST

> **Mục tiêu:** Đo được chất lượng mô hình và giá trị sử dụng trong bối cảnh giao dịch / dự báo.
>
> **Phụ thuộc:** Sprint 3.
>
> **Thời lượng ước tính:** 1–2 tuần.

### Đánh giá mô hình

- [x] Xây dựng module `mlfx.evaluation`
- [x] Tính các metric đánh giá cơ bản
- [x] Hỗ trợ đánh giá out-of-sample
- [x] Xuất báo cáo đánh giá

### Backtesting

- [x] Tạo luồng backtest dựa trên tín hiệu dự báo
- [x] Tính các chỉ số hiệu suất cơ bản
- [x] Lưu kết quả backtest vào `outputs/`
- [x] Tạo báo cáo tóm tắt cho từng lần evaluate

### Benchmark

- [x] Bổ sung lệnh `mlfx benchmark`
- [x] So sánh nhiều backend trong cùng một quy trình
- [x] Chuẩn hóa đầu ra benchmark để dễ đối chiếu

### DoD Sprint 4

- [x] Có thể đánh giá và backtest mô hình sau khi train
- [x] Benchmark đa backend hoạt động
- [x] Báo cáo giúp so sánh chất lượng backend rõ ràng

---

## SPRINT 5: SERVING & VẬN HÀNH

> **Mục tiêu:** Đưa mô hình vào trạng thái có thể phục vụ dự đoán và vận hành như một hệ thống nghiên cứu MLOps hoàn chỉnh.
>
> **Phụ thuộc:** Sprint 4.
>
> **Thời lượng ước tính:** 1–2 tuần.

### Serving

- [x] Đóng gói runtime thông qua `mlfx`
- [x] Hỗ trợ `serve`
- [x] Hỗ trợ `batch-predict`
- [x] Xây dựng FastAPI serving layer cơ bản
- [x] Bổ sung endpoint health cơ bản

### Giám sát

- [x] Hỗ trợ workflow `drift`
- [x] So sánh phân phối dữ liệu gần đây với dữ liệu tham chiếu
- [x] Sinh đầu ra phục vụ kiểm tra model drift

### Độ tin cậy vận hành

- [ ] Bổ sung retry logic cho serving layer
- [ ] Bổ sung circuit breaker cho tích hợp bên ngoài
- [ ] Chuẩn hóa error handling ở toàn bộ CLI và API
- [ ] Tăng độ chi tiết của logging runtime
- [ ] Bổ sung cấu hình triển khai production rõ ràng hơn

### DoD Sprint 5

- [x] Có thể phục vụ dự đoán qua API hoặc batch
- [x] Có workflow phát hiện drift
- [ ] Hệ thống đạt mức production-ready cơ bản

---

## CÔNG VIỆC TIẾP THEO ĐƯỢC KHUYẾN NGHỊ

> Phần này được đồng bộ với [ROADMAP.md](ROADMAP.md) và phản ánh các bước tiếp theo hợp lý nhất trong trạng thái hiện tại của dự án.

### Ưu tiên cao

- [x] Expose `bilstm` qua CLI bằng `--backend bilstm`
- [x] Bổ sung unified benchmark flow (`mlfx benchmark`)
- [x] Thêm end-to-end train/evaluate coverage (`test_training_e2e.py`)
- [x] Bổ sung export metrics tổng hợp (`metrics_log.jsonl`)

### Ưu tiên tiếp theo

- [ ] Chuẩn hóa cross-backend metrics để so sánh công bằng hơn
- [ ] Mở rộng test coverage với dataset fixture nhỏ hơn để chạy nhanh và ổn định hơn
- [ ] Refactor serving layer để dễ bảo trì hơn
- [ ] Bổ sung retry logic và circuit breakers cho production readiness
- [ ] Thêm live data adapter ngoài Dukascopy
- [ ] Mở rộng thêm backend kiến trúc mới, đặc biệt nhóm attention-based

---

## CẢI TIẾN CHUNG

### Service layer và kiến trúc nội bộ

- [ ] Tách rõ service layer cho ingestion / pipeline / training / evaluation / serving
- [ ] Giảm coupling giữa CLI và logic nghiệp vụ
- [ ] Chuẩn hóa interface giữa các backend
- [ ] Cải thiện khả năng thay thế backend mà không sửa nhiều code điều phối

### Logging và observability

- [ ] Chuẩn hóa logging theo cấp độ `DEBUG`, `INFO`, `WARNING`, `ERROR`
- [ ] Ghi log ra file riêng cho từng workflow
- [ ] Bổ sung execution summary cho mỗi lần chạy
- [ ] Hoàn thiện health checks cho runtime và serving

### Kiểm thử

- [ ] Mở rộng unit tests cho ingestion
- [ ] Mở rộng unit tests cho pipeline
- [ ] Mở rộng unit tests cho evaluation
- [ ] Bổ sung API tests cho serving layer
- [ ] Thêm báo cáo coverage
- [ ] Giảm thời gian chạy test suite tổng thể

### DevOps & triển khai

- [ ] Hoàn thiện containerization cho toàn hệ thống
- [ ] Tạo hướng dẫn triển khai production rõ ràng
- [ ] Bổ sung CI/CD pipeline trên GitHub Actions
- [ ] Kiểm tra quy trình build, test, lint tự động
- [ ] Chuẩn hóa cấu hình môi trường dev / staging / prod

### Tài liệu

- [ ] Đồng bộ `TODO.md` tiếng Anh với bản tiếng Việt
- [ ] Tiếp tục hoàn thiện tài liệu song ngữ đối xứng
- [ ] Bổ sung breadcrumb / cross-link đồng nhất giữa các file docs
- [ ] Cập nhật tài liệu khi thêm backend hoặc workflow mới
- [ ] Viết thêm guideline cho contributors

---

## DỰ TÍNH TƯƠNG LAI

> Những hạng mục dưới đây nằm ngoài phạm vi “next work” ngắn hạn nhưng hữu ích cho định hướng dài hạn của MLFX.

### Dữ liệu và pipeline

- [ ] Hỗ trợ thêm nhiều nguồn dữ liệu thị trường
- [ ] Thêm pipeline streaming gần thời gian thực
- [ ] Tăng khả năng xử lý dữ liệu khối lượng lớn
- [ ] Tối ưu feature generation theo batch lớn

### Mô hình

- [ ] Thử nghiệm thêm các kiến trúc attention-based
- [ ] Thêm cơ chế auto model selection
- [ ] Bổ sung tuning tự động cho hyperparameters
- [ ] So sánh sâu hơn giữa mô hình thống kê và deep learning

### Serving và monitoring

- [ ] Tăng cường khả năng mở rộng của serving layer
- [ ] Bổ sung authentication cho API
- [ ] Thêm monitoring dashboard
- [ ] Theo dõi model drift và data drift với cảnh báo tốt hơn

### Trải nghiệm người dùng

- [ ] Xây dựng dashboard trực quan cho training / evaluate / serving
- [ ] Cải thiện UX của CLI
- [ ] Xuất báo cáo trực quan dễ đọc hơn
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
