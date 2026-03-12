# MLFX – Lộ Trình & Kế Hoạch Phát Triển

> **Phiên bản kế hoạch:** 2026.02.08-v2
>
> Tài liệu nội bộ.  
> Tham khảo: [TODO.md](TODO.md) (danh sách task chi tiết), [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) (giải thích kiến trúc).

---

## I. PHÂN TÍCH THỊ TRƯỜNG & LỢI THẾ CẠNH TRANH

Tại sao MLFX đáng để tiếp tục đầu tư và mở rộng? Đây là bức tranh vị trí của dự án trong nhóm công cụ nghiên cứu giao dịch và pipeline MLOps cho dữ liệu thị trường:

| Tiêu chí | Script nghiên cứu rời rạc | Framework trading/bot mã nguồn mở | MLFX |
| -------- | -------------------------- | --------------------------------- | ---- |
| **Tổ chức hệ thống** | **Thấp.** Code thường rời rạc, khó tái sử dụng. | **Trung bình đến cao.** Có cấu trúc nhưng thường thiên về execution bot. | **Cao.** Pipeline rõ ràng từ ingestion → QA → pipeline → training → evaluation → serving. |
| **Khả năng tái lập** | **Thấp.** Khó chuẩn hóa môi trường và quy trình chạy. | **Trung bình.** Có workflow tương đối ổn định, nhưng thường gắn chặt vào framework. | **Cao.** Dùng `pixi`, cấu hình tập trung, workflow CLI thống nhất. |
| **Chiều sâu ML/MLOps** | **Thấp đến trung bình.** Thường chỉ dừng ở notebook hoặc backtest đơn giản. | **Trung bình.** Mạnh về rule-based hoặc bot execution, không phải lúc nào cũng mạnh về ML pipeline. | **Cao.** Tập trung vào dữ liệu, feature engineering, training, benchmark, evaluation, drift, serving. |
| **Khả năng mở rộng backend** | **Thấp.** Thêm model mới thường phải sửa nhiều nơi. | **Trung bình.** Phụ thuộc thiết kế framework. | **Cao.** Đã có nhiều backend: `mlf`, `lstm`, `bilstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`. |
| **Khả năng đánh giá** | **Trung bình.** Có thể có backtest nhưng thiếu chuẩn hóa. | **Cao.** Nhiều framework có backtest tốt. | **Cao.** Đã có evaluation, reporting, benchmark đa backend, log metrics tổng hợp. |
| **Khả năng production hóa** | **Thấp.** Script khó triển khai ổn định. | **Trung bình.** Thường tốt ở execution nhưng không phải lúc nào cũng tốt ở ML serving. | **Trung bình đến cao.** Đã có `serve`, `batch-predict`, `drift`, nhưng vẫn cần hardening ở serving layer, retry, circuit breaker, logging. |
| **Phù hợp nghiên cứu dài hạn** | **Thấp.** Dễ vỡ cấu trúc khi dự án lớn lên. | **Trung bình.** Có thể bị giới hạn bởi triết lý framework. | **Cao.** Phù hợp cho nghiên cứu mô hình, so sánh backend, mở rộng data adapters, và tiến tới vận hành ổn định hơn. |

**Kết luận:** MLFX không cố trở thành một bot giao dịch “all-in-one” ngay từ đầu. Điểm mạnh của nó là một **pipeline nghiên cứu dữ liệu thị trường theo phong cách MLOps**, nơi bạn có thể tải dữ liệu, chuẩn hóa dữ liệu, huấn luyện nhiều backend, benchmark, đánh giá, và phục vụ dự đoán trong cùng một hệ thống nhất quán.

---

## II. LỘ TRÌNH PHÁT TRIỂN

**Phụ thuộc giữa Sprint:** Sprint 1 → Sprint 2 → Sprint 3 → Sprint 4 → Sprint 5.  
Không nên chạy song song; mỗi sprint xây trên output và độ ổn định của sprint trước.

**Vòng đời hệ thống xuyên suốt:**

```text
Ingest → Validate → Transform → Train → Evaluate → Serve → Monitor → Improve
```

### SPRINT 1: NỀN TẢNG

