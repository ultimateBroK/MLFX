# Kiến trúc MLFX

Tài liệu này mô tả kiến trúc MLOps tổng thể của dự án MLFX, bao gồm các mô-đun, luồng dữ liệu và các quyết định thiết kế quan trọng.

---

## Tổng quan (C4 Context)

```text
[Người dùng / Nhà nghiên cứu]
        │
        ▼
┌─────────────────────────────────┐
│          Hệ thống MLFX          │
│   (nạp dữ liệu → xử lý →        │
│    huấn luyện → đánh giá →      │
│    phục vụ → giám sát)          │
└─────────────────────────────────┘
        │
        ├── API Dukascopy        (nguồn dữ liệu tick)
        ├── Hệ thống tệp cục bộ  (data/*, outputs/*)
        └── MLflow Server        (theo dõi thí nghiệm, tùy chọn)
```

---

## Tầng dữ liệu

### Luồng dữ liệu

```text
Dukascopy API
    │  (HTTP bất đồng bộ, giải nén bi5)
    ▼
data/raw/{symbol}/
    YYYY-MM.parquet          ← dữ liệu tick (timestamp, bid, ask, volumes)
    completed_months.json    ← trạng thái tải dữ liệu

    │  resample_symbol_tf()
    ▼
data/ohlcv/{symbol}/{tf}/
    YYYY-MM.parquet          ← OHLCV + tick_count

    │  run_feature_pipeline()
    ▼
data/features/{symbol}/{tf}/
    YYYY-MM.parquet          ← OHLCV + toàn bộ chỉ báo kỹ thuật

    │  run_label_pipeline()
    ▼
data/labels/{symbol}/{tf}/
    YYYY-MM.parquet          ← đặc trưng + label_5, label_10, label_20
```

### Chính sách quản lý đường dẫn

Tất cả đường dẫn được quản lý qua `mlfx.config.paths.ProjectPaths` (`dataclass` bất biến). Không có đường dẫn nào bị ghi cứng bên ngoài mô-đun này.

```python
from mlfx.config.paths import DEFAULT_PATHS

paths = DEFAULT_PATHS                         # hoặc ProjectPaths(project_root=...)
in_dir = paths.features_dir("XAUUSD", "1H")  # data/features/XAUUSD/1H/
```

---

## Tầng xây dựng đặc trưng

Điểm vào duy nhất: `mlfx.pipeline.features.run_feature_pipeline()`.

Các nhóm đặc trưng được bổ sung:

| Nhóm | Hàm | Cột đầu ra |
|---|---|---|
| Chỉ báo kỹ thuật | `add_ta_features()` | `rsi_14`, `macd`, `macd_signal`, `atr_14`, `ema_*` |
| Phiên khung giờ trọng điểm | `add_killzone_features()` | `is_london`, `is_ny`, `is_asian` |
| Hỗ trợ / kháng cự và các mức điểm xoay | `add_sr_pp_features()` | `pp`, `r1`–`r4`, `s1`–`s4` (traditional/fibonacci) |
| Chuẩn hóa | `add_normalized_features()` | các biến thể `*_norm` |

---

## Tầng huấn luyện

### Kiến trúc

```text
TrainingConfig (dataclass)
        │
        ▼
runner.run_training()
        │
        ├── registry.get_backend_runner(config.backend)
        │           │ (nạp động qua BACKEND_REGISTRY)
        │     ┌─────┴───────────────────────────────────────────┐
        │     │          mlfx.training.backends/               │
        │     │  mlf.py  lstm.py  sgd.py  stats.py              │
        │     │  (mỗi bộ máy import data.py,                    │
        │     │   feature_selection.py, artifacts.py để dùng    │
        │     │   lại các helper chung)                         │
        │     └─────────────────────────────────────────────────┘
        │
        ├── tracking.tracker  (ghi params + metrics)
        └── registry.models   (đăng ký tệp đầu ra)
```

### Bố cục mô-đun huấn luyện

