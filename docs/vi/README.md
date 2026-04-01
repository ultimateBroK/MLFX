# MLFX Tài liệu tiếng Việt

Chào mừng bạn đến với hệ thống tài liệu của MLFX.

`MLFX` là một quy trình nghiên cứu dữ liệu thị trường theo phong cách MLOps. Dự án bao phủ toàn bộ luồng làm việc từ tải dữ liệu tick thô, tạo OHLCV, xây dựng đặc trưng, huấn luyện mô hình, đánh giá, cho đến phục vụ mô hình và giám sát.

Trang này là **điểm vào chính** cho toàn bộ tài liệu tiếng Việt.

---

## Cấu trúc tài liệu

Tài liệu tiếng Việt được tổ chức theo mục đích sử dụng:

- **Bắt đầu** — dành cho người mới, thiết lập ban đầu, và lối đi nhanh nhất để chạy được quy trình chuẩn
- **Guides** — hướng dẫn vận hành CLI, đánh giá kết quả, và xử lý sự cố
- **Tra cứu** — tài liệu tra cứu về đặc trưng, cấu hình, API và thuật ngữ
- **Kiến trúc** — mô tả thiết kế hệ thống, luồng dữ liệu và các bộ máy huấn luyện
- **Định hướng** — lộ trình và tài liệu định hướng bảo trì tài liệu

```text
docs/vi/
├── README.md
├── getting-started/
│   ├── QUICKSTART.md
│   └── NOOB_GUIDE.md
├── guides/
│   ├── USAGE_GUIDE.md
│   ├── EVALUATION_GUIDE.md
│   └── TROUBLESHOOTING.md
├── reference/
│   ├── FEATURE_REFERENCE.md
│   ├── CONFIG_REFERENCE.md
│   ├── API_REFERENCE.md
│   └── GLOSSARY.md
├── architecture/
│   ├── ARCHITECTURE.md
│   └── BACKEND_COMPARISON.md
└── meta/
    └── ROADMAP.md
```

---

## Bắt đầu từ đâu

### Nếu bạn mới vào kho mã
- [Bắt đầu nhanh](getting-started/QUICKSTART.md) — lối đi ngắn nhất để chạy quy trình chuẩn
- [Hướng dẫn cho người mới](getting-started/NOOB_GUIDE.md) — giải thích dự án làm gì và vì sao thứ tự các bước lại quan trọng

### Nếu bạn muốn vận hành CLI
- [Hướng dẫn cấu hình và sử dụng](guides/USAGE_GUIDE.md) — cách chạy lệnh theo từng bước
- [Hướng dẫn đánh giá](guides/EVALUATION_GUIDE.md) — cách chạy đánh giá và đọc báo cáo
- [Khắc phục sự cố](guides/TROUBLESHOOTING.md) — lỗi môi trường, dữ liệu, và runtime thường gặp

### Nếu bạn cần tài liệu tra cứu kỹ thuật
- [Tham chiếu đặc trưng](reference/FEATURE_REFERENCE.md) — ý nghĩa các cột và đặc trưng được tạo ra
- [Tham chiếu cấu hình](reference/CONFIG_REFERENCE.md) — khóa trong `config.toml` và mapping với CLI
- [Tham chiếu API](reference/API_REFERENCE.md) — điểm cuối FastAPI của lớp phục vụ mô hình
- [Thuật ngữ](reference/GLOSSARY.md) — các thuật ngữ thường gặp trong dự án và giao dịch

### Nếu bạn muốn hiểu thiết kế hệ thống
- [Kiến trúc hệ thống](architecture/ARCHITECTURE.md) — luồng dữ liệu, ranh giới mô-đun và cấu trúc huấn luyện/đánh giá/phục vụ
- [So sánh bộ máy](architecture/BACKEND_COMPARISON.md) — đánh đổi giữa các bộ máy và cách chọn bộ máy phù hợp

### Nếu bạn muốn xem định hướng / kế hoạch
- [Lộ trình tài liệu](meta/ROADMAP.md)

---

## Lộ trình đọc được khuyến nghị

