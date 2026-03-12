# MLFX - Tham chiếu API

Tài liệu này mô tả REST API của inference server trong MLFX.

---

## Tổng quan

Serving API của MLFX cung cấp khả năng suy luận thời gian thực thông qua FastAPI. Server tự động nạp model tốt nhất đã được đăng ký trong registry và cung cấp các endpoint để:

- Kiểm tra tình trạng hoạt động của service
- Liệt kê các model đã đăng ký
- Chạy dự đoán cho một feature vector

### Khởi động server

```bash
pixi run mlfx serve --port 8000
```

### Hoặc chạy qua Docker

```bash
docker-compose up api
```

---

## Endpoints

## `GET /health`

Endpoint kiểm tra tình trạng sống của service, phù hợp cho load balancer, orchestrator, hoặc health checks trong môi trường production.

### Request

```bash
curl http://localhost:8000/health
```

### Response

```json
{
  "status": "ok"
}
```

### Status codes

- `200` — Service hoạt động bình thường

---

## `GET /models`

Liệt kê toàn bộ model đã được đăng ký trong registry, có hỗ trợ lọc theo một số tiêu chí.

### Request

```bash
# Tất cả model
curl http://localhost:8000/models

# Lọc theo symbol
curl "http://localhost:8000/models?symbol=XAUUSD"

# Lọc theo symbol và timeframe
curl "http://localhost:8000/models?symbol=XAUUSD&tf=1H"

# Lọc theo backend
curl "http://localhost:8000/models?backend=mlf"
```

### Query parameters

| Parameter | Type | Required | Mô tả |
|---|---|---|---|
| `symbol` | string | No | Lọc theo mã instrument |
| `tf` | string | No | Lọc theo timeframe |
| `backend` | string | No | Lọc theo loại backend |

### Response

```json
[
  {
    "run_id": "20250301_120000",
    "symbol": "XAUUSD",
    "tf": "1H",
    "label_col": "label_10",
    "backend": "mlf",
    "artifact_path": "outputs/models/XAUUSD/1H/20250301_120000.pkl",
    "metrics": {
      "best_cv_f1_macro": 0.72,
      "test_f1_macro": 0.71
    },
    "feature_columns": ["rsi_14", "atr_14", "ema_20", "..."],
    "timestamp": "2025-03-01T12:00:00"
  }
]
```

### Status codes

- `200` — Thành công

---

## `POST /predict`

Chạy suy luận cho một feature vector. Server sẽ tự động nạp model tốt nhất đã đăng ký cho tổ hợp `symbol` / `tf` / `label_col`.

### Request

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "XAUUSD",
    "tf": "1H",
    "label_col": "label_10",
    "features": {
      "rsi_14": 55.3,
      "atr_14": 2.1,
      "ema_20": 1940.5,
      "macd": 1.5,
      "macd_signal": 1.2
    }
  }'
```

### Request body schema

| Field | Type | Required | Mô tả |
|---|---|---|---|
| `symbol` | string | Yes | Mã instrument |
| `tf` | string | Yes | Timeframe |
| `label_col` | string | Yes | Cột label đã dùng khi train |
| `features` | object | Yes | Mapping `tên feature -> giá trị` |

### Response

```json
{
  "symbol": "XAUUSD",
  "tf": "1H",
  "prediction": 1,
  "confidence": 0.72,
  "model_backend": "mlf"
}
```

### Response fields

| Field | Type | Mô tả |
|---|---|---|
| `symbol` | string | Echo lại `symbol` từ request |
| `tf` | string | Echo lại `tf` từ request |
| `prediction` | integer | Nhãn dự đoán: `-2`, `-1`, `0`, `1`, `2` |
| `confidence` | float \| null | Xác suất dự đoán; có thể là `null` với backend deep learning |
| `model_backend` | string | Backend key của model được nạp |

### Status codes

- `200` — Thành công
- `404` — Không tìm thấy model đã đăng ký cho tổ hợp `symbol/tf/label_col`
- `422` — Thiếu feature bắt buộc hoặc request không hợp lệ
- `500` — Registry entry không có `artifact_path` hoặc server gặp lỗi nội bộ

---

## Ý nghĩa nhãn dự đoán

Trường `prediction` trả về nhãn ordinal:

| Value | Ý nghĩa |
|---|---|
| `2` | Kỳ vọng giá tăng mạnh |
| `1` | Kỳ vọng giá tăng vừa |
| `0` | Trung lập / không có hướng rõ ràng |
| `-1` | Kỳ vọng giá giảm vừa |
| `-2` | Kỳ vọng giá giảm mạnh |

---

## Confidence score

- `confidence` chỉ có khi backend hỗ trợ `predict_proba()`, ví dụ như `mlf` hoặc `sgd`
- Các backend deep learning như `lstm`, `bilstm`, `transformer`, `cnn_lstm`, `neuralforecast` thường trả về `null`
- Giá trị `confidence` đại diện cho xác suất của lớp được dự đoán

---

## Xử lý lỗi

## `404` — Không tìm thấy model

### Response

```json
{
  "detail": "No registered model for XAUUSD/1H/label_10"
}
```

### Cách xử lý

Hãy train model trước:

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
```

---

## `422` — Thiếu feature bắt buộc

### Response

```json
{
  "detail": "Missing required feature(s): ['rsi_14', 'atr_14']"
}
```

### Cách xử lý

Truyền đầy đủ các feature đã được dùng khi train model. Bạn có thể kiểm tra danh sách `feature_columns` trong registry.

---

## Model caching

Server duy trì LRU cache với tối đa `32` model để tránh nạp lại model cho mỗi request. Cache được đánh theo `artifact_path`.

---

## Ví dụ client Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())  # {"status": "ok"}

# List models
response = requests.get(
    "http://localhost:8000/models",
    params={"symbol": "XAUUSD", "tf": "1H"},
)
print(response.json())

# Predict
payload = {
    "symbol": "XAUUSD",
    "tf": "1H",
    "label_col": "label_10",
    "features": {
        "rsi_14": 55.3,
        "atr_14": 2.1,
        "ema_20": 1940.5,
        "macd": 1.5,
        "macd_signal": 1.2
    }
}

response = requests.post("http://localhost:8000/predict", json=payload)
print(response.json())
```

---

## Ghi chú vận hành

- API này phù hợp cho suy luận thời gian thực sau khi model đã được train và đăng ký
- Nếu chưa có model trong registry, endpoint `/predict` sẽ không hoạt động
- Dữ liệu trong `features` phải khớp với schema feature mà model đã dùng khi train
- Nên dùng endpoint `/health` cho readiness/liveness checks trong môi trường deploy
- Nếu cần scale production, bạn có thể chạy nhiều instance phía sau load balancer

---

## Xem thêm

- [API Reference (English)](../../en/reference/API_REFERENCE.md)
- [Hướng dẫn sử dụng CLI](../guides/USAGE_GUIDE.md)
- [Kiến trúc hệ thống](../architecture/ARCHITECTURE.md)
- [Tham chiếu feature](FEATURE_REFERENCE.md)
- [Tham chiếu cấu hình](CONFIG_REFERENCE.md)
