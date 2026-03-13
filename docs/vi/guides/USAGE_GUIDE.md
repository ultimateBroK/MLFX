# MLFX - Hướng dẫn cấu hình và sử dụng

Tài liệu này là **cẩm nang vận hành giao diện dòng lệnh** của MLFX.

Nội dung tập trung vào:

- Cần chạy lệnh nào
- Tham số nào là quan trọng
- Mỗi bước tạo ra những đầu ra gì
- Khi nào nên dùng từng lệnh trong luồng làm việc chuẩn

Nếu bạn muốn đi theo lối bắt đầu nhanh nhất, hãy đọc:

- [Bắt đầu nhanh](../getting-started/QUICKSTART.md)

Nếu bạn là người mới và muốn hiểu **vì sao** luồng làm việc được tổ chức theo thứ tự hiện tại, hãy đọc:

- [Hướng dẫn nhập môn](../getting-started/NOOB_GUIDE.md)

## Tài liệu liên quan

- [Cổng tài liệu tiếng Việt](../README.md)
- [Bắt đầu nhanh](../getting-started/QUICKSTART.md)
- [Hướng dẫn nhập môn](../getting-started/NOOB_GUIDE.md)
- [Hướng dẫn đánh giá](EVALUATION_GUIDE.md)
- [Khắc phục sự cố](TROUBLESHOOTING.md)
- [Tham chiếu cấu hình](../reference/CONFIG_REFERENCE.md)
- [Tham chiếu API](../reference/API_REFERENCE.md)
- [Tham chiếu đặc trưng](../reference/FEATURE_REFERENCE.md)

---

## 1. Cài đặt môi trường

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install
```

### Nguyên tắc vận hành

- Luôn chạy lệnh qua `pixi run`
- Python và các phụ thuộc được quản lý qua `pyproject.toml`
- Quy trình chuẩn không yêu cầu tự tạo `uv` hoặc `venv` riêng

### Các tác vụ Pixi hữu ích

```bash
pixi run test
pixi run verify
pixi run clean-generated
```

---

## 2. Điểm vào chính

- `pixi run mlfx`: giao diện dòng lệnh thống nhất

### Xem trợ giúp

```bash
pixi run mlfx --help
pixi run mlfx pipeline --help
```

---

## 3. `config.toml`

`config.toml` được giao diện dòng lệnh đọc để nạp các giá trị mặc định.

Ví dụ:

```toml
[download]
symbol = "XAUUSD"
asset_class = "fx"
start_year = 2015
start_month = 1
concurrency = 20

[pipeline]
symbol = "XAUUSD"
tf = "1H"
pivot_type = "traditional"
pivot_anchor = "daily"

[train]
symbol = "XAUUSD"
tf = "1H"
backend = "mlf"
n_splits = 5

[backtest]
symbol          = "XAUUSD"
tf       = "1H"
label       = "label_10"
tp_r            = 1.5
sl_r            = 1.0
initial_capital = 10000.0
risk_pct        = 1.0
commission      = 0.1
```

### Các khóa nên nhớ

- `asset_class`: `fx`, `crypto`
- `tf`: `1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `1D`
- `pivot_type`: `traditional`, `fibonacci`, `woodie`, `classic`, `demark`, `camarilla`
- `pivot_anchor`: `daily`, `weekly`, `monthly`
- `label`: `label_5`, `label_10`, `label_20`
- `backend`: `mlf`, `lstm`, `sgd`, `stats`

Nếu bạn cần bản đối chiếu đầy đủ giữa `config.toml` và các cờ dòng lệnh, hãy đọc:

- [Tham chiếu cấu hình](../reference/CONFIG_REFERENCE.md)

---

## 4. Giao diện dòng lệnh theo từng bước