### Lộ trình 1 — Thiết lập lần đầu
1. [Bắt đầu nhanh](getting-started/QUICKSTART.md)
2. [Hướng dẫn cho người mới](getting-started/NOOB_GUIDE.md)
3. [Hướng dẫn cấu hình và sử dụng](guides/USAGE_GUIDE.md)

### Lộ trình 2 — Huấn luyện và đánh giá mô hình
1. [Hướng dẫn cấu hình và sử dụng](guides/USAGE_GUIDE.md)
2. [Tham chiếu đặc trưng](reference/FEATURE_REFERENCE.md)
3. [Hướng dẫn đánh giá](guides/EVALUATION_GUIDE.md)

### Lộ trình 3 — Hiểu nội bộ của hệ thống
1. [Kiến trúc hệ thống](architecture/ARCHITECTURE.md)
2. [Tham chiếu cấu hình](reference/CONFIG_REFERENCE.md)
3. [Tham chiếu API](reference/API_REFERENCE.md)
4. [So sánh bộ máy](architecture/BACKEND_COMPARISON.md)

---

## Luồng vận hành chuẩn

Luồng vận hành thông thường của MLFX là:

```text
download
  -> qa
  -> pipeline
  -> train
  -> evaluate
  -> serve / batch-predict
  -> drift
```

Ý nghĩa từng bước:

- `download` — tải dữ liệu tick thô
- `qa` — kiểm tra dữ liệu thô để phát hiện khoảng trống và bất thường
- `pipeline` — tạo OHLCV, đặc trưng và nhãn
- `train` — huấn luyện bộ máy đã chọn và đăng ký tệp đầu ra
- `evaluate` — backtest tín hiệu và sinh báo cáo
- `benchmark` — so sánh nhiều bộ máy
- `serve` — khởi động API suy luận
- `batch-predict` — chạy dự đoán ngoại tuyến và xuất tệp
- `drift` — so sánh phân phối mới với dữ liệu tham chiếu
- `drift-retrain` — phát hiện độ lệch với tự động huấn luyện lại
- `profiles` — liệt kê các hồ sơ quy trình
- `run-profile` — train + evaluate từ hồ sơ
- `run-all` — chạy toàn bộ pipeline trong một lệnh
- `mlflow` — quản lý máy chủ theo dõi MLflow và di chuyển artifact

Để xem lệnh chạy thực tế, hãy đọc:
- [Bắt đầu nhanh](getting-started/QUICKSTART.md)
- [Hướng dẫn cấu hình và sử dụng](guides/USAGE_GUIDE.md)

---

## Ghi chú về môi trường

- Kho mã được vận hành theo hướng **ưu tiên Pixi**
- Các lệnh hằng ngày nên chạy qua `pixi run`
- Python và phụ thuộc được quản lý thông qua cấu hình của project
- Quy trình chuẩn không yêu cầu tự dựng `uv` hoặc `venv` riêng

Thiết lập môi trường cơ bản:

```bash
pixi install
```

Điểm vào thường dùng:

- `pixi run mlfx`
- `pixi run test`
- `pixi run verify`
- `pixi run clean-generated`

---

## Tài liệu liên quan

- Chỉ mục docs tổng: [../README.md](../README.md)
- Tài liệu tiếng Anh: [../en/README.md](../en/README.md)

---

## Quy ước của cây tài liệu này

- Các file `README.md` đóng vai trò **trung tâm điều hướng**, không phải cẩm nang đầy đủ
- `QUICKSTART.md` là tài liệu **bắt đầu nhanh chuẩn**
- `NOOB_GUIDE.md` tập trung vào **giải thích quy trình và tư duy nhập môn**
- `USAGE_GUIDE.md` tập trung vào **cách dùng lệnh và tệp đầu ra**
- Nhóm `REFERENCE` là nguồn tra cứu chuẩn cho field, config key, và API
- Nhóm `ARCHITECTURE` mô tả thiết kế nội bộ, không thay thế tài liệu vận hành hằng ngày

---

## Xem thêm

- [Bắt đầu nhanh](getting-started/QUICKSTART.md)
- [Hướng dẫn cấu hình và sử dụng](guides/USAGE_GUIDE.md)
- [Kiến trúc hệ thống](architecture/ARCHITECTURE.md)
- [Khắc phục sự cố](guides/TROUBLESHOOTING.md)
