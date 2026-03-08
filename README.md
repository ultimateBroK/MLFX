# MLFX

`MLFX` là một pipeline MLOps nghiên cứu dữ liệu thị trường, tập trung vào 5 giai đoạn chính:
- tải tick data lịch sử từ Dukascopy
- chuẩn hóa thành OHLCV theo nhiều timeframe
- sinh feature kỹ thuật và feature theo ngữ cảnh ICT
- gắn nhãn phục vụ huấn luyện
- train, evaluate và xuất báo cáo

Repo được vận hành theo hướng `Pixi-first`. Mọi lệnh thường ngày nên chạy qua `pixi run`.

## Tài liệu

- Tiếng Việt:
  - [README.md](README.md)
  - [NOOB_GUIDE.md](docs/NOOB_GUIDE.md)
  - [USAGE_GUIDE.md](docs/USAGE_GUIDE.md)
  - [EVALUATION_GUIDE.md](docs/EVALUATION_GUIDE.md)
  - [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
  - [GLOSSARY.md](docs/GLOSSARY.md)
  - [TODO.md](docs/TODO.md)
- English:
  - [README.md](docs/en/README.md)
  - [NOOB_GUIDE.md](docs/en/NOOB_GUIDE.md)
  - [USAGE_GUIDE.md](docs/en/USAGE_GUIDE.md)
  - [EVALUATION_GUIDE.md](docs/en/EVALUATION_GUIDE.md)
  - [TROUBLESHOOTING.md](docs/en/TROUBLESHOOTING.md)
  - [GLOSSARY.md](docs/en/GLOSSARY.md)
  - [TODO.md](docs/en/TODO.md)

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
- `pixi run mlfx-tui` cho Textual TUI
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
- `download`: tải raw tick data từ Dukascopy
- `qa`: audit raw data để phát hiện gap hoặc dữ liệu bất thường
- `pipeline`: resample → feature engineering → labeling
- `train`: huấn luyện backend đã chọn (kết quả được track và register tự động)
- `evaluate`: chạy backtest và sinh báo cáo
- `serve`: khởi động FastAPI inference server
- `batch-predict`: chạy inference theo lô và ghi kết quả ra parquet
- `drift`: so sánh phân phối feature live vs training để phát hiện drift
- `models`: liệt kê các model version đã đăng ký

## Bắt đầu nhanh

Chạy TUI:

```bash
pixi run mlfx-tui
```

Hoặc chạy hoàn toàn bằng CLI:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx qa --symbol XAUUSD --asset-class fx
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

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

Chi tiết tham số và ví dụ đầy đủ nằm trong [docs/USAGE_GUIDE.md](docs/USAGE_GUIDE.md).

## Cấu trúc dự án (MLOps)

```text
MLFX/
├── mlfx/
│   ├── app/            # CLI và TUI
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
├── docs/               # tài liệu tiếng Việt
├── docs/en/            # tài liệu tiếng Anh
├── data/               # raw, ohlcv, features, labels
├── outputs/
│   ├── models/         # registry.json + {symbol}/{tf}/ (model artifacts)
│   ├── reports/        # {symbol}/{tf}/ (HTML/PNG backtest reports)
│   ├── runs/           # {symbol}/{tf}/ (file-tracker run JSONs)
│   ├── predictions/    # {symbol}/{tf}/ (batch inference results)
│   └── monitoring/     # {symbol}/{tf}/ (drift reference snapshots + alerts)
├── Dockerfile          # multi-stage container image
├── docker-compose.yml  # API server + optional MLflow server
├── config.toml         # giá trị mặc định cho CLI/TUI
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
- dùng `pixi run clean-generated` khi muốn dọn generated artifacts và cache phổ biến trong workspace

## Bước tiếp theo nên đọc

- [docs/NOOB_GUIDE.md](docs/NOOB_GUIDE.md) nếu mới vào repo
- [docs/USAGE_GUIDE.md](docs/USAGE_GUIDE.md) nếu cần chạy từng lệnh cụ thể
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) mô tả kiến trúc MLOps chi tiết
- [docs/EVALUATION_GUIDE.md](docs/EVALUATION_GUIDE.md) nếu muốn hiểu report và metrics
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) nếu đang gặp lỗi môi trường hoặc dữ liệu

## Tác giả

Hieu Nguyen  
GitHub: [@ultimateBroK](https://github.com/ultimateBroK)
