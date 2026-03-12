# MLFX

> Pipeline MLOps theo hướng local-first, Pixi-first dành cho nghiên cứu dữ liệu thị trường, xây dựng đặc trưng, dự báo, đánh giá và phục vụ mô hình.

[![Python](https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=white)](README.md#quickstart)
[![Pixi](https://img.shields.io/badge/workflow-pixi-7A4DFF)](README.md#quickstart)
[![Platform](https://img.shields.io/badge/platform-linux--64-1793D1?logo=linux&logoColor=white)](README.md#quickstart)
[![Docs](https://img.shields.io/badge/docs-song_ngữ-brightgreen)](docs/README.md)
[![FastAPI](https://img.shields.io/badge/api-FastAPI-009688?logo=fastapi&logoColor=white)](README.md#highlights)
[![Polars](https://img.shields.io/badge/data-Polars-CD792C?logo=polars&logoColor=white)](README.md#highlights)
[![PyTorch](https://img.shields.io/badge/dl-PyTorch-EE4C2C?logo=pytorch&logoColor=white)](README.md#available-backends)
[![LightGBM](https://img.shields.io/badge/gbm-LightGBM-02569B)](README.md#available-backends)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

MLFX là một framework mã nguồn mở, vận hành cục bộ, giúp bạn xây dựng pipeline học máy cho dữ liệu thị trường theo cách dễ chạy, dễ gỡ lỗi, dễ so sánh và dễ mở rộng.

Thiết lập một lần, thử nghiệm nhiều lần:

- 📥 Thu thập dữ liệu tick lịch sử
- 🧪 Kiểm tra chất lượng và chuyển đổi sang OHLCV
- 🧩 Tạo đặc trưng và nhãn
- 🤖 Huấn luyện nhiều backend dự báo khác nhau
- 📊 So sánh và đánh giá kết quả
- 🚀 Triển khai suy luận và theo dõi độ lệch dữ liệu

Nếu bạn cần một bộ khung nghiên cứu gọn gàng, có cấu trúc rõ ràng, thay vì một mớ notebook rời rạc hoặc một nền tảng đám mây khó kiểm soát, MLFX được tạo ra cho đúng mục đích đó.

> ⭐ Nếu MLFX hữu ích với bạn, hãy tặng repo một ngôi sao để nhiều người khác biết đến dự án hơn.

## Mục lục

- [MLFX](#mlfx)
  - [Mục lục](#mục-lục)
  - [Vì sao nên dùng MLFX?](#vì-sao-nên-dùng-mlfx)
  - [Bạn có thể làm gì với MLFX](#bạn-có-thể-làm-gì-với-mlfx)
  - [Các tình huống sử dụng phù hợp](#các-tình-huống-sử-dụng-phù-hợp)
  - [Luồng làm việc cốt lõi](#luồng-làm-việc-cốt-lõi)
    - [Ý nghĩa từng bước](#ý-nghĩa-từng-bước)
  - [Điểm nổi bật](#điểm-nổi-bật)
  - [Các backend hiện có](#các-backend-hiện-có)
  - [Bắt đầu nhanh](#bắt-đầu-nhanh)
    - [Yêu cầu](#yêu-cầu)
    - [Cài môi trường](#cài-môi-trường)
    - [Chạy một luồng end-to-end tối thiểu](#chạy-một-luồng-end-to-end-tối-thiểu)
  - [Các lệnh thường dùng](#các-lệnh-thường-dùng)
    - [Giải thích nhanh](#giải-thích-nhanh)
  - [Cấu trúc dự án](#cấu-trúc-dự-án)
  - [Các đầu ra được tạo ra](#các-đầu-ra-được-tạo-ra)
  - [Tài liệu](#tài-liệu)
    - [Bắt đầu từ đây](#bắt-đầu-từ-đây)
    - [Lộ trình đọc khuyến nghị](#lộ-trình-đọc-khuyến-nghị)
  - [MLFX phù hợp với ai?](#mlfx-phù-hợp-với-ai)
  - [Định hướng hiện tại](#định-hướng-hiện-tại)
  - [Đóng góp](#đóng-góp)
  - [Tác giả](#tác-giả)
  - [Giấy phép](#giấy-phép)

---

## Vì sao nên dùng MLFX?

Phần lớn dự án trong lĩnh vực này thường buộc bạn phải chọn một trong ba hướng:

- **Script hoặc notebook viết nhanh** nhưng rất khó bảo trì lâu dài
- **Framework giao dịch** mạnh về khâu thực thi lệnh nhưng ít tập trung vào quy trình học máy
- **Nền tảng MLOps chạy trên đám mây** tiện lợi nhưng phải đánh đổi quyền kiểm soát

MLFX chọn một điểm cân bằng hợp lý hơn:

- 🏠 **Ưu tiên chạy cục bộ** — dữ liệu, mô hình, artifact và toàn bộ quy trình nằm trong tầm kiểm soát của bạn
- 🔁 **Dễ tái lập** — cấu hình rõ ràng, môi trường được quản lý bằng Pixi, mọi thứ chạy qua CLI thống nhất
- 🧱 **Tách lớp rõ ràng** — các phần ingest dữ liệu, pipeline, huấn luyện, đánh giá, phục vụ mô hình và giám sát được phân tách mạch lạc
- 🔬 **Phù hợp cho nghiên cứu** — dễ benchmark backend, kiểm tra artifact và lặp lại thí nghiệm
- 🌍 **Dễ tiếp cận như một dự án mã nguồn mở** — cấu trúc sáng sủa, có tài liệu và hỗ trợ song ngữ Anh - Việt

---

## Bạn có thể làm gì với MLFX

Với MLFX, bạn có thể:

- 📈 Thu thập dữ liệu thị trường lịch sử từ Dukascopy
- ⏱️ Chuyển dữ liệu tick thô thành OHLCV theo nhiều khung thời gian
- 🛠️ Xây dựng đặc trưng kỹ thuật và đặc trưng theo ngữ cảnh
- 🏷️ Tạo nhãn cho các bài toán học có giám sát
- ⚙️ Huấn luyện và so sánh nhiều họ mô hình khác nhau
- 🧾 Chạy backtest và xuất báo cáo
- 🌐 Cung cấp suy luận qua API
- 🚨 Phát hiện độ lệch dữ liệu trong các quy trình gần với môi trường vận hành thực tế

---

## Các tình huống sử dụng phù hợp

MLFX đặc biệt hữu ích trong những tình huống như:

- 💱 **Xây pipeline nghiên cứu ngoại hối** — tạo các thí nghiệm có thể lặp lại trên dữ liệu Dukascopy
- 🥇 **So sánh nhiều mô hình** — đặt các mô hình học máy cổ điển, học sâu và forecasting vào cùng một hệ thống để đối chiếu
- 🧪 **Thử nghiệm đặc trưng** — kiểm tra indicator, nhãn và phép biến đổi dữ liệu mà không phải dựng lại toàn bộ hạ tầng
- 🌐 **Tạo nguyên mẫu API suy luận** — chuyển từ nghiên cứu ngoại tuyến sang phục vụ mô hình thuận tiện hơn
- 📉 **Giám sát và kiểm tra độ lệch dữ liệu** — theo dõi xem dữ liệu mới có đang lệch khỏi tập huấn luyện hay không

---

## Luồng làm việc cốt lõi

```text
download
  -> qa
  -> pipeline
  -> train
  -> evaluate
  -> benchmark
  -> serve / batch-predict
  -> drift
```

### Ý nghĩa từng bước

- `download` — tải dữ liệu tick thô từ Dukascopy
- `qa` — kiểm tra dữ liệu thô để phát hiện khoảng trống và bất thường
- `pipeline` — tạo OHLCV, đặc trưng và nhãn
- `train` — huấn luyện backend đã chọn và lưu artifact
- `evaluate` — backtest kết quả và sinh báo cáo
- `benchmark` — so sánh nhiều backend theo cùng một quy trình
- `serve` — khởi động API suy luận
- `batch-predict` — xuất kết quả dự đoán ngoại tuyến
- `drift` — so sánh phân phối đặc trưng mới với mốc tham chiếu

---

## Điểm nổi bật

- ✨ CLI thống nhất: `mlfx`
- 🟣 Quy trình phát triển theo hướng Pixi-first
- 📥 Thu thập dữ liệu tick lịch sử
- 🧪 Pipeline kiểm tra chất lượng, chuyển đổi và gắn nhãn
- 🤖 Nhiều backend huấn luyện
- 📊 Luồng đánh giá, báo cáo và benchmark
- ⚡ Lớp phục vụ mô hình bằng FastAPI
- 👀 Quy trình theo dõi độ lệch dữ liệu
- 🌐 Hệ thống tài liệu song ngữ Anh - Việt

---

## Các backend hiện có

| Backend | Mô tả |
| --- | --- |
| `mlf` | Mô hình nền MLForecast + LightGBM |
| `lstm` | Mô hình PyTorch LSTM |
| `bilstm` | Mô hình LSTM hai chiều |
| `transformer` | Bộ mã hóa Transformer |
| `cnn_lstm` | Mô hình lai CNN + LSTM |
| `sgd` | Mô hình nền `SGDClassifier` dạng online |
| `stats` | Các mô hình dự báo thống kê cơ sở |
| `neuralforecast` | Nhóm mô hình của NeuralForecast |

MLFX được thiết kế để bạn có thể so sánh các hướng tiếp cận này trong cùng một cấu trúc thống nhất, thay vì phải dựng lại toàn bộ phần hạ tầng mỗi khi thử một mô hình mới.

---

## Bắt đầu nhanh

### Yêu cầu

- Linux `x86_64` / `linux-64`
- Đã cài [Pixi](https://pixi.sh/)
- Không cần tự tạo `venv` hoặc `uv` cho quy trình chuẩn

### Cài môi trường

```bash
pixi install
```

### Chạy một luồng end-to-end tối thiểu

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

Sau bước `evaluate`, MLFX sẽ in ra các chỉ số tổng hợp và đường dẫn đến những báo cáo được tạo.

Để xem hướng dẫn bắt đầu đầy đủ:

- Bản tiếng Anh: [docs/en/getting-started/QUICKSTART.md](docs/en/getting-started/QUICKSTART.md)
- Bản tiếng Việt: [docs/vi/getting-started/QUICKSTART.md](docs/vi/getting-started/QUICKSTART.md)

---

## Các lệnh thường dùng

```bash
pixi run mlfx
pixi run test
pixi run verify
pixi run clean-generated
```

### Giải thích nhanh

- `pixi run mlfx` — điểm vào CLI thống nhất
- `pixi run test` — chạy toàn bộ bộ kiểm thử
- `pixi run verify` — chạy các kiểm thử smoke và contract quan trọng
- `pixi run clean-generated` — dọn dẹp cache và các đầu ra được sinh tự động

---

## Cấu trúc dự án

```text
MLFX/
├── mlfx/
│   ├── app/            # Các điểm vào CLI
│   ├── config/         # Nạp cấu hình và chính sách đường dẫn
│   ├── ingestion/      # Tải dữ liệu lịch sử
│   ├── pipeline/       # Kiểm tra chất lượng, chuyển đổi, đặc trưng, nhãn
│   ├── features/       # Các mô-đun đặc trưng
│   ├── training/       # Hệ thống huấn luyện backend
│   ├── evaluation/     # Backtest và báo cáo
│   ├── tracking/       # Theo dõi thí nghiệm
│   ├── registry/       # Sổ đăng ký mô hình
│   ├── serving/        # Lớp suy luận dùng FastAPI
│   └── monitoring/     # Phát hiện độ lệch và giám sát
├── docs/               # Cổng tài liệu song ngữ
├── data/               # Dữ liệu thô và dữ liệu đã xử lý
├── outputs/            # Mô hình, báo cáo, dự đoán, đầu ra giám sát
├── tests/              # Kiểm thử và kiểm thử tích hợp
├── Dockerfile
├── docker-compose.yml
├── config.toml
└── pyproject.toml
```

---

## Các đầu ra được tạo ra

MLFX tổ chức đầu ra theo cách giúp thí nghiệm dễ kiểm tra và dễ tái sử dụng:

- `data/raw/{symbol}/` — dữ liệu tick thô đã tải
- `data/ohlcv/{symbol}/{tf}/` — tệp parquet OHLCV sau khi chuyển đổi
- `data/features/{symbol}/{tf}/` — tập dữ liệu đặc trưng
- `data/labels/{symbol}/{tf}/` — tập dữ liệu đã gắn nhãn
- `outputs/models/{symbol}/{tf}/` — artifact mô hình và siêu dữ liệu
- `outputs/reports/{symbol}/{tf}/` — báo cáo từ bước đánh giá
- `outputs/predictions/{symbol}/{tf}/` — kết quả dự đoán theo lô
- `outputs/monitoring/{symbol}/{tf}/` — mốc tham chiếu độ lệch và cảnh báo

---

## Tài liệu

### Bắt đầu từ đây

- Cổng tài liệu: [docs/README.md](docs/README.md)
- Tài liệu tiếng Anh: [docs/en/README.md](docs/en/README.md)
- Tài liệu tiếng Việt: [docs/vi/README.md](docs/vi/README.md)

### Lộ trình đọc khuyến nghị

**Nếu bạn mới vào repo**
- [Bắt đầu nhanh (EN)](docs/en/getting-started/QUICKSTART.md)
- [Bắt đầu nhanh (VI)](docs/vi/getting-started/QUICKSTART.md)
- [Hướng dẫn nhập môn (EN)](docs/en/getting-started/NOOB_GUIDE.md)
- [Hướng dẫn nhập môn (VI)](docs/vi/getting-started/NOOB_GUIDE.md)

**Nếu bạn muốn dùng CLI**
- [Hướng dẫn sử dụng (EN)](docs/en/guides/USAGE_GUIDE.md)
- [Hướng dẫn sử dụng (VI)](docs/vi/guides/USAGE_GUIDE.md)

**Nếu bạn muốn hiểu phần đánh giá**
- [Hướng dẫn đánh giá (EN)](docs/en/guides/EVALUATION_GUIDE.md)
- [Hướng dẫn đánh giá (VI)](docs/vi/guides/EVALUATION_GUIDE.md)

**Nếu bạn muốn xem kiến trúc**
- [Kiến trúc (EN)](docs/en/architecture/ARCHITECTURE.md)
- [Kiến trúc (VI)](docs/vi/architecture/ARCHITECTURE.md)
- [So sánh backend (EN)](docs/en/architecture/BACKEND_COMPARISON.md)
- [So sánh backend (VI)](docs/vi/architecture/BACKEND_COMPARISON.md)

**Tài liệu kế hoạch**
- [Lộ trình (EN)](docs/en/meta/ROADMAP.md)
- [Lộ trình (VI)](docs/vi/meta/ROADMAP.md)
- [Việc cần làm (EN)](docs/en/meta/TODO.md)
- [Việc cần làm (VI)](docs/vi/meta/TODO.md)

---

## MLFX phù hợp với ai?

MLFX phù hợp nếu bạn là:

- Một nhà nghiên cứu định lượng hoặc người làm nghiên cứu cá nhân muốn có workflow cục bộ, có cấu trúc
- Một kỹ sư không muốn liên tục viết lại glue code cho dữ liệu, huấn luyện và đánh giá
- Người đang muốn so sánh các mô hình học máy cổ điển, học sâu và forecasting
- Người dùng mã nguồn mở coi trọng quyền kiểm soát, khả năng tái lập và các artifact có thể kiểm tra được

MLFX có thể không phải lựa chọn phù hợp nhất nếu bạn chỉ cần:

- Một bot giao dịch cắm vào là chạy gần như không cần cấu hình
- Một quy trình hoàn toàn quản lý trên đám mây
- Một framework chỉ tập trung vào thực thi mà không quan tâm đến thí nghiệm học máy

---

## Định hướng hiện tại

MLFX hiện đã bao phủ khá tốt vòng lặp nghiên cứu cốt lõi.

Các cải tiến lớn tiếp theo tập trung vào:

- Tăng độ tin cậy của lớp phục vụ mô hình
- Làm rõ hợp đồng đầu vào/đầu ra cho suy luận
- Bổ sung cơ chế thử lại và cô lập lỗi tốt hơn
- Nâng cao khả năng quan sát hệ thống
- Mở rộng không gian thử nghiệm backend
- Cải thiện tính nhất quán của benchmark

Xem roadmap để biết thêm chi tiết:

- [Lộ trình tiếng Anh](docs/en/meta/ROADMAP.md)
- [Lộ trình tiếng Việt](docs/vi/meta/ROADMAP.md)

---

## Đóng góp

Mọi đóng góp đều được chào đón.

Nếu bạn thích hướng đi của dự án, một ⭐ trên GitHub là cách đơn giản nhất để ủng hộ.

Các hướng đóng góp phù hợp gồm:

- Backend mô hình mới
- Cải tiến phần xây dựng đặc trưng
- Adapter dữ liệu thời gian thực
- Cải tiến đánh giá và báo cáo
- Tăng độ ổn định cho lớp phục vụ mô hình
- Hoàn thiện tài liệu
- Kiểm thử và nâng cao khả năng tái lập

Nếu bạn mới bắt đầu khám phá repo, hãy đọc:

- [docs/README.md](docs/README.md)
- [docs/en/getting-started/QUICKSTART.md](docs/en/getting-started/QUICKSTART.md)
- [docs/en/architecture/ARCHITECTURE.md](docs/en/architecture/ARCHITECTURE.md)

---

## Tác giả

**Hieu Nguyen**  
GitHub: [@ultimateBroK](https://github.com/ultimateBroK)

---

## Giấy phép

Dự án này được phát hành theo giấy phép Apache License 2.0.

Xem [LICENSE](LICENSE) để biết chi tiết.
