# MLFX API Reference

REST API documentation for the MLFX inference server.

---

## Overview

The MLFX serving API provides real-time model inference via FastAPI. It automatically loads the best registered model for the requested context and exposes endpoints for:

- Health checks
- Model listing
- Prediction requests

**Start the server:**
```bash
pixi run mlfx serve --port 8000
```

**Or via Docker:**
```bash
docker-compose up api
```

---

## Endpoints

### `GET /health`

Liveness probe for load balancers, orchestrators, and deployment platforms.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200` — Server is healthy

---

### `GET /models`

List all registered models with optional filtering.

**Request:**
```bash
# All models
curl http://localhost:8000/models

# Filter by symbol
curl "http://localhost:8000/models?symbol=XAUUSD"

# Filter by symbol and timeframe
curl "http://localhost:8000/models?symbol=XAUUSD&tf=1H"

# Filter by backend
curl "http://localhost:8000/models?backend=mlf"
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | No | Filter by instrument symbol |
| `tf` | string | No | Filter by timeframe |
| `backend` | string | No | Filter by backend type |

**Response:**
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
    "feature_columns": ["rsi_14", "atr_14", "ema_20", "macd", "macd_signal"],
    "timestamp": "2025-03-01T12:00:00"
  }
]
```

**Status Codes:**
- `200` — Success

---

### `POST /predict`

Run inference for a single feature vector. The best registered model for the requested `symbol` / `tf` / `label_col` combination is loaded automatically.

**Request:**
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

**Request Body Schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | Yes | Instrument symbol |
| `tf` | string | Yes | Timeframe |
| `label_col` | string | Yes | Label column used during training |
| `features` | object | Yes | Mapping of feature name → numeric value |

**Response:**
```json
{
  "symbol": "XAUUSD",
  "tf": "1H",
  "prediction": 1,
  "confidence": 0.72,
  "model_backend": "mlf"
}
```

**Response Fields:**

| Field | Type | Description |
|---|---|---|
| `symbol` | string | Echo of the request symbol |
| `tf` | string | Echo of the request timeframe |
| `prediction` | integer | Predicted label: `-2`, `-1`, `0`, `1`, `2` |
| `confidence` | float \| null | Predicted-class probability; `null` for backends that do not expose `predict_proba()` |
| `model_backend` | string | Backend key of the loaded model |

**Status Codes:**
- `200` — Success
- `404` — No registered model for the requested `symbol` / `tf` / `label_col`
- `422` — Missing required feature columns
- `500` — Registry entry exists but has no usable `artifact_path`

---

## Prediction Labels

The `prediction` field returns ordinal labels:

| Value | Meaning |
|---|---|
| `2` | Strong upward move expected |
| `1` | Moderate upward move expected |
| `0` | Neutral / no clear direction |
| `-1` | Moderate downward move expected |
| `-2` | Strong downward move expected |

---

## Confidence Scores

- `confidence` is only available for backends that support `predict_proba()` such as `mlf` and `sgd`
- Deep learning backends such as `lstm`, `bilstm`, `transformer`, `cnn_lstm`, and `neuralforecast` typically return `null`
- The value represents the probability of the predicted class, not a full class-distribution payload

---

## Error Handling

### 404 — Model Not Found

```json
{
  "detail": "No registered model for XAUUSD/1H/label_10"
}
```

**Resolution:** Train and register a model first.

```bash
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
```

---

### 422 — Missing Features

```json
{
  "detail": "Missing required feature(s): ['rsi_14', 'atr_14']"
}
```

**Resolution:** Include all features used during training. Check the model's `feature_columns` in the registry output.

---

### 500 — Invalid Registry Entry

```json
{
  "detail": "Registry entry has no artifact_path"
}
```

**Resolution:** Re-train the model or repair the registry entry so that it points to a valid saved artifact.

---

## Model Caching

The server maintains an LRU cache with a maximum of `32` loaded models. Models are cached by `artifact_path` to avoid reloading them on every request.

---

## Python Client Example

```python
import requests

# Health check
health = requests.get("http://localhost:8000/health")
print(health.json())  # {"status": "ok"}

# List models
models_response = requests.get(
    "http://localhost:8000/models",
    params={"symbol": "XAUUSD", "tf": "1H"},
)
models = models_response.json()
print(f"Found {len(models)} model(s)")

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
        "macd_signal": 1.2,
    },
}
prediction_response = requests.post("http://localhost:8000/predict", json=payload)
result = prediction_response.json()
print(f"Prediction: {result['prediction']}, Confidence: {result['confidence']}")
```

---

## Integration Notes

- The API is stateless: each request is handled independently
- Model selection is automatic based on the best registered model for the requested context
- For production deployments, consider running multiple API instances behind a load balancer
- Use `/health` for Kubernetes liveness and readiness probes
- Ensure the request feature schema matches the feature schema used during training

---

## See Also

- [Configuration Reference](CONFIG_REFERENCE.md)
- [Feature Reference](FEATURE_REFERENCE.md)
- [Architecture](../architecture/ARCHITECTURE.md)
- [Usage Guide](../guides/USAGE_GUIDE.md)
- [Evaluation Guide](../guides/EVALUATION_GUIDE.md)
