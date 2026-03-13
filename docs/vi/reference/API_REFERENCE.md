# MLFX - Tham chiếu API

Tài liệu này mô tả API REST của máy chủ suy luận trong MLFX.

---

## Tổng quan

API phục vụ mô hình của MLFX cung cấp khả năng suy luận thời gian thực thông qua FastAPI. Máy chủ sẽ tự động nạp mô hình tốt nhất đã được đăng ký trong sổ đăng ký mô hình và cung cấp các điểm cuối để:

- Kiểm tra tình trạng hoạt động của dịch vụ
- Liệt kê các mô hình đã đăng ký
- Chạy dự đoán cho một bộ đặc trưng đầu vào

### Khởi động máy chủ

```/dev/null/api-reference-start.sh#L1-1
pixi run mlfx serve --port 8000
```

### Hoặc chạy qua Docker

```/dev/null/api-reference-docker.sh#L1-1
docker-compose up api
```

---

## Các điểm cuối

## `GET /health`

Điểm cuối kiểm tra tình trạng sống của dịch vụ. Phù hợp cho bộ cân bằng tải, trình điều phối hoặc cơ chế kiểm tra sức khỏe trong môi trường vận hành.

### Yêu cầu

```/dev/null/api-reference-health-request.sh#L1-1
curl http://localhost:8000/health
```

### Phản hồi

```/dev/null/api-reference-health-response.json#L1-3
{
  "status": "ok"
}
```

### Mã trạng thái

- `200` — Dịch vụ hoạt động bình thường

---

## `GET /models`

Liệt kê toàn bộ mô hình đã được đăng ký trong sổ đăng ký, có hỗ trợ lọc theo một số tiêu chí.

### Yêu cầu

```/dev/null/api-reference-models-request.sh#L1-10
# Tất cả mô hình
curl http://localhost:8000/models

# Lọc theo mã công cụ
curl "http://localhost:8000/models?symbol=XAUUSD"

# Lọc theo mã công cụ và khung thời gian
curl "http://localhost:8000/models?symbol=XAUUSD&tf=1H"

# Lọc theo bộ máy
curl "http://localhost:8000/models?backend=mlf"
```

### Tham số truy vấn

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `symbol` | string | Không | Lọc theo mã công cụ tài chính |
| `tf` | string | Không | Lọc theo khung thời gian |
| `backend` | string | Không | Lọc theo loại bộ máy |

### Phản hồi

```/dev/null/api-reference-models-response.json#L1-15
[
  {
    "run_id": "20250301_120000",
    "symbol": "XAUUSD",
    "tf": "1H",
    "label": "label_10",
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

### Mã trạng thái

- `200` — Thành công

---

## `POST /predict`

Chạy suy luận cho một bộ đặc trưng đầu vào. Máy chủ sẽ tự động nạp mô hình tốt nhất đã đăng ký cho tổ hợp `symbol` / `tf` / `label`.

### Yêu cầu

```/dev/null/api-reference-predict-request.sh#L1-13
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "XAUUSD",
    "tf": "1H",
    "label": "label_10",
    "features": {
      "rsi_14": 55.3,
      "atr_14": 2.1,
      "ema_20": 1940.5,
      "macd": 1.5,
      "macd_signal": 1.2
    }
  }'
