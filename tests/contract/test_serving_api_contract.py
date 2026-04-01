from __future__ import annotations

from pathlib import Path
import pickle

import numpy as np
import pytest


class _OrderSensitiveModel:
    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.where(X[:, 0] > X[:, 1], 4, 0)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:  # pragma: no cover - simple helper
        proba = np.full((len(X), 5), 0.05, dtype=np.float32)
        labels = self.predict(X)
        for idx, label in enumerate(labels):
            proba[idx, int(label)] = 0.8
        return proba


def test_predict_uses_registry_feature_columns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    pytest.importorskip("fastapi")

    from mlfx.serving import api
    from mlfx.serving.api import PredictRequest, predict

    artifact_path = tmp_path / "model.pkl"
    with artifact_path.open("wb") as file_handle:
        pickle.dump(_OrderSensitiveModel(), file_handle)

    class _FakeRegistry:
        def best_model(self, **_: object) -> dict[str, object]:
            return {
                "backend": "mlf",
                "artifact_path": str(artifact_path),
                "feature_columns": ["f2", "f1"],
            }

    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: _FakeRegistry())
    api._MODEL_CACHE.clear()

    response = predict(
        PredictRequest(
            symbol="XAUUSD",
            tf="1H",
            label="label_10",
            features={"f1": 1.0, "f2": 2.0},
        )
    )
    # Model sees columns in order [f2, f1], so 2.0 > 1.0 -> class 4 -> remapped to 2.
    assert response.prediction == 2


def test_predict_rejects_missing_required_features(monkeypatch: pytest.MonkeyPatch):
    pytest.importorskip("fastapi")

    from fastapi import HTTPException

    from mlfx.serving.api import PredictRequest, predict

    class _FakeRegistry:
        def best_model(self, **_: object) -> dict[str, object]:
            return {
                "backend": "mlf",
                "artifact_path": "/tmp/unused.pkl",
                "feature_columns": ["f1", "f2"],
            }

    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: _FakeRegistry())

    with pytest.raises(HTTPException) as exc_info:
        predict(
            PredictRequest(
                symbol="XAUUSD",
                tf="1H",
                label="label_10",
                features={"f1": 1.0},
            )
        )
    assert exc_info.value.status_code == 422
