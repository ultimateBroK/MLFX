# MLFX

> Quy trình MLOps ưu tiên cục bộ, ưu tiên Pixi dành cho nghiên cứu dữ liệu thị trường, xây dựng đặc trưng, dự báo, đánh giá và phục vụ mô hình.

[![Python](https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=white)](#yêu-cầu)
[![Pixi](https://img.shields.io/badge/quy_tr%C3%ACnh-pixi-7A4DFF)](#bắt-đầu-nhanh)
[![Platform](https://img.shields.io/badge/platform-linux--64-1793D1?logo=linux&logoColor=white)](#yêu-cầu)
[![Docs](https://img.shields.io/badge/docs-song_ngữ-brightgreen)](docs/README.md)
[![FastAPI](https://img.shields.io/badge/api-FastAPI-009688?logo=fastapi&logoColor=white)](#điểm-nổi-bật)
[![Polars](https://img.shields.io/badge/data-Polars-CD792C?logo=polars&logoColor=white)](#điểm-nổi-bật)
[![PyTorch](https://img.shields.io/badge/dl-PyTorch-EE4C2C?logo=pytorch&logoColor=white)](#các-bộ-máy-hiện-có)
[![LightGBM](https://img.shields.io/badge/gbm-LightGBM-02569B)](#các-bộ-máy-hiện-có)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Stars](https://img.shields.io/github/stars/ultimateBroK/MLFX?style=social)](https://github.com/ultimateBroK/MLFX/stargazers)

MLFX là một khung làm việc mã nguồn mở, vận hành cục bộ, giúp bạn xây dựng quy trình học máy cho dữ liệu thị trường theo cách dễ chạy, dễ gỡ lỗi, dễ so sánh và dễ mở rộng.

Thiết lập một lần, thử nghiệm nhiều lần:

- 📥 Thu thập dữ liệu tick lịch sử
- 🧪 Kiểm tra chất lượng và chuyển đổi sang OHLCV
- 🧩 Tạo đặc trưng và nhãn
- 🤖 Huấn luyện nhiều bộ máy dự báo khác nhau
- 📊 So sánh chuẩn và đánh giá kết quả
- 🚀 Phục vụ dự đoán và theo dõi độ lệch dữ liệu

Dù bạn là nhà nghiên cứu định lượng cá nhân, kỹ sư ML, hay trader thiên về hệ thống, MLFX mang lại một quy trình có thể tái lập mà không ép bạn phải phụ thuộc vào nền tảng đám mây hay một mớ sổ tay tính toán rời rạc.

> ⭐ Nếu MLFX hữu ích với bạn, hãy tặng kho mã này một ngôi sao — điều đó giúp nhiều người làm dự án khác khám phá dự án hơn.

## Mục lục

- [Vì sao nên dùng MLFX?](#vì-sao-nên-dùng-mlfx)
- [Bạn có thể làm gì với MLFX](#bạn-có-thể-làm-gì-với-mlfx)
- [Các tình huống sử dụng phù hợp](#các-tình-huống-sử-dụng-phù-hợp)
- [Luồng làm việc cốt lõi](#luồng-làm-việc-cốt-lõi)
- [Điểm nổi bật](#điểm-nổi-bật)
- [Các bộ máy hiện có](#các-bộ-máy-hiện-có)
- [Bắt đầu nhanh](#bắt-đầu-nhanh)
- [Yêu cầu](#yêu-cầu)
- [Cài môi trường](#cài-môi-trường)
- [Chạy một luồng end-to-end tối thiểu](#chạy-một-luồng-end-to-end-tối-thiểu)
- [Các lệnh thường dùng](#các-lệnh-thường-dùng)
- [Tham chiếu nhanh cho lệnh](#tham-chiếu-nhanh-cho-lệnh)
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

- **Kịch bản viết nhanh** nhưng rất khó bảo trì
- **Khung giao dịch** mạnh về thực thi nhưng ít định hướng cho quy trình ML
- **Công cụ MLOps trên đám mây** tiện lợi nhưng làm giảm quyền kiểm soát

MLFX đứng ở khoảng giữa:

- 🏠 **Ưu tiên chạy cục bộ** — dữ liệu, tệp đầu ra và quy trình vẫn nằm trong tầm kiểm soát của bạn
- 🔁 **Dễ tái lập** — vận hành theo cấu hình, quản lý bằng Pixi, ưu tiên CLI
- 🧱 **Mô-đun rõ ràng** — các lớp nạp dữ liệu, xử lý, huấn luyện, đánh giá, phục vụ và giám sát được tách biệt rõ ràng
- 🔬 **Thân thiện cho nghiên cứu** — dễ so sánh các bộ máy, kiểm tra tệp đầu ra và lặp lại thí nghiệm
- 🌍 **Dễ tiếp cận như một dự án mã nguồn mở** — cấu trúc dễ đọc, quy trình có tài liệu, tài liệu song ngữ

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
- 🚨 Phát hiện độ lệch đặc trưng trong các quy trình gần với môi trường vận hành thực tế

---

## Các tình huống sử dụng phù hợp

MLFX đặc biệt hữu ích trong những quy trình như:

- 💱 **Quy trình nghiên cứu FX** — xây các thí nghiệm có thể lặp lại trên dữ liệu Dukascopy
- 🥇 **So sánh chuẩn mô hình** — so sánh ML cổ điển, học sâu và các bộ máy dự báo trong cùng một nơi
- 🧪 **Thử nghiệm xây dựng đặc trưng** — kiểm tra chỉ báo, nhãn và phép biến đổi mà không phải dựng lại toàn bộ hạ tầng
- 🌐 **Tạo nguyên mẫu API suy luận** — chuyển từ nghiên cứu ngoại tuyến sang phục vụ mô hình với ít ma sát hơn
- 📉 **Giám sát và kiểm tra độ lệch** — kiểm tra xem dữ liệu gần thời gian thực có đang lệch khỏi mốc huấn luyện hay không

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
- `train` — huấn luyện bộ máy đã chọn và lưu tệp đầu ra
- `evaluate` — backtest kết quả và sinh báo cáo
- `benchmark` — so sánh nhiều bộ máy theo cùng một quy trình
- `serve` — khởi động API suy luận
- `batch-predict` — xuất kết quả dự đoán ngoại tuyến
- `drift` — so sánh phân phối đặc trưng gần đây với mốc tham chiếu

---

## Điểm nổi bật

- ✨ CLI thống nhất: `mlfx`
- 🟣 Quy trình phát triển theo hướng Pixi-first
- 📥 Thu thập dữ liệu tick lịch sử
- 🧪 Pipeline kiểm tra chất lượng, chuyển đổi và gắn nhãn
- 🤖 Nhiều bộ máy huấn luyện
- 📊 Luồng đánh giá + báo cáo + so sánh chuẩn
- ⚡ Lớp phục vụ mô hình bằng FastAPI
- 👀 Quy trình theo dõi độ lệch dữ liệu
- 🌐 Tài liệu song ngữ: tiếng Anh + tiếng Việt

---

## Các bộ máy hiện có

| Bộ máy | Mô tả |
| --- | --- |
| `mlf` | Mô hình nền MLForecast + LightGBM |
| `lstm` | Mô hình PyTorch LSTM |
| `bilstm` | Mô hình LSTM hai chiều |
| `transformer` | Bộ mã hóa Transformer |
| `cnn_lstm` | Mô hình lai CNN + LSTM |
| `sgd` | Mô hình nền `SGDClassifier` dạng trực tuyến |
| `stats` | Các mô hình dự báo thống kê cơ sở |
| `neuralforecast` | Nhóm mô hình thuộc NeuralForecast |

MLFX được thiết kế để bạn có thể so sánh các hướng tiếp cận này trong cùng một cấu trúc thống nhất, thay vì phải dựng lại cùng một phần hạ tầng mỗi lần.

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

### Chạy một luồng tối thiểu từ đầu đến cuối

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

Sau bước `evaluate`, MLFX sẽ in ra các chỉ số tổng hợp và gợi ý đường dẫn tới các báo cáo được tạo.

Để xem hướng dẫn bắt đầu đầy đủ:

- Tiếng Anh: [docs/en/getting-started/QUICKSTART.md](docs/en/getting-started/QUICKSTART.md)
- Tiếng Việt: [docs/vi/getting-started/QUICKSTART.md](docs/vi/getting-started/QUICKSTART.md)

---

## Các lệnh thường dùng

```bash
pixi run mlfx
pixi run test
pixi run verify
pixi run clean-generated
```

### Tham chiếu nhanh cho lệnh

- `pixi run mlfx` — điểm vào CLI thống nhất
- `pixi run test` — chạy toàn bộ bộ kiểm thử
- `pixi run verify` — chạy các kiểm thử smoke / contract quan trọng
- `pixi run clean-generated` — xóa an toàn các vùng nhớ đệm và tệp đầu ra sinh tự động thường gặp

---

## Cấu trúc dự án

```text
MLFX/
├── mlfx/
│   ├── app/            # Các điểm vào CLI
│   ├── config/         # Nạp cấu hình và chính sách đường dẫn
│   ├── ingestion/      # Tải dữ liệu lịch sử
│   ├── pipeline/       # qa, chuyển đổi, đặc trưng, nhãn
│   ├── features/       # Các mô-đun đặc trưng
│   ├── training/       # Hệ thống huấn luyện bộ máy
│   ├── evaluation/     # Backtest và báo cáo
│   ├── tracking/       # Theo dõi thí nghiệm
│   ├── registry/       # Sổ đăng ký mô hình
│   ├── serving/        # Lớp suy luận FastAPI
│   └── monitoring/     # Phát hiện drift và giám sát
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

MLFX tổ chức đầu ra theo cách giúp thí nghiệm luôn dễ kiểm tra:

- `data/raw/{symbol}/` — dữ liệu tick thô đã tải
- `data/ohlcv/{symbol}/{tf}/` — tệp parquet OHLCV sau khi chuyển đổi
- `data/features/{symbol}/{tf}/` — tập dữ liệu đặc trưng
- `data/labels/{symbol}/{tf}/` — tập dữ liệu đã gắn nhãn
- `outputs/models/{symbol}/{tf}/{label}/` — tệp mô hình và siêu dữ liệu theo từng nhãn
- `outputs/reports/{symbol}/{tf}/{label}/{mode}/Rxx/` — báo cáo đánh giá theo nhãn, chế độ (`model` hoặc `labels`) và mức rủi ro
- `outputs/predictions/{symbol}/{tf}/{label}/` — kết quả dự đoán theo lô cho từng nhãn
- `outputs/monitoring/{symbol}/{tf}/` — mốc tham chiếu drift và cảnh báo

---

## Tài liệu

### Bắt đầu từ đây

- Cổng tài liệu: [docs/README.md](docs/README.md)
- Tài liệu tiếng Anh: [docs/en/README.md](docs/en/README.md)
- Tài liệu tiếng Việt: [docs/vi/README.md](docs/vi/README.md)

### Lộ trình đọc khuyến nghị

**Nếu bạn mới vào kho mã**
- [Bắt đầu nhanh (Tiếng Anh)](docs/en/getting-started/QUICKSTART.md)
- [Bắt đầu nhanh (Tiếng Việt)](docs/vi/getting-started/QUICKSTART.md)
- [Hướng dẫn nhập môn (Tiếng Anh)](docs/en/getting-started/NOOB_GUIDE.md)
- [Hướng dẫn nhập môn (Tiếng Việt)](docs/vi/getting-started/NOOB_GUIDE.md)

**Nếu bạn muốn dùng CLI**
- [Hướng dẫn sử dụng (Tiếng Anh)](docs/en/guides/USAGE_GUIDE.md)
- [Hướng dẫn sử dụng (Tiếng Việt)](docs/vi/guides/USAGE_GUIDE.md)

**Nếu bạn muốn hiểu phần đánh giá**
- [Hướng dẫn đánh giá (Tiếng Anh)](docs/en/guides/EVALUATION_GUIDE.md)
- [Hướng dẫn đánh giá (Tiếng Việt)](docs/vi/guides/EVALUATION_GUIDE.md)

**Nếu bạn muốn xem kiến trúc**
- [Kiến trúc (Tiếng Anh)](docs/en/architecture/ARCHITECTURE.md)
- [Kiến trúc (Tiếng Việt)](docs/vi/architecture/ARCHITECTURE.md)
- [So sánh bộ máy (Tiếng Anh)](docs/en/architecture/BACKEND_COMPARISON.md)
- [So sánh bộ máy (Tiếng Việt)](docs/vi/architecture/BACKEND_COMPARISON.md)

**Tài liệu kế hoạch**
- [Lộ trình (Tiếng Anh)](docs/en/meta/ROADMAP.md)
- [Lộ trình (Tiếng Việt)](docs/vi/meta/ROADMAP.md)
- [Việc cần làm (Tiếng Anh)](docs/en/meta/TODO.md)
- [Việc cần làm (Tiếng Việt)](docs/vi/meta/TODO.md)

---

## MLFX phù hợp với ai?

MLFX phù hợp nếu bạn là:

- Một nhà nghiên cứu định lượng cá nhân hoặc người làm nghiên cứu muốn có quy trình cục bộ, có cấu trúc
- Một kỹ sư mệt mỏi vì phải liên tục viết lại mã chắp vá cho dữ liệu / huấn luyện / đánh giá
- Người đang muốn so sánh các mô hình ML cổ điển, học sâu và các bộ máy dự báo
- Người dùng mã nguồn mở coi trọng quyền kiểm soát, khả năng tái lập và các tệp đầu ra có thể kiểm tra được

MLFX có thể ít phù hợp hơn nếu bạn chỉ muốn:

- Một bot giao dịch cắm vào là chạy gần như không cần thiết lập
- Một quy trình SaaS quản lý hoàn toàn trên đám mây
- Một framework chỉ tập trung vào thực thi mà không có nhu cầu thí nghiệm ML

---

## Định hướng hiện tại

MLFX hiện đã bao phủ khá tốt vòng lặp nghiên cứu cốt lõi.

Các cải tiến lớn tiếp theo tập trung vào:

- Độ tin cậy của lớp phục vụ mô hình
- Làm rõ hơn hợp đồng đầu vào / đầu ra cho suy luận
- Bổ sung cơ chế thử lại và cô lập lỗi
- Tăng khả năng quan sát hệ thống
- Mở rộng không gian thử nghiệm bộ máy
- Cải thiện tính nhất quán của so sánh chuẩn

Xem lộ trình để biết thêm chi tiết:

- [Lộ trình tiếng Anh](docs/en/meta/ROADMAP.md)
- [Lộ trình tiếng Việt](docs/vi/meta/ROADMAP.md)

---

## Đóng góp

Mọi đóng góp đều được chào đón.

Nếu bạn thích hướng đi của dự án, một ⭐ trên GitHub là một trong những cách đơn giản nhất để ủng hộ.

Các hướng đóng góp phù hợp gồm:

- Bộ máy mô hình mới
- Cải tiến phần xây dựng đặc trưng
- Bộ kết nối dữ liệu thời gian thực
- Cải tiến đánh giá / báo cáo
- Tăng độ ổn định cho lớp phục vụ mô hình
- Hoàn thiện tài liệu
- Kiểm thử và nâng cao khả năng tái lập

Nếu bạn mới bắt đầu khám phá kho mã, hãy bắt đầu với:

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