### 4.1. Tải dữ liệu tick

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
```

#### Mục đích

- Tải dữ liệu tick vào `data/raw/`
- Lưu trạng thái để có thể tiếp tục nếu quá trình tải bị gián đoạn

#### Tham số chính

- `--symbol`
- `--asset-class`
- `--start-year`
- `--start-month`
- `--end-year` *(không bắt buộc, mặc định: năm hiện tại)*
- `--end-month` *(không bắt buộc, mặc định: tháng hiện tại)*
- `--concurrency`
- `--force`
- `--skip-current-month` — bỏ qua kiểm tra hoặc sửa chữa tháng hiện tại

#### Đầu ra

- `data/raw/{symbol}/YYYY-MM.parquet`
- `data/raw/{symbol}/completed_months.json`

---

### 4.2. Kiểm tra dữ liệu thô

```bash
pixi run mlfx qa --symbol XAUUSD --asset-class fx
```

#### Mục đích

- Kiểm tra các khoảng trống dữ liệu đáng kể
- Xuất báo cáo chất lượng dữ liệu

#### Đầu ra

- `data/raw/{symbol}/{symbol}_Data_Quality_Report.md`

---

### 4.3. Chạy pipeline

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx pipeline --symbol XAUUSD --tf 1H 4H 1D
```

### Ví dụ bỏ qua từng chặng

```bash
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-resample
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-features
pixi run mlfx pipeline --symbol XAUUSD --tf 1H --skip-labels
```

#### Tham số chính

- `--symbol`
- `--tf` *(chấp nhận nhiều giá trị, ví dụ `1H 4H 1D`)*
- `--pivot`
- `--anchor`
- `--atr-period`
- `--atr-mult`
- `--force`
- `--skip-resample`
- `--skip-features`
- `--skip-labels`

#### Đầu ra

- `data/ohlcv/{symbol}/{tf}/`
- `data/features/{symbol}/{tf}/`
- `data/labels/{symbol}/{tf}/`

---

### 4.4. Huấn luyện mô hình

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf --n-trials 15 --n-splits 5
```

#### Sử dụng khoảng ngày

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --train-start 20240101 --train-end 20241231
```

#### Sử dụng hồ sơ

```bash
pixi run mlfx train --profile research
```

#### Các bộ máy hiện hỗ trợ qua dòng lệnh

- `mlf`
- `lstm`
- `sgd`
- `stats`

#### Tham số chính

- `--symbol`
- `--tf`
- `--label`
- `--backend`
- `--n-trials`
- `--n-splits`
- `--train-start` — ngày bắt đầu huấn luyện (định dạng YYYYMMDD)
- `--train-end` — ngày kết thúc huấn luyện (định dạng YYYYMMDD)
- `--profile` — sử dụng hồ sơ cấu hình
- `--force`

#### Đầu ra

- `outputs/models/{symbol}/{tf}/{label}/`

#### Lưu ý

- `n_trials` áp dụng cho `mlf` và `lstm`
- `n_splits` được ánh xạ khác nhau tùy bộ máy trong mã nguồn
- Để chọn bộ máy phù hợp, đọc:
  - [So sánh bộ máy](../architecture/BACKEND_COMPARISON.md)

---

### 4.5. Đánh giá và sinh báo cáo

```bash
pixi run mlfx evaluate \
  --symbol XAUUSD \
  --tf 1H \
  --label label_10 \
  --capital 10000 \
  --risk 1.0 \
  --commission 0.1 \
  --tp 1.5 \
  --sl 1.0 \
  --slippage 0.0
```

#### Sử dụng khoảng ngày

```bash
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --eval-start 20250101 --eval-end 20250331
```

#### Sử dụng hồ sơ

```bash
pixi run mlfx evaluate --profile research
```

#### Mặc định hoạt động như thế nào

- Nếu đã có mô hình phù hợp: backtest **mô hình**
- Nếu chưa có mô hình: quay về dùng **nhãn**
- Nếu muốn chỉ backtest nhãn: thêm `--use-labels`

#### Tham số chính

- `--symbol`
- `--tf`
- `--label`
- `--capital`
- `--risk`
- `--commission`
- `--tp`
- `--sl`
- `--slippage`
- `--eval-start` — ngày bắt đầu đánh giá (định dạng YYYYMMDD)
- `--eval-end` — ngày kết thúc đánh giá (định dạng YYYYMMDD)
- `--profile` — sử dụng hồ sơ cấu hình
- `--use-labels`

#### Đầu ra mặc định

- `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/model_{label}_R{tp*10}_candlestick.html`
- `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/model_{label}_R{tp*10}_equity.png`
- `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/model_{label}_R{tp*10}_heatmap.png`

