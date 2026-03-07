"""Model loading and prediction adapters for serving.

Provides a minimal compatibility layer across currently persisted artifact
formats:
- sklearn/nixtla objects exposing ``predict(X)``
- dict payloads containing ``clf`` and ``scaler`` (online SGD backend)
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np


def load_artifact(artifact_path: str) -> Any:
    """Load a pickle or torch payload from disk."""
    path = Path(artifact_path)
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    if path.suffix in (".pt", ".pth"):
        import torch  # noqa: PLC0415

        return torch.load(path, map_location="cpu", weights_only=False)

    with path.open("rb") as file_handle:
        return pickle.load(file_handle)  # noqa: S301


def predict_labels(model: Any, X: np.ndarray) -> np.ndarray:
    """Run prediction with best-effort adaptation by artifact type.

    Returns class labels in backend-native encoding (typically 0..4).
    """
    # Most sklearn/nixtla objects.
    if hasattr(model, "predict"):
        return np.asarray(model.predict(X))

    # Online SGD backend saves {"clf": clf, "scaler": scaler}.
    if isinstance(model, dict) and "clf" in model and "scaler" in model:
        clf = model["clf"]
        scaler = model["scaler"]
        X_scaled = scaler.transform(X)
        return np.asarray(clf.predict(X_scaled))

    raise TypeError(
        "Unsupported artifact format for serving. "
        "Expected object with predict(X) or dict with clf/scaler."
    )
