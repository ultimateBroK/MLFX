# Báo cáo Tổng quan Dự án MLFX

**Ngày lập:** Tháng 3/2026  
**Tác giả:** Hieu Nguyen (@ultimateBroK)  
**Phiên bản:** 0.1.0

---

## Mục lục

1. [Mục tiêu và Phạm vi](#1-mục-tiêu-và-phạm-vi)
2. [Kiến trúc Tổng thể](#2-kiến-trúc-tổng-thể)
3. [Công nghệ và Thư viện](#3-công-nghệ-và-thư-viện)
4. [Hướng dẫn Vận hành Cơ bản](#4-hướng-dẫn-vận-hành-cơ-bản)
5. [Artifact Đầu ra Chính](#5-artifact-đầu-ra-chính)
6. [Vấn đề Hiện tại và Hướng Phát triển](#6-vấn-đề-hiện-tại-và-hướng-phát-triển)
7. [Điểm mạnh và Điểm yếu](#7-điểm-mạnh-và-điểm-yếu)
8. [Kết luận](#8-kết-luận)

---

## 1. Mục tiêu và Phạm vi

### 1.1 Mục tiêu

MLFX (Machine Learning _ Forex) là một pipeline MLOps nghiên cứu dữ liệu thị trường tài chính, được thiết kế với triết lý **hobby-first**, tập trung vào thử nghiệm và học hỏi hơn là triển khai production.

**Mục tiêu chính:**
- Xây dựng pipeline end-to-end từ thu thập dữ liệu đến đánh giá mô hình
- Hỗ trợ nhiều backend huấn luyện (LightGBM, LSTM, Transformer, CNN-LSTM, ...)
- Cung cấp công cụ phân tích kỹ thuật và feature engineering phong phú
- Tạo báo cáo backtest trực quan và chi tiết

### 1.2 Phạm vi

**Trong phạm vi:**
- Tải tick data lịch sử từ Dukascopy
- Chuẩn hóa thành OHLCV theo nhiều timeframe
- Sinh feature kỹ thuật (TA) và feature theo ngữ cảnh ICT
- Gắn nhãn (label) phục vụ huấn luyện phân loại
- Train, evaluate và xuất báo cáo backtest
- Serving real-time (FastAPI) và batch inference
- Drift detection cơ bản

**Ngoài phạm vi:**
- Live trading / execution
- Paper trading real-time
- Production-grade reliability

---

## 2. Kiến trúc Tổng thể

### 2.1 Sơ đồ Luồng MLOps Pipeline

```
┌────────────┐    ┌─────┐    ┌──────────┐    ┌───────┐    ┌──────────┐
│  DOWNLOAD  │───►│ QA  │───►│ PIPELINE │───►│ TRAIN │───►│ EVALUATE │
└────────────┘    └─────┘    └──────────┘    └───────┘    └──────────┘
    │                            │               │              │
    │                            │               │              │
    ▼                            ▼               ▼              ▼
data/raw/                  data/ohlcv/      tracking/      reports/
                           data/features/   registry/
                           data/labels/         │
                                               ▼
                                        ┌────────────┐
                                        │   SERVE    │
                                        │   BATCH    │
                                        │   DRIFT    │
                                        └────────────┘
```

### 2.2 Các Module Chính

| Module | Vị trí | Chức năng |
|--------|--------|-----------|
| **app** | `mlfx/app/` | CLI (argparse + Rich) — terminal-first workflow |
| **config** | `mlfx/config/` | Path policy và config loader |
| **ingestion** | `mlfx/ingestion/` | Downloader Dukascopy (async HTTP) |
| **pipeline** | `mlfx/pipeline/` | QA, resampling, feature engineering, labeling; `runner.py` orchestrates all stages |
| **features** | `mlfx/features/` | Feature modules theo domain (indicators) |
| **training** | `mlfx/training/` | Backend implementations, runner, registry |
| **evaluation** | `mlfx/evaluation/` | Backtest, reporting, metrics computation |
| **tracking** | `mlfx/tracking/` | Experiment tracking (MLflow / file-based) |
| **registry** | `mlfx/registry/` | Model registry (JSON-backed) |
| **serving** | `mlfx/serving/` | FastAPI real-time API (`api.py`, `inference.py`, `torch_adapters.py`) + batch inference |
| **monitoring** | `mlfx/monitoring/` | Drift detection (KS + PSI) + structured logging |

### 2.3 Chi tiết Luồng Dữ liệu

```
Dukascopy API
    │  (async HTTP, bi5 decompression)
    ▼
data/raw/{symbol}/
    YYYY-MM.parquet          ← tick data (timestamp, bid, ask, volumes)
    completed_months.json    ← download state

    │  resample_symbol_tf()
    ▼
data/ohlcv/{symbol}/{tf}/
    YYYY-MM.parquet          ← OHLCV + tick_count

    │  run_feature_pipeline()
    ▼
data/features/{symbol}/{tf}/
    YYYY-MM.parquet          ← OHLCV + all technical indicators

    │  run_label_pipeline()
    ▼
data/labels/{symbol}/{tf}/
    YYYY-MM.parquet          ← features + label_5, label_10, label_20
```

### 2.4 Training Architecture

```
TrainingConfig (dataclass)
        │
        ▼
runner.run_training()
        │
        ├── registry.get_backend_runner(config.backend)
        │           │ (dynamic import via BACKEND_REGISTRY)
        │     ┌─────┴───────────────────────────────────────────┐
        │     │          mlfx.training.backends/                │
        │     │  mlforecast.py  lstm.py  bilstm.py  ...         │
        │     │  transformer.py  cnn_lstm.py  online_sgd.py     │
        │     │  stats.py  neuralforecast.py                    │
        │     └─────────────────────────────────────────────────┘
        │
        ├── tracking.tracker  (log params + metrics)
        └── registry.models   (register artifact)
```

---

## 3. Công nghệ và Thư viện

### 3.1 Core Dependencies

| Category | Thư viện | Phiên bản | Mục đích |
|----------|----------|-----------|----------|
| **Package Management** | Pixi | - | Workflow management, environment |
| **Data Processing** | Polars | >=1.38.1 | DataFrame operations (fast, memory-efficient) |
| **Data Processing** | PyArrow | >=23.0.1 | Parquet I/O |
| **Data Processing** | Pandas | >=2.0.0 | Compatibility với một số thư viện |
| **Technical Analysis** | TA-Lib | >=0.6.4 | Indicators (RSI, MACD, ATR, EMA, ...) |

### 3.2 ML/DL Frameworks

| Thư viện | Phiên bản | Backend |
|----------|-----------|---------|
| LightGBM | >=4.6.0 | `mlf` (via MLForecast) |
| PyTorch | >=2.10 (CPU) | `lstm`, `bilstm`, `transformer`, `cnn_lstm` |
| Lightning | >=2.6.1 | Training orchestration for PyTorch |
| scikit-learn | >=1.8.0 | `sgd` (SGDClassifier) |
| XGBoost | >=3.2 | Alternative tree-based |
| Optuna | >=4.7 | Hyperparameter optimization |
| SHAP | >=0.50 | Feature importance |
| MLForecast | >=1.0.2 | Time-series ML wrapper |
| StatsForecast | >=2.0.3 | `stats` (AutoARIMA, SeasonalNaive) |
| NeuralForecast | >=3.1.5 | `neuralforecast` (NHiTS, NBEATS) |

### 3.3 Visualization

| Thư viện | Phiên bản | Mục đích |
|----------|-----------|----------|
| Plotly | >=6.5.2 | Interactive charts |
| Matplotlib | >=3.10.8 | Static charts |
| Seaborn | >=0.13.2 | Statistical visualization |
| Rich | >=14.3.3 | Console formatting |

### 3.4 API & Serving

| Thư viện | Phiên bản | Mục đích |
|----------|-----------|----------|
| FastAPI | >=0.135.1 | REST API server |
| Uvicorn | >=0.41.0 | ASGI server |
| Pydantic | >=2.12.5 | Data validation |
| aiohttp | >=3.9 | Async HTTP (downloader) |

### 3.5 Optional Integrations

| Thư viện | Mục đích |
|----------|----------|
| QuestDB | Time-series database |
| ChromaDB | Vector database |
| OpenAI | LLM integration |
| LMStudio | Local LLM |
| Agno | Agent framework |

---

## 4. Hướng dẫn Vận hành Cơ bản

### 4.1 Cài đặt Môi trường

```bash
# Cài Pixi (nếu chưa có)
curl -fsSL https://pixi.sh/install.sh | bash

# Cài đặt dependencies
pixi install
```

### 4.2 Workflow 4 Bước Chính

```bash
# Bước 1: Tải dữ liệu tick từ Dukascopy
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024

# Bước 2: Chạy pipeline (resample → features → labels)
pixi run mlfx pipeline --symbol XAUUSD --tf 1H

# Bước 3: Train model
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf

# Bước 4: Evaluate và xem báo cáo backtest
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

### 4.3 Entrypoint Chính

| Lệnh | Mô tả |
|------|-------|
| `pixi run mlfx` | CLI hợp nhất (terminal-first workflow) |
| `pixi run test` | Chạy test suite |
| `pixi run verify` | Chạy smoke/contract tests |
| `pixi run clean-generated` | Dọn cache và artifacts |

### 4.4 Các Lệnh Nâng cao

```bash
# Audit dữ liệu raw
pixi run mlfx qa --symbol XAUUSD --asset-class fx

# Benchmark nhiều backend cùng lúc
pixi run mlfx benchmark --backends mlf bilstm lstm --n-trials 10

# Xem model registry
pixi run mlfx models --symbol XAUUSD --tf 1H

# Batch predict
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H --label label_10

# Serving API
pixi run mlfx serve --port 8000

# Drift detection
pixi run mlfx drift --symbol XAUUSD --tf 1H
```

---

## 5. Artifact Đầu ra Chính

### 5.1 Cấu trúc Thư mục

```
MLFX/
├── data/
│   ├── raw/{symbol}/                ← tick data + state
│   │   ├── YYYY-MM.parquet
│   │   └── completed_months.json
│   ├── ohlcv/{symbol}/{tf}/         ← OHLCV sau resample
│   ├── features/{symbol}/{tf}/      ← features đã tính
│   └── labels/{symbol}/{tf}/        ← labels đã gắn
│
├── outputs/
│   ├── models/
│   │   ├── registry.json            ← model metadata
│   │   └── {symbol}/{tf}/           ← model artifacts
│   ├── reports/{symbol}/{tf}/       ← backtest reports
│   │   ├── *_candlestick.html
│   │   ├── *_equity.png
│   │   └── *_heatmap.png
│   ├── predictions/{symbol}/{tf}/   ← batch inference results
│   ├── runs/{symbol}/{tf}/          ← experiment tracking JSONs + metrics_log.jsonl
│   └── monitoring/{symbol}/{tf}/    ← drift reference + alerts
│
└── logs/                            ← structured JSON logs
```

### 5.2 Chi tiết Artifacts theo Giai đoạn

| Giai đoạn | Artifact | Vị trí |
|-----------|----------|---------|
| Download | tick data parquet | `data/raw/{symbol}/YYYY-MM.parquet` |
| Download | download state | `data/raw/{symbol}/completed_months.json` |
| QA | quality report | `data/raw/{symbol}/{symbol}_Data_Quality_Report.md` |
| Pipeline | OHLCV | `data/ohlcv/{symbol}/{tf}/` |
| Pipeline | Features | `data/features/{symbol}/{tf}/` |
| Pipeline | Labels | `data/labels/{symbol}/{tf}/` |
| Train | Model artifacts | `outputs/models/{symbol}/{tf}/` |
| Train | Registry entry | `outputs/models/registry.json` |
| Evaluate | Candlestick HTML | `outputs/reports/{symbol}/{tf}/*_candlestick.html` |
| Evaluate | Equity curve PNG | `outputs/reports/{symbol}/{tf}/*_equity.png` |
| Evaluate | Session heatmap PNG | `outputs/reports/{symbol}/{tf}/*_heatmap.png` |
| Benchmark | Summary JSON | `outputs/reports/{symbol}/{tf}/benchmark_{timestamp}.json` |
| Batch-predict | Predictions | `outputs/predictions/{symbol}/{tf}/` |

---

## 6. Vấn đề Hiện tại và Hướng Phát triển

### 6.1 Năng lực Hiện có (✓)

- [x] CLI hợp nhất `mlfx` (terminal-first, argparse + Rich)
- [x] Downloader dữ liệu từ Dukascopy
- [x] QA, resample, feature engineering, labeling pipeline
- [x] 8 training backends (mlf, lstm, bilstm, transformer, cnn_lstm, sgd, stats, neuralforecast)
- [x] Benchmark command để so sánh nhiều backend
- [x] Backtest và reporting
- [x] Experiment tracking (MLflow / file-based fallback)
- [x] Model registry (JSON-backed)
- [x] FastAPI serving + batch inference
- [x] Drift detection cơ bản
- [x] Metrics export (metrics_log.jsonl) cho monitoring
- [x] Workflow phát triển chuẩn qua Pixi

### 6.2 Vấn đề Cần Giải quyết

| Ưu tiên | Vấn đề | Trạng thái |
|---------|--------|------------|
| ~~Cao~~ | ~~`bilstm` chưa expose ở CLI~~ | ✓ Đã expose qua `--backend bilstm` |
| ~~Trung bình~~ | ~~Thiếu benchmark thống nhất~~ | ✓ Đã thêm `mlfx benchmark` command |
| ~~Trung bình~~ | ~~Test end-to-end chưa đủ~~ | ✓ Đã có test e2e với synthetic data |
| ~~Thấp~~ | ~~Export metrics/summary cho monitoring~~ | ✓ Đã thêm `metrics_log.jsonl` |

### 6.3 Hướng Phát triển Tiếp theo

1. **Nếu mục tiêu là so sánh mô hình:**
   - ✓ Đã có benchmark command (`mlfx benchmark --backends mlf bilstm lstm`)
   - Chuẩn hóa metrics cross-backend

2. **Nếu mục tiêu là ổn định vận hành:**
   - ✓ Đã có test e2e với synthetic data
   - ✓ Đã có metrics export (metrics_log.jsonl)

3. **Nếu mục tiêu là mở rộng thử nghiệm:**
   - ✓ Đã expose tất cả 8 backends ra CLI
   - Thêm backend mới (e.g., attention-based)

---

## 7. Điểm mạnh và Điểm yếu

### 7.1 Điểm mạnh

| Khía cạnh | Chi tiết |
|-----------|----------|
| **Architecture** | Thiết kế modular, separation of concerns tốt |
| **MLOps Coverage** | Pipeline end-to-end từ ingestion → serving |
| **Backend Diversity** | 8 backend đa dạng (statistical → DL) |
| **Feature Engineering** | Phong phú: TA indicators, ICT concepts (Order Blocks, FVG, Killzones, SR/Pivot) |
| **Documentation** | Tài liệu song ngữ (Việt + English) |
| **DX (Developer Experience)** | Pixi-first workflow, CLI với help chi tiết |
| **Extensibility** | Backend registry cho phép thêm backend mới dễ dàng |
| **Testing** | Contract tests, integration tests có sẵn |
| **Lazy Loading** | Backend import lazy để tránh load heavy deps không cần thiết |

### 7.2 Điểm yếu

| Khía cạnh | Chi tiết | Đề xuất Cải thiện |
|-----------|----------|-------------------|
| **Production Readiness** | Thiết kế hobby-first, chưa sẵn sàng cho production | Nếu cần production, thêm retry logic, circuit breaker |
| **Hyperparameter** | `n_trials` chỉ có ý nghĩa với `mlf`, mapping không nhất quán | Chuẩn hóa config interface |
| **Feature Selection** | Feature selection chưa tự động | Thêm auto feature selection pipeline |
| **Live Data** | Chỉ hỗ trợ historical data | Thêm live data adapter |
| **Scalability** | Chưa tối ưu cho dataset lớn (>10GB) | Thêm chunked processing |
| **Model Versioning** | JSON-backed registry đơn giản | Nâng cấp lên MLflow registry hoặc DVC |

### 7.3 Đánh giá Tổng quan

```
┌─────────────────────────────────────────────────────────────┐
│                    MLFX Maturity Assessment                 │
├─────────────────────────────────────────────────────────────┤
│ Data Pipeline        ████████████████████░░░░ 80%           │
│ Feature Engineering  ███████████████████████░ 92%           │
│ Training             ████████████████████░░░░ 80%           │
│ Evaluation           ███████████████████████░ 92%           │
│ Serving              ████████████████░░░░░░░░ 64%           │
│ Monitoring           ████████████░░░░░░░░░░░░ 48%           │
│ Documentation        ███████████████████████░ 92%           │
│ Testing              ████████████████████░░░░ 80%           │
│ Production Readiness ████████░░░░░░░░░░░░░░░░ 32%           │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Kết luận

### 8.1 Tóm tắt

MLFX là một dự án MLOps pipeline hoàn chỉnh cho nghiên cứu dữ liệu thị trường FX, với:
- **5 giai đoạn chính:** Download → QA → Pipeline → Train → Evaluate
- **8 training backends** đa dạng từ statistical đến deep learning
- **Feature engineering phong phú** bao gồm cả ICT trading concepts
- **CLI terminal-first** với help chi tiết và benchmark command

### 8.2 Khuyến nghị

**Cho việc sử dụng:**
- Sử dụng `pixi run mlfx --help` để xem các lệnh có sẵn
- Workflow 4 bước là đủ cho hầu hết use cases
- Backend `mlf` là lựa chọn mặc định tốt (nhanh, ổn định)
- Dùng `mlfx benchmark` để so sánh nhiều backend cùng lúc

**Cho việc phát triển:**
1. **Ngắn hạn:** Mở rộng test coverage, fixture dataset nhỏ hơn
2. **Trung hạn:** Chuẩn hóa hyperparameter interface, thêm backend mới
3. **Dài hạn:** Nếu cần production, xem xét refactor serving layer

### 8.3 Tài liệu Tham khảo

- [README.md](../README.md) - Tổng quan nhanh
- [NOOB_GUIDE.md](NOOB_GUIDE.md) - Hướng dẫn người mới
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Hướng dẫn chi tiết
- [ARCHITECTURE.md](ARCHITECTURE.md) - Kiến trúc kỹ thuật
- [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) - Hướng dẫn đánh giá
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Xử lý sự cố
- [GLOSSARY.md](GLOSSARY.md) - Thuật ngữ

---

*Báo cáo này được tạo như tài liệu tham khảo để đánh giá, thêm bớt và tối ưu dự án MLFX.*