#### Đọc tiếp

- [Hướng dẫn đánh giá](EVALUATION_GUIDE.md)

---

### 4.6. Phục vụ mô hình thời gian thực bằng FastAPI

```bash
# Khởi động máy chủ suy luận
pixi run mlfx serve --port 8000

# Hoặc qua Docker
docker-compose up api

# Kiểm tra trạng thái
curl http://localhost:8000/health

# Liệt kê các mô hình đã đăng ký
curl http://localhost:8000/models

# Dự đoán
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "XAUUSD",
    "tf": "1H",
    "label": "label_10",
    "features": {"rsi_14": 65.2, "atr_14": 0.003, "...": "..."}
  }'
```

#### Đọc tiếp

- [Tham chiếu API](../reference/API_REFERENCE.md)

---

### 4.7. Suy luận theo lô

Dùng khi cần xuất parquet dự đoán để triển khai hoặc tích hợp sang hệ thống khác.

> **Không dùng để xem kết quả backtest** — hãy dùng `evaluate` cho việc đó.

```bash
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H --label label_10
# → outputs/predictions/XAUUSD/1H/label_10/predictions.parquet
```

---

### 4.8. Phát hiện độ lệch dữ liệu

#### Bước 1 — Lưu mốc tham chiếu sau khi huấn luyện

```bash
python -c "
from mlfx.monitoring.drift import save_reference
import polars as pl
df = pl.read_parquet('data/labels/XAUUSD/1H/*.parquet')
feature_cols = [c for c in df.columns if c not in ['datetime','label_5','label_10','label_20']]
save_reference(df, feature_cols, 'XAUUSD', '1H')
"
```

#### Bước 2 — Kiểm tra độ lệch theo chu kỳ

```bash
pixi run mlfx drift --symbol XAUUSD --tf 1H
# In báo cáo JSON và trả về mã lỗi 1 nếu phát hiện độ lệch nghiêm trọng

# Tùy chỉnh ngưỡng:
pixi run mlfx drift --symbol XAUUSD --tf 1H --threshold-ks 0.1 --threshold-psi 0.2
```

#### Tham số tùy chọn

- `--threshold-ks` — ngưỡng kiểm định KS (mặc định: `0.1`)
- `--threshold-psi` — ngưỡng PSI (mặc định: `0.2`)

---

### 4.9. Sổ đăng ký mô hình

```bash
pixi run mlfx models
pixi run mlfx models --symbol XAUUSD --tf 1H
pixi run mlfx models --backend mlf --label label_10
```

---

### 4.10. So sánh nhiều bộ máy

So sánh hiệu năng giữa nhiều bộ máy trong một lần chạy:

```bash
pixi run mlfx benchmark --symbol XAUUSD --tf 1H --backends mlf sgd stats --n-trials 10
```

#### Sử dụng hồ sơ

```bash
pixi run mlfx benchmark --profile benchmark_fast
```

#### Tham số chính

- `--symbol`
- `--tf`
- `--label`
- `--backends` — danh sách bộ máy cần so sánh
- `--n-trials` — số lần thử cho mỗi bộ máy
- `--n-splits`
- `--train-start` / `--train-end` — khoảng ngày huấn luyện
- `--profile` — sử dụng hồ sơ cấu hình
- `--force`

---

### 4.11. Phát hiện độ lệch với tự động huấn luyện lại

Kiểm tra độ lệch đặc trưng và tự động huấn luyện lại nếu phát hiện:

```bash
pixi run mlfx drift-retrain --symbol XAUUSD --tf 1H --threshold-ks 0.1 --threshold-psi 0.2
```

#### Tham số chính

- `--symbol`
- `--tf`
- `--label`
- `--threshold-ks` — ngưỡng kiểm định KS
- `--threshold-psi` — ngưỡng PSI
- `--min-samples` — số mẫu tối thiểu cho mỗi đặc trưng

---

### 4.12. Liệt kê hồ sơ quy trình

Xem tất cả hồ sơ quy trình có sẵn trong `config.toml`:

```bash
pixi run mlfx profiles
```

---

### 4.13. Chạy train + evaluate từ hồ sơ