- **Mục tiêu:** Thiết lập nền móng để dự án có thể chạy end-to-end ở mức cơ bản.
- **Phụ thuộc:** Không.
- **Thời gian ước tính:** 1–2 tuần.
- **Công nghệ:** Python, Pixi, Parquet, cấu trúc CLI, tài liệu cơ bản.
- **Nhiệm vụ:**
  1. Khởi tạo dự án Python với `pixi`.
  2. Thiết lập cấu trúc thư mục chính cho `mlfx`, `tests`, `data`, `outputs`, `docs`.
  3. Tạo `pyproject.toml`, `config.toml`, `.gitignore`, `README.md`.
  4. Chuẩn hóa CLI thống nhất `mlfx`.
  5. Bổ sung Dockerfile và `docker-compose.yml` cơ bản.
  6. Thiết lập khung tài liệu song ngữ.
- **DoD:** Repo có thể chạy workflow cơ bản bằng CLI, cấu trúc dự án ổn định, môi trường phát triển tái lập được.
- **Tiêu chí chấp nhận:** Người mới có thể clone repo, cài môi trường, và chạy lệnh cơ bản bằng `pixi run`.
- **Rủi ro kỹ thuật:** Nếu cấu trúc ban đầu thiếu rõ ràng, các sprint sau sẽ phát sinh coupling và nợ kỹ thuật.

### SPRINT 2: INGESTION & PIPELINE DỮ LIỆU

- **Mục tiêu:** Biến dữ liệu thị trường thô thành dữ liệu chuẩn hóa có thể dùng để huấn luyện và đánh giá.
- **Phụ thuộc:** Sprint 1.
- **Thời gian ước tính:** 1–2 tuần.
- **Công nghệ:** `mlfx.ingestion`, `mlfx.pipeline`, Parquet, resampling, labeling.
- **Nhiệm vụ:**
  1. Xây dựng downloader dữ liệu trong `mlfx.ingestion`.
  2. Tải tick data từ Dukascopy.
  3. Lưu dữ liệu raw theo partition tháng.
  4. Theo dõi trạng thái tải bằng file trạng thái.
  5. Kiểm tra chất lượng dữ liệu (QA), phát hiện gap và bất thường.
  6. Chuyển tick data sang OHLCV theo timeframe.
  7. Tạo feature engineering và labeling.
  8. Chuẩn hóa dữ liệu đầu ra cho training/evaluation.
- **DoD:** Từ raw data có thể sinh ra OHLCV, feature, label và dữ liệu processed nhất quán.
- **Tiêu chí chấp nhận:** QA, resample, feature engineering, labeling chạy được trong một workflow thống nhất.
- **Rủi ro kỹ thuật:** Dữ liệu tài chính rất dễ gặp gap, lỗi timestamp, hoặc format không đồng nhất; nếu xử lý không chặt, các bước training sẽ bị sai lệch.

### SPRINT 3: HUẤN LUYỆN & CHUẨN HÓA BACKEND ✅

- **Mục tiêu:** Huấn luyện được nhiều backend và chuẩn hóa quy trình train để so sánh mô hình công bằng hơn.
- **Phụ thuộc:** Sprint 2.
- **Thời gian ước tính:** 1–2 tuần.
- **Công nghệ:** `mlfx.training`, MLflow tùy chọn, cấu hình train theo CLI.
- **Nhiệm vụ:**
  1. Xây dựng module huấn luyện dùng chung.
  2. Tích hợp các backend: `mlf`, `lstm`, `bilstm`, `transformer`, `cnn_lstm`, `sgd`, `stats`, `neuralforecast`.
  3. Chuẩn hóa train/validation/test theo chuỗi thời gian.
  4. Tránh data leakage.
  5. Lưu artifact và metrics huấn luyện vào `outputs/`.
  6. Tích hợp MLflow theo chế độ tùy chọn.
  7. Chuẩn hóa metadata cho mỗi run.
- **DoD:** Có thể huấn luyện ít nhất một backend end-to-end; artifact và metrics được lưu nhất quán; nhiều backend có thể so sánh trong cùng hệ thống.
- **Trạng thái:** ✅ Hoàn thành.

