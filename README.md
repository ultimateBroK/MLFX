# MLFX

`MLFX` là một pipeline MLOps nghiên cứu dữ liệu thị trường, tập trung vào 5 giai đoạn chính:
- Tải tick data lịch sử từ Dukascopy
- Chuẩn hóa thành OHLCV theo nhiều timeframe
- Sinh feature kỹ thuật và feature theo ngữ cảnh ICT
- Gắn nhãn phục vụ huấn luyện
- Train, evaluate và xuất báo cáo

Repo được vận hành theo hướng `Pixi-first`. Mọi lệnh thường ngày nên chạy qua `pixi run`.

## Tài liệu

- Cổng tài liệu tổng:
  - [docs/README.md](docs/README.md)
- Tiếng Việt:
  - [README.md](docs/vi/README.md)
  - [QUICKSTART.md](docs/vi/getting-started/QUICKSTART.md)
  - [NOOB_GUIDE.md](docs/vi/getting-started/NOOB_GUIDE.md)
  - [USAGE_GUIDE.md](docs/vi/guides/USAGE_GUIDE.md)
  - [EVALUATION_GUIDE.md](docs/vi/guides/EVALUATION_GUIDE.md)
  - [TROUBLESHOOTING.md](docs/vi/guides/TROUBLESHOOTING.md)
  - [FEATURE_REFERENCE.md](docs/vi/reference/FEATURE_REFERENCE.md)
  - [CONFIG_REFERENCE.md](docs/vi/reference/CONFIG_REFERENCE.md)
  - [API_REFERENCE.md](docs/vi/reference/API_REFERENCE.md)
  - [GLOSSARY.md](docs/vi/reference/GLOSSARY.md)
  - [ARCHITECTURE.md](docs/vi/architecture/ARCHITECTURE.md)
  - [BACKEND_COMPARISON.md](docs/vi/architecture/BACKEND_COMPARISON.md)
  - [ROADMAP.md](docs/vi/meta/ROADMAP.md)
- English:
  - [README.md](docs/en/README.md)
  - [QUICKSTART.md](docs/en/getting-started/QUICKSTART.md)
  - [NOOB_GUIDE.md](docs/en/getting-started/NOOB_GUIDE.md)
  - [USAGE_GUIDE.md](docs/en/guides/USAGE_GUIDE.md)
  - [EVALUATION_GUIDE.md](docs/en/guides/EVALUATION_GUIDE.md)
  - [TROUBLESHOOTING.md](docs/en/guides/TROUBLESHOOTING.md)
  - [FEATURE_REFERENCE.md](docs/en/reference/FEATURE_REFERENCE.md)
  - [CONFIG_REFERENCE.md](docs/en/reference/CONFIG_REFERENCE.md)
  - [API_REFERENCE.md](docs/en/reference/API_REFERENCE.md)
  - [GLOSSARY.md](docs/en/reference/GLOSSARY.md)
  - [ARCHITECTURE.md](docs/en/architecture/ARCHITECTURE.md)
  - [BACKEND_COMPARISON.md](docs/en/architecture/BACKEND_COMPARISON.md)
  - [ROADMAP.md](docs/en/meta/ROADMAP.md)

## Yêu cầu môi trường

- Pixi đã được cài trên máy
- Linux 64-bit là platform hiện được pin trong `pyproject.toml`
- Python được quản lý bởi Pixi, không cần tự tạo `uv` hoặc `venv` riêng cho workflow chuẩn

Cài môi trường:

```bash
pixi install
```

## Entrypoint chính

- `pixi run mlfx` cho CLI hợp nhất
- `pixi run test` để chạy toàn bộ test suite
- `pixi run verify` để chạy bộ test smoke/contract trọng tâm
- `pixi run clean-generated` để dọn cache và generated artifacts an toàn

## Luồng vận hành chuẩn (MLOps pipeline)

```text
download  →  qa  →  pipeline  →  train  →  evaluate
                                   ↓            ↓
                               tracking       reports
                               registry
                                   ↓
                              serve / batch-predict
                                   ↓
                                drift
```

Ý nghĩa từng bước:
- `download`: Tải raw tick data từ Dukascopy.
- `qa`: Audit raw data để phát hiện gap hoặc dữ liệu bất thường.
- `pipeline`: Resample → feature engineering → labeling.
- `train`: Huấn luyện backend đã chọn (kết quả được track và register tự động).
- `evaluate`: Backtest model (hoặc labels nếu chưa train) và sinh báo cáo; in metrics ra console.
- `serve`: Khởi động FastAPI inference server.
- `batch-predict`: Export predictions parquet (dùng khi deploy; xem kết quả dùng `evaluate`).
- `drift`: So sánh phân phối feature live vs training để phát hiện drift.
- `models`: Liệt kê các model version đã đăng ký.

## Bắt đầu nhanh

Quickstart canonical đã được tách sang hệ thống docs mới để tránh trùng lặp và giữ luồng bắt đầu nhanh nhất ở một nơi duy nhất:

- Tiếng Việt: [docs/vi/getting-started/QUICKSTART.md](docs/vi/getting-started/QUICKSTART.md)
- English: [docs/en/getting-started/QUICKSTART.md](docs/en/getting-started/QUICKSTART.md)

Quickstart rút gọn:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