Thực thi luồng train + evaluate hoàn chỉnh sử dụng hồ sơ đã định nghĩa:

```bash
pixi run mlfx run-profile --profile research
```

#### Bỏ qua bước

```bash
pixi run mlfx run-profile --profile research --skip-train
pixi run mlfx run-profile --profile research --skip-evaluate
pixi run mlfx run-profile --profile research --skip-benchmark
```

#### Tham số chính

- `--profile` — **bắt buộc**, tên hồ sơ cần sử dụng
- `--skip-train` — bỏ qua bước huấn luyện
- `--skip-evaluate` — bỏ qua bước đánh giá
- `--skip-benchmark` — bỏ qua bước benchmark (nếu có trong hồ sơ)

---

### 4.14. Chạy toàn bộ quy trình từ đầu đến cuối

Thực thi pipeline hoàn chỉnh từ download đến đánh giá:

```bash
pixi run mlfx run-all --symbol XAUUSD --tf 1H --label label_10 --backend mlf
```

#### Bỏ qua bước

```bash
pixi run mlfx run-all --symbol XAUUSD --tf 1H --skip-download
pixi run mlfx run-all --symbol XAUUSD --tf 1H --skip-pipeline
pixi run mlfx run-all --symbol XAUUSD --tf 1H --skip-train
pixi run mlfx run-all --symbol XAUUSD --tf 1H --skip-evaluate
```

#### Tiếp tục khi có lỗi

```bash
pixi run mlfx run-all --symbol XAUUSD --tf 1H --continue-on-error --json
```

#### Tham số chính

- `--symbol`
- `--tf`
- `--label`
- `--backend`
- `--skip-download` — bỏ qua tải dữ liệu
- `--skip-pipeline` — bỏ qua xử lý đặc trưng
- `--skip-train` — bỏ qua huấn luyện mô hình
- `--skip-evaluate` — bỏ qua đánh giá
- `--continue-on-error` — tiếp tục ngay cả khi có bước thất bại
- `--json` — xuất kết quả dạng JSON

---

### 4.10. Theo dõi bằng MLflow (không bắt buộc)

Khởi động máy chủ MLflow qua Docker:

```bash
docker-compose --profile tracking up mlflow
# Giao diện tại http://localhost:5000
```

Khi máy chủ đang chạy, hệ thống theo dõi sẽ tự động dùng MLflow thay cho bộ theo dõi bằng tệp.

Nếu cần cài MLflow:

```bash
pip install mlflow
```

---

## 5. Luồng chạy đầy đủ

### 5.1. Luồng tối thiểu

Đủ để xem kết quả backtest:

```bash
pixi run mlfx download --symbol XAUUSD --asset-class fx --start-year 2024
pixi run mlfx pipeline --symbol XAUUSD --tf 1H
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
pixi run mlfx evaluate --symbol XAUUSD --tf 1H --label label_10 --tp 1.5 --sl 1.0
```

### 5.2. Một lệnh từ đầu đến cuối

Dùng `run-all` cho pipeline hoàn chỉnh:

```bash
pixi run mlfx run-all --symbol XAUUSD --tf 1H --label label_10 --backend mlf
```

### 5.3. Luồng dựa trên hồ sơ

Định nghĩa hồ sơ trong `config.toml` và dùng cho các thí nghiệm có thể tái tạo:

```bash
# Liệt kê các hồ sơ có sẵn
pixi run mlfx profiles

# Chạy train + evaluate sử dụng hồ sơ
pixi run mlfx run-profile --profile research

# Huấn luyện sử dụng hồ sơ
pixi run mlfx train --profile research

# Đánh giá sử dụng hồ sơ
pixi run mlfx evaluate --profile research

# Benchmark sử dụng hồ sơ
pixi run mlfx benchmark --profile benchmark_fast
```

### 5.4. Luồng nâng cao

```bash
# Kiểm tra dữ liệu thô
pixi run mlfx qa --symbol XAUUSD --asset-class fx

# Xem sổ đăng ký mô hình
pixi run mlfx models --symbol XAUUSD --tf 1H

# Suy luận theo lô
pixi run mlfx batch-predict --symbol XAUUSD --tf 1H --label label_10

# Phục vụ API thời gian thực
pixi run mlfx serve --port 8000

# Kiểm tra độ lệch dữ liệu
pixi run mlfx drift --symbol XAUUSD --tf 1H

# Phát hiện độ lệch với tự động huấn luyện lại
pixi run mlfx drift-retrain --symbol XAUUSD --tf 1H
```

