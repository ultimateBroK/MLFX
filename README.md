# ML_FX

`ML_FX` là một pipeline MLOps nghiên cứu dữ liệu thị trường, tập trung vào 5 giai đoạn chính:
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

## Luồng vận hành chuẩn

```text
download
  -> qa
  -> pipeline
  -> train
  -> evaluate
```

Ý nghĩa từng bước:
- `download`: tải raw tick data
- `qa`: audit raw data để phát hiện gap hoặc dữ liệu bất thường
- `pipeline`: tạo OHLCV, feature và label
- `train`: huấn luyện backend đã chọn
- `evaluate`: chạy backtest và sinh báo cáo

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

- `mlf`
- `lstm`
- `transformer`
- `cnn_lstm`
- `sgd`
- `stats`
- `neuralforecast`

Chi tiết tham số và ví dụ đầy đủ nằm trong [docs/USAGE_GUIDE.md](docs/USAGE_GUIDE.md).

## Cấu trúc dự án

```text
ML_FX/
├── mlfx/
│   ├── app/           # CLI và TUI
│   ├── config/        # path policy và config loader
│   ├── ingestion/     # downloader Dukascopy
│   ├── pipeline/      # qa, resampling, feature engineering, labeling
│   ├── features/      # feature modules theo domain
│   ├── training/      # dataset loading, persistence, backend registry
│   └── evaluation/    # backtest, reporting, evaluation runner
├── docs/              # tài liệu tiếng Việt
├── docs/en/           # tài liệu tiếng Anh
├── data/              # raw, ohlcv, features, labels
├── outputs/           # model artifacts và reports
├── logs/              # log hoặc artifact tạm nếu cần
├── config.toml        # giá trị mặc định cho CLI/TUI
└── pyproject.toml     # package metadata, Pixi config, tasks
```

## Artifacts chính

- `data/raw/{symbol}/`: raw tick data và file state download
- `data/ohlcv/{symbol}/{tf}/`: parquet sau resample
- `data/features/{symbol}/{tf}/`: parquet đã thêm feature
- `data/labels/{symbol}/{tf}/`: parquet đã gắn nhãn
- `outputs/models/{symbol}/{tf}/`: model artifacts, metrics, metadata train
- `outputs/reports/`: HTML/PNG reports từ evaluate

## Chính sách cleanup

- `data/raw/` nên được giữ lại nếu muốn tái tạo pipeline mà không tải lại dữ liệu
- `data/ohlcv/`, `data/features/`, `data/labels/`, `outputs/`, `lightning_logs/`, `.pixi-cache/`, `.cache/` là phần có thể tái sinh
- dùng `pixi run clean-generated` khi muốn dọn generated artifacts và cache phổ biến trong workspace

## Bước tiếp theo nên đọc

- [docs/NOOB_GUIDE.md](docs/NOOB_GUIDE.md) nếu mới vào repo
- [docs/USAGE_GUIDE.md](docs/USAGE_GUIDE.md) nếu cần chạy từng lệnh cụ thể
- [docs/EVALUATION_GUIDE.md](docs/EVALUATION_GUIDE.md) nếu muốn hiểu report và metrics
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) nếu đang gặp lỗi môi trường hoặc dữ liệu

## Tác giả

Hieu Nguyen  
GitHub: [@ultimateBroK](https://github.com/ultimateBroK)