Sau `evaluate`, CLI in bảng metrics và đường dẫn biểu đồ. Mặc định backtest **model** nếu đã train.

## Backend huấn luyện hiện có

| Key | Mô tả |
|---|---|
| `mlf` | MLForecast + LightGBM (default) |
| `lstm` | PyTorch LSTM với HPO Optuna |
| `bilstm` | Bidirectional LSTM |
| `transformer` | PyTorch Transformer encoder |
| `cnn_lstm` | CNN + LSTM hybrid |
| `sgd` | Online SGDClassifier (sklearn) |
| `stats` | StatsForecast baseline (AutoARIMA, SeasonalNaive) |
| `neuralforecast` | NeuralForecast (NHiTS, NBEATS) |

Chi tiết tham số và ví dụ đầy đủ nằm trong:
- [docs/vi/guides/USAGE_GUIDE.md](docs/vi/guides/USAGE_GUIDE.md)
- [docs/en/guides/USAGE_GUIDE.md](docs/en/guides/USAGE_GUIDE.md)

## Cấu trúc dự án (MLOps)

```text
MLFX/
├── mlfx/
│   ├── app/            # CLI
│   ├── config/         # path policy và config loader
│   ├── ingestion/      # downloader Dukascopy
│   ├── pipeline/       # qa, resampling, feature engineering, labeling
│   ├── features/       # feature modules theo domain (indicators)
│   ├── training/
│   │   ├── backends/           # Backend implementations (mlf, lstm, transformer, ...)
│   │   │   └── base.py         # BackendRunner protocol, TrainingConfig, TrainResult
│   │   ├── data.py             # Dataset loading helpers
│   │   ├── feature_selection.py# Feature selection helpers
│   │   ├── artifacts.py        # Artifact persistence helpers
│   │   ├── config.py           # Public TrainingConfig/TrainResult aliases
│   │   ├── runner.py           # High-level orchestrator (track + register)
│   │   └── registry.py         # Backend key → module:function map
│   ├── evaluation/     # backtest, reporting, evaluation runner
│   ├── tracking/       # Experiment tracking (MLflow / file-based fallback)
│   ├── registry/       # Model registry (JSON-backed, MLflow-extensible)
│   ├── serving/        # FastAPI real-time API + batch inference
│   └── monitoring/     # Feature drift detection + structured JSON logging
├── docs/               # hub tài liệu và archive
│   ├── en/             # tài liệu tiếng Anh
│   ├── vi/             # tài liệu tiếng Việt
│   └── archive/        # tracking / legacy docs
├── data/               # raw, ohlcv, features, labels
├── outputs/
│   ├── models/         # registry.json + {symbol}/{tf}/ (model artifacts)
│   ├── reports/        # {symbol}/{tf}/ (HTML/PNG backtest reports)
│   ├── runs/           # {symbol}/{tf}/ (file-tracker run JSONs)
│   ├── predictions/    # {symbol}/{tf}/ (batch inference results)
│   └── monitoring/     # {symbol}/{tf}/ (drift reference snapshots + alerts)
├── Dockerfile          # multi-stage container image
├── docker-compose.yml  # API server + optional MLflow server
├── config.toml         # giá trị mặc định cho CLI
└── pyproject.toml      # package metadata, Pixi config, tasks
```

## Artifacts chính

- `data/raw/{symbol}/`: raw tick data và file state download
- `data/ohlcv/{symbol}/{tf}/`: parquet sau resample
- `data/features/{symbol}/{tf}/`: parquet đã thêm feature
- `data/labels/{symbol}/{tf}/`: parquet đã gắn nhãn
- `outputs/models/{symbol}/{tf}/`: model artifacts, metrics, metadata train
- `outputs/reports/{symbol}/{tf}/`: HTML/PNG reports từ evaluate

## Chính sách cleanup

- `data/raw/` nên được giữ lại nếu muốn tái tạo pipeline mà không tải lại dữ liệu
- `data/ohlcv/`, `data/features/`, `data/labels/`, `outputs/`, `lightning_logs/`, `.pixi-cache/`, `.cache/` là phần có thể tái sinh
- Dùng `pixi run clean-generated` khi muốn dọn generated artifacts và cache phổ biến trong workspace

## Bước tiếp theo nên đọc

- [docs/README.md](docs/README.md) để vào cổng tài liệu mới
- [docs/vi/getting-started/NOOB_GUIDE.md](docs/vi/getting-started/NOOB_GUIDE.md) nếu mới vào repo
- [docs/vi/guides/USAGE_GUIDE.md](docs/vi/guides/USAGE_GUIDE.md) nếu cần chạy từng lệnh cụ thể
- [docs/vi/architecture/ARCHITECTURE.md](docs/vi/architecture/ARCHITECTURE.md) để xem kiến trúc MLOps chi tiết
- [docs/vi/guides/EVALUATION_GUIDE.md](docs/vi/guides/EVALUATION_GUIDE.md) nếu muốn hiểu report và metrics
- [docs/vi/guides/TROUBLESHOOTING.md](docs/vi/guides/TROUBLESHOOTING.md) nếu đang gặp lỗi môi trường hoặc dữ liệu
- [docs/en/README.md](docs/en/README.md) nếu muốn đọc tài liệu tiếng Anh

## Tác giả

Hieu Nguyen  
GitHub: [@ultimateBroK](https://github.com/ultimateBroK)
