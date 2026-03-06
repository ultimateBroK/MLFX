# ML_FX

ML_FX là dự án phân tích dữ liệu giá và huấn luyện mô hình dự báo hướng giá dựa trên dữ liệu tick, pipeline đặc trưng kỹ thuật, và backtest theo phong cách giao dịch định lượng.

Repo hiện tập trung vào:
- tải dữ liệu tick từ Dukascopy
- resample sang OHLCV nhiều khung thời gian
- tạo đặc trưng từ `ICT Killzone`, `Support/Resistance`, `Pivot Points`, và TA indicators
- gắn nhãn `label_5`, `label_10`, `label_20`
- huấn luyện nhiều backend khác nhau từ TUI hoặc CLI
- chạy backtest và xuất báo cáo vào `outputs/reports`

## Tài liệu

- Tiếng Việt:
  - `README.md`
  - `docs/NOOB_GUIDE.md`
  - `docs/USAGE_GUIDE.md`
  - `docs/EVALUATION_GUIDE.md`
  - `docs/TROUBLESHOOTING.md`
  - `docs/GLOSSARY.md`
  - `docs/TODO.md`
- English:
  - `docs/en/README.md`
  - `docs/en/NOOB_GUIDE.md`
  - `docs/en/USAGE_GUIDE.md`
  - `docs/en/EVALUATION_GUIDE.md`
  - `docs/en/TROUBLESHOOTING.md`
  - `docs/en/GLOSSARY.md`
  - `docs/en/TODO.md`

## Quy trình hiện tại

```text
download_data.py
  -> resample.py
  -> features.py
  -> labels.py
  -> train backend
  -> eval/run_eval.py
  -> outputs/reports
```

Pipeline dữ liệu chính:
- `pipeline/download_data.py`: tải dữ liệu tick về `data/raw/{symbol}/`
- `pipeline/resample.py`: tạo OHLCV vào `data/ohlcv/{symbol}/{tf}/`
- `pipeline/features.py`: tạo feature vào `data/features/{symbol}/{tf}/`
- `pipeline/labels.py`: tạo dữ liệu đã gắn nhãn vào `data/labels/{symbol}/{tf}/`

Các backend huấn luyện hiện có trong TUI:
- `mlf` -> `models/ml_models.py`
- `lstm` -> `models/lstm.py`
- `transformer` -> `models/transformer.py`
- `cnn_lstm` -> `models/cnn_lstm.py`
- `sgd` -> `models/online_sgd.py`
- `stats` -> `models/stats_baseline.py`
- `neuralforecast` -> `models/neural_forecast.py`

Thư mục `agent/` hiện là phần dự kiến cho giai đoạn sau, chưa có implementation hoàn chỉnh để sử dụng như một tính năng chính của repo.

## Cấu trúc dự án

```text
ML_FX/
├── indicators/        # Feature engineering theo ICT, S/R, Pivot Points
├── pipeline/          # Download, resample, features, labels, QA
├── models/            # Các backend huấn luyện hiện tại
├── eval/              # Backtest và tổng hợp đánh giá
├── viz/               # Tạo biểu đồ và báo cáo
├── docs/              # Tài liệu tiếng Việt
├── docs/en/           # Tài liệu tiếng Anh
├── data/              # Raw, OHLCV, features, labels
├── outputs/           # Models và reports được sinh ra
├── main.py            # TUI với 4 tab: Download, Pipeline, Train, Backtest
├── config.toml        # Giá trị mặc định cho TUI
└── pyproject.toml     # Metadata package và dependencies
```

## Bắt đầu nhanh

Yêu cầu thực tế để chạy dự án là dùng `Pixi`. `pyproject.toml` khai báo `requires-python >= 3.11`, còn môi trường Pixi hiện pin Python `3.13`.

```bash
pixi install
pixi run python main.py
```

Phím tắt trong TUI:
- `q`: thoát
- `d`: đổi dark/light mode

Bốn tab chính trong TUI:
- `Download Data`: tải dữ liệu tick
- `Pipeline`: resample, features, labels
- `Train Model`: chọn backend và train
- `Backtest`: chạy mô phỏng trên dữ liệu đã gắn nhãn

## Chạy bằng CLI

Ví dụ một luồng cơ bản:

```bash
pixi run python pipeline/download_data.py --symbol XAUUSD --start-year 2024
pixi run python pipeline/resample.py --symbol XAUUSD --tf 1H
pixi run python pipeline/features.py --symbol XAUUSD --tf 1H
pixi run python pipeline/labels.py --symbol XAUUSD --tf 1H
pixi run python models/ml_models.py --symbol XAUUSD --tf 1H --label label_10
pixi run python eval/run_eval.py --data data/labels/XAUUSD/1H/2024-01.parquet --symbol XAUUSD --tf 1H --label label_10
```

Chi tiết tham số, backend, và ví dụ đầy đủ nằm trong `docs/USAGE_GUIDE.md`.

## Đầu ra

- Models: `outputs/models/{symbol}/{tf}/`
- Reports: `outputs/reports/`
- Dữ liệu trung gian:
  - `data/raw/`
  - `data/ohlcv/`
  - `data/features/`
  - `data/labels/`

## Ghi chú

- README này là điểm vào ngắn gọn.
- Tài liệu thao tác chi tiết nằm trong `docs/`.
- Tài liệu tiếng Anh nằm trong `docs/en/`.

## Tác giả

Hieu Nguyen  
GitHub: [@ultimateBroK](https://github.com/ultimateBroK)