```

### Cấu trúc phần thân yêu cầu

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `symbol` | string | Có | Mã công cụ tài chính |
| `tf` | string | Có | Khung thời gian |
| `label` | string | Có | Cột nhãn đã dùng khi huấn luyện |
| `features` | object | Có | Ánh xạ `tên đặc trưng -> giá trị` |

### Phản hồi

```/dev/null/api-reference-predict-response.json#L1-7
{
  "symbol": "XAUUSD",
  "tf": "1H",
  "prediction": 1,
  "confidence": 0.72,
  "model_backend": "mlf"
}
```

### Ý nghĩa các trường phản hồi

| Trường | Kiểu | Mô tả |
|---|---|---|
| `symbol` | string | Trả lại `symbol` từ yêu cầu |
| `tf` | string | Trả lại `tf` từ yêu cầu |
| `prediction` | integer | Nhãn dự đoán: `-2`, `-1`, `0`, `1`, `2` |
| `confidence` | float \| null | Xác suất dự đoán; có thể là `null` với một số backend học sâu |
| `model_backend` | string | Khóa bộ máy của mô hình được nạp |

### Mã trạng thái

- `200` — Thành công
- `404` — Không tìm thấy mô hình đã đăng ký cho tổ hợp `symbol/tf/label`
- `422` — Thiếu đặc trưng bắt buộc hoặc yêu cầu không hợp lệ
- `500` — Bản ghi trong sổ đăng ký không có `artifact_path` hoặc máy chủ gặp lỗi nội bộ

---

## Ý nghĩa nhãn dự đoán

Trường `prediction` trả về nhãn thứ bậc:

| Giá trị | Ý nghĩa |
|---|---|
| `2` | Kỳ vọng giá tăng mạnh |
| `1` | Kỳ vọng giá tăng vừa |
| `0` | Trung lập / không có hướng rõ ràng |
| `-1` | Kỳ vọng giá giảm vừa |
| `-2` | Kỳ vọng giá giảm mạnh |

---

## Điểm tin cậy dự đoán

- `confidence` chỉ có khi bộ máy hỗ trợ `predict_proba()`, ví dụ như `mlf` hoặc `sgd`
- Bộ máy PyTorch `lstm` thường trả về `null`
- Giá trị `confidence` đại diện cho xác suất của lớp được dự đoán

---

## Xử lý lỗi

## `404` — Không tìm thấy mô hình

### Phản hồi

```/dev/null/api-reference-404-response.json#L1-3
{
  "detail": "No registered model for XAUUSD/1H/label_10"
}
```

### Cách xử lý

Hãy huấn luyện mô hình trước:

```/dev/null/api-reference-train-before-predict.sh#L1-1
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
```

---

## `422` — Thiếu đặc trưng bắt buộc

### Phản hồi

```/dev/null/api-reference-422-response.json#L1-3
{
  "detail": "Missing required feature(s): ['rsi_14', 'atr_14']"
}
```

### Cách xử lý

Hãy truyền đầy đủ các đặc trưng đã được dùng khi huấn luyện mô hình. Bạn có thể kiểm tra danh sách `feature_columns` trong sổ đăng ký mô hình.

---

## Bộ nhớ đệm mô hình

Máy chủ duy trì bộ nhớ đệm LRU với tối đa `32` mô hình để tránh phải nạp lại mô hình cho mỗi yêu cầu. Bộ nhớ đệm này được đánh dấu theo `artifact_path`.

---

## Ví dụ bằng Python

```/dev/null/api-reference-python-client.py#L1-26
import requests

# Kiểm tra sức khỏe
response = requests.get("http://localhost:8000/health")
print(response.json())  # {"status": "ok"}

# Liệt kê mô hình
response = requests.get(
    "http://localhost:8000/models",
    params={"symbol": "XAUUSD", "tf": "1H"},
)
print(response.json())

# Dự đoán
payload = {
    "symbol": "XAUUSD",
    "tf": "1H",
    "label": "label_10",
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

- API này phù hợp cho suy luận thời gian thực sau khi mô hình đã được huấn luyện và đăng ký
- Nếu chưa có mô hình trong sổ đăng ký, điểm cuối `/predict` sẽ không hoạt động
- Dữ liệu trong `features` phải khớp với lược đồ đặc trưng mà mô hình đã dùng khi huấn luyện
- Nên dùng điểm cuối `/health` cho các kiểm tra sẵn sàng / còn sống trong môi trường triển khai
- Nếu cần mở rộng khi vận hành thực tế, bạn có thể chạy nhiều phiên bản dịch vụ phía sau bộ cân bằng tải

---

## Xem thêm

- [API Reference (English)](../../en/reference/API_REFERENCE.md)
- [Hướng dẫn sử dụng CLI](../guides/USAGE_GUIDE.md)
- [Kiến trúc hệ thống](../architecture/ARCHITECTURE.md)
- [Tham chiếu đặc trưng](FEATURE_REFERENCE.md)
- [Tham chiếu cấu hình](CONFIG_REFERENCE.md)