### SPRINT 4: EVALUATION, BACKTEST & BENCHMARK ✅

- **Mục tiêu:** Đánh giá chất lượng mô hình một cách tái lập được và tạo nền tảng so sánh giữa các backend.
- **Phụ thuộc:** Sprint 3.
- **Thời gian ước tính:** 1–2 tuần.
- **Công nghệ:** `mlfx.evaluation`, reporting, benchmark flow.
- **Nhiệm vụ:**
  1. Xây dựng module evaluation.
  2. Hỗ trợ backtesting.
  3. Tính metric đánh giá cơ bản và out-of-sample.
  4. Lưu kết quả đánh giá vào `outputs/`.
  5. Sinh báo cáo và summary metrics.
  6. Bổ sung benchmark flow thống nhất qua `mlfx benchmark`.
  7. Bổ sung `metrics_log.jsonl`.
  8. Thêm end-to-end coverage cho train/evaluate.
- **DoD:** Sau khi train có thể evaluate và backtest được; benchmark đa backend hoạt động; kết quả được lưu và so sánh được.
- **Trạng thái:** ✅ Hoàn thành.
- **Tiêu chí chấp nhận:** Có thể dùng cùng một workflow để so sánh nhiều backend trên cùng dữ liệu và cùng tập metrics.

### SPRINT 5: SERVING, MONITORING & HARDENING

- **Mục tiêu:** Đưa hệ thống vào trạng thái vận hành ổn định hơn cho inference, batch prediction, và monitoring.
- **Phụ thuộc:** Sprint 4.
- **Thời gian ước tính:** 1–2 tuần.
- **Công nghệ:** FastAPI serving layer, runtime packaging, drift workflow, logging, retry/circuit breaker.
- **Nhiệm vụ:**
  1. Hoàn thiện serving layer cho `serve` và `batch-predict`.
  2. Chuẩn hóa contract input/output cho inference.
  3. Cải thiện health-check và runtime diagnostics.
  4. Hoàn thiện workflow `drift`.
  5. Thêm retry logic cho các thao tác không ổn định.
  6. Thêm circuit breaker cho tích hợp dễ lỗi.
  7. Cải thiện logging runtime và error handling.
  8. Viết rõ hơn tài liệu triển khai production-style.
- **DoD:** Hệ thống có thể phục vụ dự đoán qua API hoặc batch, có khả năng phát hiện drift, và có mức độ production-readiness cơ bản.
- **Tiêu chí chấp nhận:** Runtime failures được hiển thị rõ ràng, API có health-check ổn định, và operator có thể chạy theo tài liệu.
- **Rủi ro kỹ thuật:** Serving layer nếu không được harden sẽ trở thành điểm yếu lớn nhất khi chuyển từ nghiên cứu sang vận hành.

---

## III. TRẠNG THÁI HIỆN TẠI & ƯU TIÊN TIẾP THEO

### Những gì đã có

- CLI thống nhất `mlfx`
- Downloader dữ liệu trong `mlfx.ingestion`
- QA, resampling, feature engineering, labeling trong `mlfx.pipeline`
- Nhiều backend huấn luyện trong `mlfx.training`
- Evaluation, backtesting, reporting trong `mlfx.evaluation`
- Runtime packaging qua `mlfx`
- Workflow benchmark thống nhất
- End-to-end coverage cho train/evaluate
- Summary metrics export qua `metrics_log.jsonl`
- Workflow `serve`, `batch-predict`, `drift`

### Ưu tiên kế tiếp

1. Chuẩn hóa cross-backend metrics để so sánh công bằng hơn.
2. Mở rộng test coverage với dataset fixture nhỏ hơn để chạy nhanh và ổn định hơn.
3. Refactor serving layer để dễ bảo trì hơn.
4. Bổ sung retry logic và circuit breakers.
5. Thêm live data adapter ngoài Dukascopy.
6. Mở rộng thêm backend kiến trúc mới, đặc biệt nhóm attention-based.

### Cách ưu tiên

