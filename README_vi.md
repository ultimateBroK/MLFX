# MLFX

> Pipeline MLOps local-first, Pixi-first cho nghiên cứu dữ liệu thị trường, feature engineering, forecasting, evaluation và serving.

[![Python](https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=white)](README.md#quickstart)
[![Pixi](https://img.shields.io/badge/workflow-pixi-7A4DFF)](README.md#quickstart)
[![Platform](https://img.shields.io/badge/platform-linux--64-1793D1?logo=linux&logoColor=white)](README.md#quickstart)
[![Docs](https://img.shields.io/badge/docs-song_ngữ-brightgreen)](docs/README.md)
[![FastAPI](https://img.shields.io/badge/api-FastAPI-009688?logo=fastapi&logoColor=white)](README.md#highlights)
[![Polars](https://img.shields.io/badge/data-Polars-CD792C?logo=polars&logoColor=white)](README.md#highlights)
[![PyTorch](https://img.shields.io/badge/dl-PyTorch-EE4C2C?logo=pytorch&logoColor=white)](README.md#available-backends)
[![LightGBM](https://img.shields.io/badge/gbm-LightGBM-02569B)](README.md#available-backends)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

MLFX là một framework mã nguồn mở, local-first, giúp bạn xây dựng pipeline ML cho dữ liệu thị trường theo cách dễ chạy, dễ debug, dễ benchmark và dễ mở rộng.

Xây một lần, lặp nhanh nhiều lần:

- 📥 ingest dữ liệu tick lịch sử
- 🧪 kiểm tra chất lượng và resample sang OHLCV
- 🧩 tạo feature và label
- 🤖 train nhiều backend dự báo khác nhau
- 📊 benchmark và evaluate kết quả
- 🚀 serve prediction và theo dõi drift

Nếu bạn muốn một research stack sạch sẽ, có cấu trúc, thay vì một đống notebook rời rạc hoặc một nền tảng cloud khó kiểm soát, MLFX được xây cho đúng nhu cầu đó.

> ⭐ Nếu MLFX hữu ích với bạn, hãy star repo để nhiều builder khác tìm thấy dự án hơn.

## Mục lục

- [Vì sao là MLFX?](#vì-sao-là-mlfx)
- [Bạn có thể làm gì với MLFX](#bạn-có-thể-làm-gì-với-mlfx)
- [Use cases](#use-cases)
- [Luồng workflow cốt lõi](#luồng-workflow-cốt-lõi)
- [Highlights](#highlights)
- [Các backend hiện có](#các-backend-hiện-có)
- [Quickstart](#quickstart)
- [Các lệnh thường dùng](#các-lệnh-thường-dùng)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Artifacts được sinh ra](#artifacts-được-sinh-ra)
- [Tài liệu](#tài-liệu)
- [MLFX phù hợp với ai?](#mlfx-phù-hợp-với-ai)
- [Định hướng hiện tại](#định-hướng-hiện-tại)
- [Đóng góp](#đóng-góp)
- [Tác giả](#tác-giả)
- [Giấy phép](#giấy-phép)

---

## Vì sao là MLFX?

Phần lớn dự án trong mảng này buộc bạn phải chọn một trong ba hướng:

- **script nhanh / notebook nhanh** nhưng rất khó maintain
- **framework trading** mạnh về execution nhưng ít opinionated về workflow ML
- **nền tảng hosted MLOps** tiện lợi nhưng đánh đổi quyền kiểm soát

MLFX đứng ở điểm cân bằng hơn:

- 🏠 **Local-first** — dữ liệu, artifact và workflow nằm trong quyền kiểm soát của bạn
- 🔁 **Tái lập được** — config-driven, quản lý môi trường bằng Pixi, chạy qua CLI thống nhất
- 🧱 **Modular** — ingestion, pipeline, training, evaluation, serving, monitoring được tách rõ
- 🔬 **Thân thiện cho nghiên cứu** — dễ benchmark backend, inspect artifact, lặp thí nghiệm
- 🌍 **Dễ tiếp cận như một dự án open-source** — cấu trúc rõ ràng, có tài liệu, song ngữ Anh-Việt

---

## Bạn có thể làm gì với MLFX

Với MLFX, bạn có thể:

- 📈 ingest dữ liệu thị trường lịch sử từ Dukascopy
- ⏱️ resample dữ liệu tick thô thành OHLCV theo nhiều timeframe
- 🛠️ xây feature kỹ thuật và feature ngữ cảnh
- 🏷️ sinh label cho supervised learning
- ⚙️ train và so sánh nhiều họ model khác nhau
- 🧾 chạy backtest và xuất report
- 🌐 serve inference qua API
- 🚨 phát hiện drift trong workflow gần production

---

## Use cases

MLFX đặc biệt phù hợp cho các tình huống như:

- 💱 **FX research pipeline** — xây thí nghiệm lặp lại được trên dữ liệu Dukascopy
- 🥇 **Benchmark nhiều model** — so sánh ML cổ điển, deep learning và forecasting backend trong cùng một hệ thống
- 🧪 **Feature engineering experiments** — thử indicator, label, transformation mà không phải dựng lại cả stack
- 🌐 **Prototype inference API** — đi từ nghiên cứu offline sang serving với ít ma sát hơn
- 📉 **Monitoring và drift checks** — theo dõi xem dữ liệu mới có lệch khỏi baseline huấn luyện hay không

---

## Luồng workflow cốt lõi

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

- `download` — tải raw tick data từ Dukascopy
- `qa` — kiểm tra raw data để phát hiện gap và bất thường
- `pipeline` — tạo OHLCV, feature và label
- `train` — train backend đã chọn và lưu artifact
- `evaluate` — backtest kết quả và sinh report
- `benchmark` — so sánh nhiều backend theo cùng một quy trình
- `serve` — khởi động inference API
- `batch-predict` — xuất prediction offline
- `drift` — so sánh phân phối feature mới với baseline tham chiếu

---

## Highlights

- ✨ CLI thống nhất: `mlfx`
- 🟣 Workflow phát triển theo hướng Pixi-first
- 📥 Ingest dữ liệu tick lịch sử
- 🧪 Pipeline QA + resampling + labeling
- 🤖 Nhiều backend huấn luyện
- 📊 Evaluation + reporting + benchmark
- ⚡ FastAPI serving layer
- 👀 Drift monitoring workflow
- 🌐 Tài liệu song ngữ: English + Vietnamese

---

## Các backend hiện có

| Backend | Mô tả |
| --- | --- |
| `mlf` | Baseline MLForecast + LightGBM |
| `lstm` | PyTorch LSTM |
| `bilstm` | Bidirectional LSTM |
| `transformer` | Transformer encoder |
| `cnn_lstm` | Hybrid CNN + LSTM |
| `sgd` | Baseline `SGDClassifier` online |
| `stats` | Các baseline forecasting thống kê |
| `neuralforecast` | Họ model của NeuralForecast |

MLFX được thiết kế để bạn so sánh các hướng tiếp cận này trong cùng một cấu trúc thống nhất, thay vì phải dựng lại toàn bộ plumbing mỗi lần thử model mới.

---

## Quickstart

### Yêu cầu

- Linux `x86_64` / `linux-64`
- Đã cài [Pixi](https://pixi.sh/)
- Không cần tự tạo `venv` hoặc `uv` cho workflow chuẩn

### Cài môi trường

```bash
pixi install
```

### Chạy một flow end-to-end tối thiểu

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

Sau `evaluate`, MLFX sẽ in summary metrics và đường dẫn đến các report được sinh ra.

Để xem luồng onboarding đầy đủ:

- English: [docs/en/getting-started/QUICKSTART.md](docs/en/getting-started/QUICKSTART.md)
- Tiếng Việt: [docs/vi/getting-started/QUICKSTART.md](docs/vi/getting-started/QUICKSTART.md)

---

## Các lệnh thường dùng

```bash
pixi run mlfx
pixi run test
pixi run verify
pixi run clean-generated
```

### Giải thích nhanh

- `pixi run mlfx` — CLI entrypoint thống nhất
- `pixi run test` — chạy toàn bộ test suite
- `pixi run verify` — chạy smoke/contract checks quan trọng
- `pixi run clean-generated` — dọn cache và artifact được sinh tự động

---

## Cấu trúc dự án

```text
MLFX/
├── mlfx/
│   ├── app/            # CLI entrypoints
│   ├── config/         # nạp config và policy đường dẫn
│   ├── ingestion/      # tải dữ liệu lịch sử
│   ├── pipeline/       # qa, resampling, features, labels
│   ├── features/       # các module feature
│   ├── training/       # hệ thống train backend
│   ├── evaluation/     # backtesting và reports
│   ├── tracking/       # experiment tracking
│   ├── registry/       # model registry
│   ├── serving/        # FastAPI inference layer
│   └── monitoring/     # drift detection và monitoring
├── docs/               # hub tài liệu song ngữ
├── data/               # dữ liệu raw và processed
├── outputs/            # models, reports, predictions, monitoring outputs
├── tests/              # tests và integration coverage
├── Dockerfile
├── docker-compose.yml
├── config.toml
└── pyproject.toml
```

---

## Artifacts được sinh ra

MLFX tổ chức output theo cách giúp thí nghiệm dễ kiểm tra và dễ tái sử dụng:

- `data/raw/{symbol}/` — raw tick data đã tải
- `data/ohlcv/{symbol}/{tf}/` — file OHLCV parquet sau resample
- `data/features/{symbol}/{tf}/` — dataset feature
- `data/labels/{symbol}/{tf}/` — dataset đã gắn nhãn
- `outputs/models/{symbol}/{tf}/` — model artifact và metadata
- `outputs/reports/{symbol}/{tf}/` — report từ evaluation
- `outputs/predictions/{symbol}/{tf}/` — kết quả batch prediction
- `outputs/monitoring/{symbol}/{tf}/` — drift references và alerts

---

## Tài liệu

### Bắt đầu từ đây

- Cổng docs: [docs/README.md](docs/README.md)
- Docs tiếng Anh: [docs/en/README.md](docs/en/README.md)
- Docs tiếng Việt: [docs/vi/README.md](docs/vi/README.md)

### Lộ trình đọc khuyến nghị

**Nếu bạn mới vào repo**
- [English Quickstart](docs/en/getting-started/QUICKSTART.md)
- [Vietnamese Quickstart](docs/vi/getting-started/QUICKSTART.md)
- [Beginner Guide (EN)](docs/en/getting-started/NOOB_GUIDE.md)
- [Beginner Guide (VI)](docs/vi/getting-started/NOOB_GUIDE.md)

**Nếu bạn muốn dùng CLI**
- [Usage Guide (EN)](docs/en/guides/USAGE_GUIDE.md)
- [Usage Guide (VI)](docs/vi/guides/USAGE_GUIDE.md)

**Nếu bạn muốn hiểu evaluation**
- [Evaluation Guide (EN)](docs/en/guides/EVALUATION_GUIDE.md)
- [Evaluation Guide (VI)](docs/vi/guides/EVALUATION_GUIDE.md)

**Nếu bạn muốn xem kiến trúc**
- [Architecture (EN)](docs/en/architecture/ARCHITECTURE.md)
- [Architecture (VI)](docs/vi/architecture/ARCHITECTURE.md)
- [Backend Comparison (EN)](docs/en/architecture/BACKEND_COMPARISON.md)
- [Backend Comparison (VI)](docs/vi/architecture/BACKEND_COMPARISON.md)

**Tài liệu kế hoạch**
- [Roadmap (EN)](docs/en/meta/ROADMAP.md)
- [Roadmap (VI)](docs/vi/meta/ROADMAP.md)
- [TODO (EN)](docs/en/meta/TODO.md)
- [TODO (VI)](docs/vi/meta/TODO.md)

---

## MLFX phù hợp với ai?

MLFX phù hợp nếu bạn là:

- một solo quant hoặc researcher muốn workflow local có cấu trúc
- một engineer chán việc phải viết lại glue code cho data/training/evaluation
- người đang muốn so sánh ML cổ điển, deep learning và forecasting backend
- người dùng open-source coi trọng quyền kiểm soát, tính tái lập và artifact có thể inspect

MLFX có thể không phải lựa chọn lý tưởng nếu bạn chỉ cần:

- một trading bot plug-and-play gần như không cần setup
- một SaaS cloud-managed workflow
- một framework chỉ tập trung execution mà không quan tâm đến ML experimentation

---

## Định hướng hiện tại

MLFX hiện đã bao phủ khá tốt vòng lặp nghiên cứu cốt lõi.

Các cải tiến lớn tiếp theo tập trung vào:

- độ tin cậy của serving
- inference contracts rõ ràng hơn
- retry và failure isolation
- observability tốt hơn
- mở rộng backend experiments
- benchmark consistency tốt hơn

Xem roadmap để biết chi tiết:

- [English roadmap](docs/en/meta/ROADMAP.md)
- [Vietnamese roadmap](docs/vi/meta/ROADMAP.md)

---

## Đóng góp

Mọi đóng góp đều được chào đón.

Nếu bạn thích hướng đi của dự án, một ⭐ trên GitHub là cách đơn giản nhất để ủng hộ.

Các hướng đóng góp phù hợp gồm:

- backend model mới
- cải tiến feature engineering
- live data adapters
- cải tiến evaluation/reporting
- hardening serving layer
- polish tài liệu
- tests và cải thiện khả năng tái lập

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