```text
mlfx/training/
├── backends/               ← Các phần cài đặt (vị trí chuẩn)
│   ├── __init__.py
│   ├── _pytorch_common.py  ← Tiện ích PyTorch dùng chung cho bộ máy học sâu
│   ├── _sequence_utils.py  ← Helper chuẩn bị chuỗi cho bộ máy học sâu
│   ├── base.py             ← BackendRunner protocol, TrainingConfig, TrainResult
│   ├── mlf.py              ← LightGBM qua MLForecast   (key: "mlf")
│   ├── lstm.py             ← PyTorch LSTM              (key: "lstm")
│   ├── sgd.py              ← Sklearn SGD               (key: "sgd")
│   ├── stats.py            ← Baseline StatsForecast    (key: "stats")
├── __init__.py             ← Tái xuất public từ data/feature_selection/artifacts
├── _utils.py               ← Tiện ích nội bộ
├── artifacts.py            ← Helper lưu mô hình (chuẩn)
├── config.py               ← Alias public cho TrainingConfig / TrainResult
├── data.py                 ← Helper nạp dữ liệu (chuẩn)
├── evaluation.py           ← Helper đánh giá mô hình
├── feature_selection.py    ← Helper chọn đặc trưng (chuẩn)
├── registry.py             ← BACKEND_REGISTRY: key → (module, function)
└── runner.py               ← Bộ điều phối cấp cao
```

### Giao diện bộ máy

Mọi bộ máy phải triển khai chữ ký tương thích với `BackendRunner`:

```python
def run_xxx(
    symbol: str,
    tf: str,
    label: str,
    force: bool,
    **kwargs,
) -> dict:
```

Các bộ máy được ánh xạ trong `mlfx.training.registry.BACKEND_REGISTRY`, dùng lazy import để tránh nạp các phụ thuộc nặng khi chỉ dùng những phần nhẹ hơn.

### Cấu hình huấn luyện

```python
from mlfx.training.config import TrainingConfig

cfg = TrainingConfig(
    symbol="XAUUSD",
    tf="1H",
    backend="mlf",
    n_trials=15,
    n_splits=5,
)
```

---

## Theo dõi thí nghiệm

Mô-đun `mlfx.tracking` cung cấp giao diện theo dõi thống nhất với tích hợp MLflow:

```text
mlfx/tracking/
├── __init__.py       ← Các xuất public
├── context.py        ← ExperimentContext, workflow_context cho lồng run
└── tracker.py        ← BaseTracker, FileTracker, MlflowTracker, get_tracker()
```

### Các bộ máy theo dõi

| Bộ máy | Điều kiện | Nơi lưu |
|---|---|---|
| `MlflowTracker` | đã cài `mlflow` | MLflow server (backend SQLite: `mlflow.db`) |
| `FileTracker` | phương án dự phòng mặc định | `outputs/runs/{symbol}/{tf}/*.json` |

### Cách sử dụng

Tracking được gọi tự động bên trong `runner.run_training()`. Muốn tắt:

```python
run_training(cfg, enable_tracking=False)
```

Truy cập qua chương trình:

```python
from mlfx.tracking import get_tracker, experiment_context

tracker = get_tracker()
run_id = tracker.start_run("my_run", params={"lr": 0.01})
tracker.log_metrics(run_id, {"f1": 0.72})
tracker.end_run(run_id)

# Context manager cho các run lồng nhau
with experiment_context("experiment_name", symbol="XAUUSD", tf="1H"):
    # Mã huấn luyện ở đây
    pass
```

---

## Sổ đăng ký mô hình

Mô-đun `mlfx.registry` cung cấp hỗ trợ sổ đăng ký kép cho việc theo dõi các tệp đầu ra mô hình đã huấn luyện:

```text
mlfx/registry/
├── __init__.py           ← Các xuất public, factory get_registry()
├── models.py             ← ModelRegistry (dựa trên JSON)
└── mlflow_registry.py    ← MlflowModelRegistry (dựa trên MLflow)
```

### Các backend sổ đăng ký

| Backend | Hàm | Nơi lưu |
|---|---|---|
| `MlflowModelRegistry` | `get_registry(use_mlflow=True)` | MLflow Model Registry |
| `ModelRegistry` | `get_registry(use_mlflow=False)` | `outputs/models/registry.json` |

### Cách sử dụng

```python
from mlfx.registry import get_registry

# Dùng MLflow registry khi có sẵn (mặc định)
reg = get_registry(use_mlflow=True)

# Hoặc dùng JSON registry một cách rõ ràng
reg = get_registry(use_mlflow=False)

# Truy vấn mô hình tốt nhất
best = reg.best_model(symbol="XAUUSD", tf="1H", metric="best_cv_f1_macro")
```