- Nếu mục tiêu là **so sánh mô hình**: ưu tiên benchmark, metrics consistency, và reporting.
- Nếu mục tiêu là **độ tin cậy vận hành**: ưu tiên test coverage, retry, circuit breaker, logging.
- Nếu mục tiêu là **mở rộng nghiên cứu**: ưu tiên backend mới và live data adapter.
- Nếu mục tiêu là **production readiness**: ưu tiên refactor serving layer và chuẩn hóa runtime contracts.

---

## IV. THÔNG TIN BỔ SUNG

### Rủi ro kỹ thuật (tổng quan)

- **Dữ liệu thị trường:** Gap dữ liệu, lệch timestamp, hoặc format thay đổi có thể làm hỏng pipeline nếu QA không chặt.
- **Backend ML/DL:** Một số backend deep learning có thể đòi hỏi tài nguyên lớn hoặc thời gian train dài; cần chuẩn hóa benchmark để tránh so sánh thiếu công bằng.
- **Serving layer:** Nếu interface input/output không ổn định, việc tích hợp inference vào hệ thống ngoài sẽ khó bảo trì.
- **Drift monitoring:** Nếu dữ liệu tham chiếu không được quản lý rõ, cảnh báo drift dễ trở nên nhiễu hoặc khó diễn giải.
- **Phụ thuộc bên ngoài:** Nguồn dữ liệu hoặc adapter live có thể thay đổi API, rate limits, hoặc chính sách truy cập.

### Chi phí & Best Practices

- **Chi phí ban đầu:** Thấp; trọng tâm là compute cục bộ hoặc máy chủ nghiên cứu cơ bản.
- Dùng `pixi` để giữ môi trường tái lập.
- Giữ dữ liệu raw và processed tách biệt rõ ràng.
- Không trộn logic nghiên cứu với logic serving trong cùng một tầng.
- Ưu tiên benchmark tái lập được hơn là benchmark “nhanh nhưng khó lặp lại”.
- Mỗi backend mới cần đi kèm tài liệu, metrics tối thiểu, và test phù hợp.

### Tại sao không chỉ dùng notebook hoặc script rời?

Notebook rất tốt cho thử nghiệm nhanh, nhưng khó duy trì khi dự án mở rộng. MLFX cung cấp một cấu trúc nhất quán hơn để nghiên cứu lâu dài, so sánh mô hình, và tiến gần hơn đến chuẩn MLOps thực tế.

### Hướng tư duy hệ thống

MLFX nên được xem là một vòng lặp cải tiến liên tục:

```text
Dữ liệu mới → Kiểm tra chất lượng → Biến đổi → Huấn luyện → Đánh giá → Phục vụ → Theo dõi drift → Điều chỉnh
```

---

## V. KẾ HOẠCH TƯƠNG LAI

- **Giai đoạn 1 – Mở rộng nghiên cứu mô hình:**
  - Bổ sung thêm backend attention-based và các biến thể sequence model.
  - Mở rộng auto-tuning hoặc workflow tìm kiếm siêu tham số.
  - Chuẩn hóa sâu hơn việc so sánh giữa mô hình thống kê và deep learning.

- **Giai đoạn 2 – Mở rộng dữ liệu & vận hành:**

  - Hỗ trợ thêm live data adapters ngoài Dukascopy.
  - Tăng khả năng xử lý dữ liệu khối lượng lớn.
  - Hoàn thiện runtime contracts và production-style serving.

- **Giai đoạn 3 – Quan sát & trải nghiệm người dùng:**
  - Bổ sung dashboard trực quan cho training/evaluate/serving.
  - Cải thiện logging, health checks, diagnostics, và drift observability.
  - Cải thiện UX của CLI và tài liệu vận hành.

---

## Tài liệu

| Tài liệu | Mô tả |
| -------- | ----- |
| [../../README.md](../../README.md) | Tổng quan hệ thống tài liệu |
| [../README.md](../README.md) | Điểm vào chính của tài liệu tiếng Việt |
| [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md) | Giải thích kiến trúc hệ thống |
| [TODO.md](TODO.md) | Danh sách task theo sprint |
| [ROADMAP.md](ROADMAP.md) | Lộ trình & kế hoạch phát triển |
| [../en/meta/ROADMAP.md](../../en/meta/ROADMAP.md) | Phiên bản tiếng Anh |

---
