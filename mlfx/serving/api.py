"""FastAPI real-time inference endpoint.

Requires ``fastapi`` and ``uvicorn`` to be installed::

    pip install fastapi uvicorn

Start the server::

    python -m mlfx.serving.api
    # or:
    uvicorn mlfx.serving.api:app --host 0.0.0.0 --port 8000

Endpoints
---------
GET  /health           — liveness probe
POST /predict          — direction prediction for a feature vector
GET  /models           — list registered models
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from mlfx.serving.core import resolve_and_predict

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel

    _FASTAPI_AVAILABLE = True
except ImportError as _exc:
    _FASTAPI_AVAILABLE = False
    _FASTAPI_IMPORT_ERROR = str(_exc)


def _require_fastapi() -> None:
    if not _FASTAPI_AVAILABLE:
        raise ImportError(
            "FastAPI is required for the serving module. "
            "Install it with:  pip install fastapi uvicorn"
        )


_require_fastapi()

from fastapi import FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402

app = FastAPI(
    title="ML_FX Inference API",
    description="Real-time direction prediction for FX / commodities.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class PredictRequest(BaseModel):
    """Input feature map for a single bar."""

    symbol: str = "XAUUSD"
    tf: str = "1H"
    label_col: str = "label_10"
    features: dict[str, float]


class PredictResponse(BaseModel):
    symbol: str
    tf: str
    prediction: int
    confidence: float | None = None
    model_backend: str | None = None


# ---------------------------------------------------------------------------
# Model cache
# ---------------------------------------------------------------------------

_MODEL_CACHE: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/models")
def list_models(
    symbol: str | None = None,
    tf: str | None = None,
    backend: str | None = None,
) -> list[dict[str, Any]]:
    """Return entries from the model registry."""
    from mlfx.registry.models import get_registry  # noqa: PLC0415

    reg = get_registry()
    return reg.list_models(symbol=symbol, tf=tf, backend=backend)


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    """Run inference for a single feature vector.

    The *best* registered model for the requested symbol / tf / label_col is
    loaded automatically.
    """
    from mlfx.registry.models import get_registry  # noqa: PLC0415

    reg = get_registry()
    result = resolve_and_predict(
        request.symbol,
        request.tf,
        request.label_col,
        dict(request.features),
        registry=reg,
        model_cache=_MODEL_CACHE,
    )
    if result is None:
        entry = reg.best_model(
            symbol=request.symbol,
            tf=request.tf,
            label_col=request.label_col,
        )
        if entry is None:
            raise HTTPException(
                status_code=404,
                detail=f"No registered model for {request.symbol}/{request.tf}/{request.label_col}",
            )
        artifact_path = entry.get("artifact_path", "")
        if not artifact_path:
            raise HTTPException(status_code=500, detail="Registry entry has no artifact_path.")
        feature_names = entry.get("feature_columns") or sorted(request.features.keys())
        missing = [f for f in feature_names if f not in request.features]
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"Missing required feature(s): {missing[:10]}",
            )
        raise HTTPException(status_code=404, detail="Artifact not found or inference failed.")

    predictions, artifact_path, entry = result
    prediction = int(predictions[0])

    confidence = None
    if _MODEL_CACHE.get(artifact_path) is not None:
        model = _MODEL_CACHE[artifact_path]
        if hasattr(model, "predict_proba"):
            feature_names = entry.get("feature_columns") or sorted(request.features.keys())
            X = np.array([[request.features[f] for f in feature_names]], dtype=np.float32)
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            proba = model.predict_proba(X)[0]
            confidence = float(proba.max())

    return PredictResponse(
        symbol=request.symbol,
        tf=request.tf,
        prediction=prediction,
        confidence=confidence,
        model_backend=entry.get("backend"),
    )


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import uvicorn  # noqa: PLC0415

    uvicorn.run("mlfx.serving.api:app", host="0.0.0.0", port=8000, reload=False)