---

## 6. Đầu ra và theo dõi

Mỗi lần huấn luyện thường sinh ra:

- **Tệp mô hình** — lưu trong `outputs/models/{symbol}/{tf}/{label}/`
- **Bản ghi trong sổ đăng ký** — cập nhật vào `outputs/models/registry.json`
- **Bản ghi chỉ số** — thường nằm trong `outputs/runs/{symbol}/{tf}/{label}/`
- **Tệp thông tin lần chạy** — lưu chi tiết khi dùng bộ theo dõi bằng tệp

### Theo dõi thí nghiệm

MLflow sẽ được dùng tự động nếu đã cài. Nếu chưa cài, hệ thống dùng bộ theo dõi dự phòng bằng tệp.

Ví dụ:

```bash
pixi run mlfx train ...
pixi run mlfx train ...
```

---

## 7. Bảng kiểm tra nhanh

Sau mỗi bước, nên kiểm tra:

- Sau `download`: có tệp parquet trong `data/raw/{symbol}/`
- Sau `qa`: có tệp báo cáo chất lượng dữ liệu
- Sau `pipeline`: có parquet trong `data/ohlcv/`, `data/features/`, `data/labels/`
- Sau `train`: có tệp đầu ra mới trong `outputs/models/{symbol}/{tf}/{label}/`
- Sau `evaluate`: có HTML hoặc PNG mới trong `outputs/reports/{symbol}/{tf}/{label}/model/R{tp*10}/` hoặc `outputs/reports/{symbol}/{tf}/{label}/labels/R{tp*10}/`
- Sau `batch-predict`: có parquet trong `outputs/predictions/{symbol}/{tf}/{label}/`
- Sau `drift`: không có cảnh báo độ lệch nghiêm trọng hoặc bạn đã hiểu rõ nguyên nhân

---

## 8. Dọn dẹp an toàn

Dọn vùng nhớ đệm và các đầu ra sinh tự động thường gặp:

```bash
pixi run clean-generated
```

### Khi nào nên dùng

- Trước khi chạy lại so sánh chuẩn hoặc kiểm thử khói
- Sau các lần huấn luyện dài tạo nhiều `lightning_logs`
- Khi workspace có quá nhiều đầu ra hoặc báo cáo cũ gây khó kiểm tra

Nếu cần xử lý sự cố, đọc:

- [Khắc phục sự cố](TROUBLESHOOTING.md)

Nếu cần lối chạy nhanh nhất, đọc:

- [Bắt đầu nhanh](../getting-started/QUICKSTART.md)

---

## 9. Lưu ý về vai trò của tài liệu này

- `QUICKSTART.md` là lối đi nhanh nhất
- `NOOB_GUIDE.md` dành cho người mới cần hiểu tư duy và luồng làm việc
- file này là cẩm nang vận hành chính cho giao diện dòng lệnh
- `CONFIG_REFERENCE.md` là nguồn tra cứu chuẩn khi cần đối chiếu cấu hình hoặc ánh xạ với cờ dòng lệnh
- `API_REFERENCE.md` là nguồn tra cứu chuẩn cho các điểm cuối của lớp phục vụ mô hình

---

## 10. Xem thêm

- [Bắt đầu nhanh](../getting-started/QUICKSTART.md)
- [Hướng dẫn nhập môn](../getting-started/NOOB_GUIDE.md)
- [Hướng dẫn đánh giá](EVALUATION_GUIDE.md)
- [Khắc phục sự cố](TROUBLESHOOTING.md)
- [Tham chiếu cấu hình](../reference/CONFIG_REFERENCE.md)
- [Tham chiếu API](../reference/API_REFERENCE.md)
- [Tham chiếu đặc trưng](../reference/FEATURE_REFERENCE.md)
- [So sánh bộ máy](../architecture/BACKEND_COMPARISON.md)
- [Cổng tài liệu tiếng Việt](../README.md)
