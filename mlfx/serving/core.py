"""Shared prediction pipeline for API and batch inference."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import polars as pl

from mlfx.serving.inference import load_artifact, load_from_mlflow, predict_labels

if TYPE_CHECKING:
    from mlfx.registry.models import ModelRegistry

logger = logging.getLogger(__name__)


def resolve_and_predict(
    symbol: str,
    tf: str,
    label: str,
    features: pl.DataFrame | dict[str, float],
    *,
    backend: str | None = None,
    registry: ModelRegistry | None = None,
    model_cache: dict[str, Any] | None = None,
    use_mlflow: bool = True,
    mlflow_stage: Literal["Staging", "Production", "Archived", "None"] = "Production",
) -> tuple[np.ndarray, str, dict[str, Any]] | None:
    """Resolve model, load, validate, predict.

    Parameters
    ----------
    symbol
        Trading symbol.
    tf
        Timeframe.
    label
        Label column name.
    features
        Feature DataFrame or dict.
    backend
        Optional backend filter. When provided, only models from this backend
        are considered. When None, the best model across all backends is used.
    registry
        Optional model registry instance.
    model_cache
        Optional cache for loaded models.
    use_mlflow
        Whether to try MLflow registry first. Falls back to JSON registry if unavailable.
    mlflow_stage
        Stage to load from MLflow registry. Defaults to "Production".

    Returns
    -------
    tuple[np.ndarray, str, dict[str, Any]] | None
        (predictions, artifact_path, entry) on success, or None on failure.
    """
    # Try MLflow first if enabled
    if use_mlflow:
        result = _resolve_from_mlflow(
            symbol, tf, label, features, backend=backend,
            model_cache=model_cache, stage=mlflow_stage,
        )
        if result is not None:
            return result

    # Fall back to JSON registry
    return _resolve_from_json_registry(
        symbol, tf, label, features, backend=backend,
        registry=registry, model_cache=model_cache,
    )


def _resolve_from_mlflow(
    symbol: str,
    tf: str,
    label: str,
    features: pl.DataFrame | dict[str, float],
    *,
    backend: str | None = None,
    model_cache: dict[str, Any] | None = None,
    stage: str = "Production",
) -> tuple[np.ndarray, str, dict[str, Any]] | None:
    """Resolve model from MLflow Model Registry."""
    try:
        from mlfx.config.mlflow import get_mlflow_config

        config = get_mlflow_config()
        if not config.is_mlflow_available():
            return None

        model_name = config.model_name(symbol, tf, label, backend)
        cache_key = f"mlflow:{model_name}:{stage}"

        if model_cache is not None and cache_key in model_cache:
            model = model_cache[cache_key]
        else:
            model = load_from_mlflow(model_name, stage=stage)  # type: ignore[arg-type]
            if model_cache is not None:
                model_cache[cache_key] = model

        # Get feature columns
        feature_cols = _get_feature_cols(features)

        # Prepare features
        X = _prepare_features(features, feature_cols)

        # Predict
        predictions = _run_prediction(model, X, features, label, feature_cols)

        # Build entry dict
        entry = {
            "model_name": model_name,
            "stage": stage,
            "symbol": symbol,
            "tf": tf,
            "backend": backend,
            "label": label,
        }

        return predictions, f"mlflow://{model_name}/{stage}", entry

    except Exception as exc:  # noqa: BLE001
        logger.debug("MLflow resolution failed: %s", exc)
        return None


def _resolve_from_json_registry(
    symbol: str,
    tf: str,
    label: str,
    features: pl.DataFrame | dict[str, float],
    *,
    backend: str | None = None,
    registry: ModelRegistry | None = None,
    model_cache: dict[str, Any] | None = None,
) -> tuple[np.ndarray, str, dict[str, Any]] | None:
    """Resolve model from JSON registry (original implementation)."""
    if registry is None:
        from mlfx.registry import get_registry  # noqa: PLC0415

        registry = get_registry(use_mlflow=False)

    entry = registry.best_model(symbol=symbol, tf=tf, label=label, backend=backend)
    if entry is None:
        return None

    artifact_path = entry.get("artifact_path", "")
    if not artifact_path or not Path(artifact_path).exists():
        return None

    feature_cols = entry.get("feature_columns")
    if feature_cols is None:
        feature_cols = _get_feature_cols(features)

    X = _prepare_features(features, feature_cols)

    if model_cache is not None and artifact_path in model_cache:
        model = model_cache[artifact_path]
    else:
        try:
            model = load_artifact(artifact_path)
        except FileNotFoundError:
            return None
        if model_cache is not None:
            model_cache[artifact_path] = model

    predictions = _run_prediction(model, X, features, label, feature_cols)
    return predictions, artifact_path, entry


def _get_feature_cols(features: pl.DataFrame | dict[str, float]) -> list[str]:
    """Extract feature columns from features."""
    if isinstance(features, pl.DataFrame):
        from mlfx.serving.features import select_numeric_feature_columns

        return select_numeric_feature_columns(features)
    return sorted(features.keys())


def _prepare_features(
    features: pl.DataFrame | dict[str, float],
    feature_cols: list[str],
) -> np.ndarray:
    """Prepare features for prediction."""
    if isinstance(features, pl.DataFrame):
        missing = [c for c in feature_cols if c not in features.columns]
        if missing:
            raise ValueError(f"Missing features: {missing}")
        X = features.select(feature_cols).to_numpy().astype(np.float32)
    else:
        missing = [c for c in feature_cols if c not in features]
        if missing:
            raise ValueError(f"Missing features: {missing}")
        X = np.array([[features[c] for c in feature_cols]], dtype=np.float32)

    return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)


def _run_prediction(
    model: Any,
    X: np.ndarray,
    features: pl.DataFrame | dict[str, float],
    label: str,
    feature_cols: list[str],
) -> np.ndarray:
    """Run prediction with model."""
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

    return (raw_preds - 2).astype(np.int32)  # remap [0,4] → [-2,2]