Kết quả trả về có dạng:

```json
{"backend": "mlf", "artifact_path": "...", "metrics": {...}}
```

Sổ đăng ký tự động quay về dùng JSON nếu MLflow chưa được cài đặt.

---

## Tầng đánh giá

```text
load_labelled_dataset()
        │
        ▼
simulate_trades()      ← tín hiệu → vào/ra lệnh với TP/SL/TIME
        │
        ▼
compute_metrics()      ← win_rate, sharpe, sortino, calmar, profit_factor, ...
        │
        ▼
generate_full_report() ← HTML nến + PNG đường vốn + PNG heatmap theo phiên
```

---

## Tầng phục vụ mô hình

### Thời gian thực (FastAPI)

```text
POST /predict
  body: {symbol, tf, label, features: {col: value}}
  → nạp mô hình tốt nhất từ registry
  → chạy suy luận
  → trả về {prediction, confidence}
```

Khởi động:

```bash
pixi run mlfx serve --port 8000
# hoặc
docker-compose up api
```

Bố cục mô-đun phục vụ:

```text
mlfx/serving/
├── __init__.py
├── api.py            ← FastAPI app (GET /health, GET /models, POST /predict)
├── batch.py          ← Bộ chạy suy luận theo lô
├── core.py           ← Tiện ích dùng chung cho lớp phục vụ
├── features.py       ← Chuẩn bị đặc trưng cho suy luận
├── inference.py      ← Nạp mô hình và dự đoán
└── torch_adapters.py ← Bộ điều hợp mô hình PyTorch cho lớp phục vụ
```

### Theo lô

```bash
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H
# → outputs/predictions/XAUUSD/1H/label_10/predictions.parquet
```

---

## Giám sát

### Độ lệch đặc trưng

1. Sau khi huấn luyện: `save_reference(train_df, feature_cols, symbol, tf)` → `outputs/monitoring/{symbol}/{tf}/`
2. Theo chu kỳ: `DriftDetector.load(symbol, tf).detect(live_df)` → KS-test + PSI

```bash
pixi run mlfx drift --symbol XAUUSD --tf 1H
# Tùy chỉnh ngưỡng:
pixi run mlfx drift --symbol XAUUSD --tf 1H --threshold-ks 0.1 --threshold-psi 0.2
```

### Tích hợp MLflow

Cả `save_reference()` và `detect()` đều hỗ trợ ghi log tự động vào MLflow:

```python
from mlfx.monitoring.drift import DriftDetector, save_reference

# Ghi mốc tham chiếu vào MLflow
save_reference(train_df, feature_cols, "XAUUSD", "1H", log_to_mlflow=True)

# Ghi kết quả phát hiện độ lệch vào MLflow
detector = DriftDetector.load("XAUUSD", "1H")
report = detector.detect(live_df, log_to_mlflow=True)
```

Khi MLflow có sẵn, các chỉ số độ lệch và artifact sẽ tự động được ghi vào thí nghiệm `mlfx/monitoring/drift`.

### Ghi nhật ký có cấu trúc

Mọi log được xuất dưới dạng JSON lines khi chạy qua CLI:

```json
{"timestamp": "2025-01-01T10:00:00Z", "level": "INFO", "logger": "mlfx.training.runner",
 "message": "Training complete", "backend": "mlf", "elapsed_seconds": 45.2}
```

---

## Hệ thống cấu hình

### Luồng nạp cấu hình

```text
config.toml
    │
    ▼
mlfx.config.schema.ServingSettings
    │
    ▼
Lệnh CLI đọc giá trị mặc định từ config
    │
    ▼
Cờ CLI sẽ ghi đè giá trị từ config
```

Hệ thống cấu hình dùng Pydantic để kiểm tra hợp lệ:

```python
from mlfx.config.schema import ServingSettings

# Nạp từ config.toml + biến môi trường
settings = ServingSettings()
```

Biến môi trường có thể ghi đè:
- `MLFX_DATA_ROOT` — ghi đè thư mục dữ liệu
- `MLFX_OUTPUTS_ROOT` — ghi đè thư mục outputs

