# MLFX API Reference

This document describes the REST API of the MLFX inference server.

---

## Overview

The MLFX serving API provides real-time inference through FastAPI. The server automatically loads the best model registered in the model registry and exposes endpoints for:

- Service health checks
- Listing registered models
- Running predictions for an input feature set

### Start the server

```/dev/null/api-reference-start.sh#L1-1
pixi run mlfx serve --port 8000
```

### Or run via Docker

```/dev/null/api-reference-docker.sh#L1-1
docker-compose up api
```

---

## Endpoints

## `GET /health`

A liveness endpoint for the service. Suitable for load balancers, orchestrators, or health checks in operational environments.

### Request

```/dev/null/api-reference-health-request.sh#L1-1
curl http://localhost:8000/health
```

### Response

```/dev/null/api-reference-health-response.json#L1-3
{
  "status": "ok"
}
```

### Status codes

- `200` — Service is healthy

---

## `GET /models`

List all models registered in the model registry, with optional filtering.

### Request

```/dev/null/api-reference-models-request.sh#L1-10
# All models
curl http://localhost:8000/models

# Filter by symbol
curl "http://localhost:8000/models?symbol=XAUUSD"

# Filter by symbol and timeframe
curl "http://localhost:8000/models?symbol=XAUUSD&tf=1H"

# Filter by backend
curl "http://localhost:8000/models?backend=mlf"
```

### Query parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | No | Filter by instrument symbol |
| `tf` | string | No | Filter by timeframe |
| `backend` | string | No | Filter by backend type |

### Response

```/dev/null/api-reference-models-response.json#L1-15
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

- `200` — Success

---

## `POST /predict`

Run inference for an input feature vector. The server automatically loads the best registered model for the `symbol` / `tf` / `label_col` combination.

### Request

```/dev/null/api-reference-predict-request.sh#L1-13
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

| Field | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | Yes | Instrument symbol |
| `tf` | string | Yes | Timeframe |
| `label_col` | string | Yes | Label column used during training |
| `features` | object | Yes | Mapping of `feature name -> value` |

### Response

```/dev/null/api-reference-predict-response.json#L1-7
{
  "symbol": "XAUUSD",
  "tf": "1H",
  "prediction": 1,
  "confidence": 0.72,
  "model_backend": "mlf"
}
```

### Response field meanings

| Field | Type | Description |
|---|---|---|
| `symbol` | string | Echo of the request `symbol` |
| `tf` | string | Echo of the request `tf` |
| `prediction` | integer | Predicted label: `-2`, `-1`, `0`, `1`, `2` |
| `confidence` | float \| null | Prediction probability; may be `null` for some deep-learning backends |
| `model_backend` | string | Backend key of the loaded model |

### Status codes

- `200` — Success
- `404` — No registered model found for the `symbol/tf/label_col` combination
- `422` — Missing required features or invalid request
- `500` — Registry entry has no `artifact_path` or the server encountered an internal error

---

## Meaning of prediction labels

The `prediction` field returns ordinal labels:

| Value | Meaning |
|---|---|
| `2` | Strong upward move expected |
| `1` | Moderate upward move expected |
| `0` | Neutral / no clear direction |
| `-1` | Moderate downward move expected |
| `-2` | Strong downward move expected |

---

## Confidence scores

- `confidence` is only available when the backend supports `predict_proba()`, such as `mlf` or `sgd`
- Deep-learning backends such as `lstm`, `bilstm`, `transformer`, `cnn_lstm`, and `neuralforecast` usually return `null`
- The `confidence` value represents the probability of the predicted class

---

## Error handling

## `404` — Model not found

### Response

```/dev/null/api-reference-404-response.json#L1-3
{
  "detail": "No registered model for XAUUSD/1H/label_10"
}
```

### Resolution

Train a model first:

```/dev/null/api-reference-train-before-predict.sh#L1-1
pixi run mlfx train --symbol XAUUSD --tf 1H --label label_10 --backend mlf
```

---

## `422` — Missing required features

### Response

```/dev/null/api-reference-422-response.json#L1-3
{
  "detail": "Missing required feature(s): ['rsi_14', 'atr_14']"
}
```

### Resolution

Pass all features that were used during model training. You can inspect the `feature_columns` list in the model registry.

---

## Model cache

The server maintains an LRU cache of up to `32` models to avoid reloading the model for every request. The cache key is based on `artifact_path`.

---

## Python example

```/dev/null/api-reference-python-client.py#L1-26
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

## Operational notes

- This API is suitable for real-time inference after a model has been trained and registered
- If no model exists in the registry, the `/predict` endpoint will not work
- The data inside `features` must match the feature schema used when the model was trained
- You should use the `/health` endpoint for readiness / liveness checks in deployed environments
- If you need to scale in a real deployment, you can run multiple service instances behind a load balancer

---

## See Also

- [API Reference (Vietnamese)](../../vi/reference/API_REFERENCE.md)
- [CLI Usage Guide](../guides/USAGE_GUIDE.md)
- [Architecture](../architecture/ARCHITECTURE.md)
- [Feature Reference](FEATURE_REFERENCE.md)
- [Configuration Reference](CONFIG_REFERENCE.md)
