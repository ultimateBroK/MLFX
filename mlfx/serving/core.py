"""Shared prediction pipeline for API and batch inference."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import polars as pl

from mlfx.serving.inference import load_artifact, predict_labels

if TYPE_CHECKING:
    from mlfx.registry.models import ModelRegistry


def resolve_and_predict(
    symbol: str,
    tf: str,
    label: str,
    features: pl.DataFrame | dict[str, float],
    *,
    registry: ModelRegistry | None = None,
    model_cache: dict[str, Any] | None = None,
) -> tuple[np.ndarray, str, dict[str, Any]] | None:
    """Resolve model, load, validate, predict.

    Returns (predictions, artifact_path, entry) on success, or None on failure.
    """
    if registry is None:
        from mlfx.registry.models import get_registry  # noqa: PLC0415

        registry = get_registry()

    entry = registry.best_model(symbol=symbol, tf=tf, label=label)
    if entry is None:
        return None

    artifact_path = entry.get("artifact_path", "")
    if not artifact_path or not Path(artifact_path).exists():
        return None

    feature_cols = entry.get("feature_columns")
    if feature_cols is None:
        if isinstance(features, pl.DataFrame):
            from mlfx.serving.features import select_numeric_feature_columns

            feature_cols = select_numeric_feature_columns(features)
        else:
            feature_cols = sorted(features.keys())

    if isinstance(features, pl.DataFrame):
        missing = [c for c in feature_cols if c not in features.columns]
        if missing:
            return None
        X = features.select(feature_cols).to_numpy().astype(np.float32)
    else:
        missing = [c for c in feature_cols if c not in features]
        if missing:
            return None
        X = np.array([[features[c] for c in feature_cols]], dtype=np.float32)

    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    if model_cache is not None and artifact_path in model_cache:
        model = model_cache[artifact_path]
    else:
        try:
            model = load_artifact(artifact_path)
        except FileNotFoundError:
            return None
        if model_cache is not None:
            model_cache[artifact_path] = model

    from mlfx.serving.inference import _is_mlforecast

    if (
        isinstance(features, pl.DataFrame)
        and _is_mlforecast(model)
        and label in features.columns
    ):
        raw_preds = predict_labels(
            model,
            X,
            df=features,
            label=label,
            feature_cols=feature_cols,
        )
    else:
        raw_preds = predict_labels(model, X)
    predictions = (raw_preds - 2).astype(np.int32)  # remap [0,4] → [-2,2]

    return predictions, artifact_path, entry