### Cấu hình MLflow

Mô-đun `mlfx.config.mlflow` cung cấp cấu hình MLflow tập trung:

```python
from mlfx.config.mlflow import get_mlflow_config

config = get_mlflow_config()
config.setup_mlflow()  # Cấu hình MLflow với cài đặt dự án
```

**Các tùy chọn cấu hình:**

| Cài đặt | Mặc định | Mô tả |
|---|---|---|
| Tracking URI | `sqlite:///mlflow.db` | URI máy chủ theo dõi MLflow |
| Artifact Root | `outputs/mlflow_artifacts/` | Thư mục gốc cho artifact |
| Experiment Prefix | `mlfx` | Tiền tố cho tên thí nghiệm |

**Ghi đè bằng biến môi trường:**

| Biến | Mô tả |
|---|---|---|
| `MLFLOW_TRACKING_URI` | Ghi đè URI máy chủ theo dõi (ví dụ: `http://localhost:5000`) |
| `MLFLOW_ARTIFACT_ROOT` | Ghi đè đường dẫn lưu artifact |
| `MLFLOW_REGISTRY_URI` | Ghi đè URI sổ đăng ký mô hình |

**Quy ước đặt tên thí nghiệm:**

```python
# Tạo: mlfx/XAUUSD/1H/label_10
experiment_name = config.experiment_name(symbol="XAUUSD", tf="1H", label="label_10")

# Tạo: mlfx-XAUUSD-1H-label_10
model_name = config.model_name(symbol="XAUUSD", tf="1H", label="label_10")
```

---

## Điều phối quy trình làm việc

### Mô-đun Workflow

Mô-đun `mlfx.workflow/` cung cấp khả năng điều phối từ đầu đến cuối:

```text
mlfx/workflow/
├── __init__.py           ← Các xuất public
├── results.py            ← StageResult, WorkflowResult, persist_workflow_result()
├── stages.py             ← Các runner giai đoạn riêng lẻ (run_download, run_train, v.v.)
├── stage.py              ← Tiện ích thực thi giai đoạn
└── result.py             ← Các định nghĩa kiểu kết quả
```

### Các giai đoạn quy trình

Lệnh `run-all` thực thi các giai đoạn theo trình tự:

```text
Giai đoạn 1: download    → data/raw/{symbol}/
Giai đoạn 2: pipeline    → data/ohlcv/, data/features/, data/labels/
Giai đoạn 3: train       → outputs/models/{symbol}/{tf}/{label}/
Giai đoạn 4: evaluate    → outputs/reports/{symbol}/{tf}/{label}/
```

Mỗi giai đoạn có thể bỏ qua độc lập qua các cờ:
- `--skip-download`
- `--skip-pipeline`
- `--skip-train`
- `--skip-evaluate`

### Kết quả giai đoạn

Mỗi giai đoạn trả về một `StageResult` với đầu ra có cấu trúc:

```python
from mlfx.workflow import StageResult, WorkflowResult, persist_workflow_result

# Kết quả giai đoạn chứa trạng thái, thời lượng và đường dẫn đầu ra
result: StageResult = run_train(symbol="XAUUSD", tf="1H", label="label_10")

# Kết quả quy trình tổng hợp tất cả giai đoạn
workflow_result = WorkflowResult(
    stages=[download_result, pipeline_result, train_result, evaluate_result],
    total_duration=120.5
)

# Lưu thành JSON để tích hợp CI/CD
persist_workflow_result(workflow_result, path="outputs/runs/workflow_result.json")
```

### Hệ thống hồ sơ

Hồ sơ quy trình cho phép định nghĩa cấu hình đặt trước cho các thí nghiệm có thể tái tạo:

```toml
[profiles.research.train]
symbol      = "XAUUSD"
tf          = "1H"
label       = "label_10"
backend     = "mlf"
train_start = "20240101"
train_end   = "20241231"
n_trials    = 5

[profiles.research.evaluate]
symbol          = "XAUUSD"
tf              = "1H"
label           = "label_10"
eval_start      = "20250101"
eval_end        = "20250331"
tp_r            = 1.5
sl_r            = 1.0
initial_capital = 10000.0
```

Cách sử dụng hồ sơ:

```bash
# Liệt kê các hồ sơ có sẵn
pixi run mlfx profiles

# Chạy train + evaluate từ hồ sơ
pixi run mlfx run-profile --profile research

# Dùng hồ sơ cho từng lệnh riêng lẻ
pixi run mlfx train --profile research
pixi run mlfx evaluate --profile research
pixi run mlfx benchmark --profile benchmark_fast
```

### Giải quyết hồ sơ

Khi một hồ sơ được chỉ định, hệ thống:

1. Nạp hồ sơ từ `config.toml` qua `WorkflowProfileConfig`
2. Gộp cài đặt hồ sơ với cấu hình cụ thể cho lệnh
3. Cờ CLI ghi đè cả cài đặt hồ sơ và mặc định từ config

```text
Cờ CLI (ưu tiên cao nhất)
    │
    ▼
Cài đặt hồ sơ
    │
    ▼
Mặc định từ config.toml
    │
    ▼
Mặc định tích hợp sẵn (ưu tiên thấp nhất)
```

---

## Kiến trúc CLI

### Cấu trúc lệnh

```text
mlfx
├── download          # Nạp dữ liệu tick
├── pipeline          # Xây dựng đặc trưng
├── train             # Huấn luyện mô hình
├── evaluate          # Backtesting & báo cáo
├── benchmark         # So sánh nhiều bộ máy
├── serve             # Máy chủ suy luận FastAPI
├── batch-predict     # Suy luận theo lô
├── drift             # Phát hiện độ lệch đặc trưng
├── drift-retrain     # Phát hiện độ lệch với tự động huấn luyện lại
├── models            # Liệt kê sổ đăng ký mô hình
├── profiles          # Liệt kê các hồ sơ quy trình
├── run-profile       # Train + evaluate từ hồ sơ
└── run-all           # Pipeline từ đầu đến cuối
```

### Triển khai lệnh

Mỗi lệnh CLI tuân theo một mẫu nhất quán:

```python
# mlfx/cli/main.py
@app.command("train")
def train_cmd(
    symbol: str = None,
    tf: str = None,
    label: str = None,
    profile: str = None,
    ...
):
    config = resolve_config("train", profile=profile)
    # Thực thi logic huấn luyện
```

---

## Nội bộ bộ máy học sâu

### Tiện ích chuỗi (`_sequence_utils.py`)

Các helper dùng chung cho bộ máy PyTorch dạng chuỗi:

| Hàm | Mục đích |
|----------|---------|
| `create_sequences()` | Chuyển ma trận đặc trưng thành sliding windows |
| `train_sequence_model_once()` | Huấn luyện với early stopping |

Ví dụ tạo chuỗi:

```python
from mlfx.training.backends._sequence_utils import create_sequences

X_seq, y_seq = create_sequences(X, y, seq_len=60)
# X_seq shape: (n_samples - seq_len, seq_len, n_features)
# y_seq shape: (n_samples - seq_len,)
```

### PyTorch Common (`_pytorch_common.py`)

Khung HPO dùng chung cho mọi bộ máy học sâu:

```python
from mlfx.training.backends._pytorch_common import run_pytorch_hpo

# Mỗi bộ máy cung cấp:
# - train_once_fn: hàm train cho một fold
# - suggest_params_fn: hàm lấy siêu tham số bằng Optuna

model, metrics = run_pytorch_hpo(
    train_once_fn=train_lstm_once,
    suggest_params_fn=_suggest_lstm_params,
    X=X, y=y, feature_cols=feature_cols,
    model_type="LSTM",
    n_trials=10, n_splits=5,
    seq_len=60, epochs=30, batch_size=128, patience=5,
    top_k_features=20, seed=42,
)
```

Khung này xử lý:
1. Chọn đặc trưng (`SelectKBest`)
2. HPO bằng Optuna với time-series CV
3. Đánh giá ngoài mẫu
4. Huấn luyện mô hình cuối cùng

---

## Chi tiết kiến trúc serving

### Torch Adapters (`torch_adapters.py`)

Dựng lại mô hình PyTorch từ tệp đầu ra đã lưu:

```python
from mlfx.serving.torch_adapters import rebuild_torch_model, predict_with_torch_model

# Nạp mô hình từ payload trong registry
model = rebuild_torch_model(payload)

# Dự đoán (tự xử lý sequence padding)
preds = predict_with_torch_model(model, X, seq_len=60)
```

Các loại mô hình được hỗ trợ:
- `LSTM` — `FXLstm`

### Chuỗi suy luận

```text
POST /predict
    │
    ▼
resolve_and_predict()
    │
    ├── Nạp mô hình tốt nhất từ registry
    │   └── mlfx.registry.models.get_registry()
    │
    ├── Dựng lại mô hình (sklearn hoặc torch)
    │   └── mlfx.serving.torch_adapters.rebuild_torch_model()
    │
    ├── Tiền xử lý đặc trưng
    │   └── mlfx.serving.features.prepare_features()
    │
    └── Chạy suy luận
        └── model.predict() hoặc predict_with_torch_model()
```

### Tiền xử lý đặc trưng cho suy luận

```python
from mlfx.serving.features import prepare_features

# Căn chỉnh đặc trưng đầu vào với các cột mô hình mong đợi
X_aligned = prepare_features(
    features_dict={"rsi_14": 55.3, "atr_14": 2.1, ...},
    feature_columns=model_feature_cols,
)
```

---

## Triển khai

```text
Dockerfile        ← multi-stage build (TA-Lib + Python)
docker-compose.yml
  ├── api         ← máy chủ suy luận mlfx (cổng 8000)
  └── mlflow      ← máy chủ MLflow (cổng 5000, profile: tracking)
```

---

## Bản đồ phụ thuộc

### Phụ thuộc giữa các mô-đun

```text
mlfx.cli
  └── mlfx.training.runner
        ├── mlfx.training.config        (TrainingConfig)
        ├── mlfx.training.registry      (get_backend_runner)
        ├── mlfx.training.backends.*    (các hàm run_*)
        ├── mlfx.tracking.tracker       (tùy chọn)
        └── mlfx.registry.models        (tùy chọn)

mlfx.serving.api
  └── mlfx.registry.models

mlfx.serving.batch
  ├── mlfx.registry.models
  ├── mlfx.serving.features
  └── mlfx.serving.inference

mlfx.monitoring.drift
  └── scipy.stats (KS test)
```

### Phụ thuộc ngoài theo từng tầng

| Tầng | Phụ thuộc chính |
|-------|------------------|
| Dữ liệu | `polars`, `pyarrow`, `aiohttp` |
| Đặc trưng | `ta-lib`, `numpy` |
| Huấn luyện | `sklearn`, `lightgbm`, `torch`, `optuna` |
| Bộ máy học sâu | `torch`, `pytorch-forecasting` |
| Serving | `fastapi`, `uvicorn`, `cachetools` |
| Tracking | `mlflow` (tùy chọn) |
| Monitoring | `scipy` |

---

## Tham chiếu chính sách đường dẫn

Mọi đường dẫn filesystem được quản lý qua `mlfx.config.paths.ProjectPaths`:

```python
from mlfx.config.paths import DEFAULT_PATHS

# Đường dẫn dữ liệu
DEFAULT_PATHS.raw_data_dir("XAUUSD")         # data/raw/XAUUSD/
DEFAULT_PATHS.ohlcv_dir("XAUUSD", "1H")      # data/ohlcv/XAUUSD/1H/
DEFAULT_PATHS.features_dir("XAUUSD", "1H")   # data/features/XAUUSD/1H/
DEFAULT_PATHS.labels_dir("XAUUSD", "1H")     # data/labels/XAUUSD/1H/

# Đường dẫn đầu ra
DEFAULT_PATHS.models_dir("XAUUSD", "1H")                      # outputs/models/XAUUSD/1H/
DEFAULT_PATHS.models_label_dir("XAUUSD", "1H", "label_10")   # outputs/models/XAUUSD/1H/label_10/
DEFAULT_PATHS.reports_dir("XAUUSD", "1H")                     # outputs/reports/XAUUSD/1H/
DEFAULT_PATHS.report_run_dir("XAUUSD", "1H", "label_10", "model", "R15")   # outputs/reports/XAUUSD/1H/label_10/model/R15/
DEFAULT_PATHS.runs_dir("XAUUSD", "1H")                        # outputs/runs/XAUUSD/1H/
```
