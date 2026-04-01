"""Model loading and prediction adapters for serving.

Provides a minimal compatibility layer across currently persisted artifact
formats:
- sklearn/nixtla objects exposing ``predict(X)``
- MLForecast (uses underlying LGBMClassifier + preprocess)
- dict payloads containing ``clf`` and ``scaler`` (online SGD backend)
- PyTorch state_dict payloads (LSTM)
- MLflow Model Registry models

Security
--------
Only load artifacts from trusted sources (local disk, user-configured paths).
Both ``pickle.load`` and ``torch.load(weights_only=False)`` can execute
arbitrary code if the file is tampered with.
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Literal

import numpy as np
import polars as pl

logger = logging.getLogger(__name__)


def load_artifact(artifact_path: str) -> Any:
    """Load a pickle or torch payload from disk.

    Only load artifacts from trusted sources. Both pickle and torch.load
    (with weights_only=False) can execute arbitrary code if the file is
    tampered with.
    """
    path = Path(artifact_path)
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    if path.suffix in (".pt", ".pth"):
        import torch  # noqa: PLC0415

        # weights_only=False: payloads contain clf/scaler or state_dict+metrics,
        # not pure tensors; safe only for trusted artifact paths.
        return torch.load(path, map_location="cpu", weights_only=False)

    with path.open("rb") as file_handle:
        return pickle.load(file_handle)  # noqa: S301  # trusted paths only


def load_from_mlflow(
    model_name: str,
    version: str | int | None = None,
    stage: Literal["Staging", "Production", "Archived", "None"] | None = None,
    tracking_uri: str | None = None,
) -> Any:
    """Load a model from MLflow Model Registry.

    Parameters
    ----------
    model_name
        Registered model name.
    version
        Specific version number. If None, uses stage to determine version.
    stage
        Stage to load from ("Production", "Staging", etc.). Ignored if version is provided.
        Defaults to "Production" if both version and stage are None.
    tracking_uri
        MLflow tracking URI. If None, uses default from config.

    Returns
    -------
    Any
        The loaded model artifact.

    Raises
    ------
    ImportError
        If MLflow is not installed.
    ValueError
        If model is not found.
    """
    try:
        import mlflow  # noqa: PLC0415
        from mlflow.tracking import MlflowClient  # noqa: PLC0415

        from mlfx.config.mlflow import get_mlflow_config

        config = get_mlflow_config(tracking_uri=tracking_uri)
        config.setup_mlflow()

        client = MlflowClient()

        # Determine which version to load
        if version:
            model_version = client.get_model_version(model_name, str(version))
        else:
            target_stage = stage or "Production"
            # Use search_model_versions instead of deprecated get_latest_versions
            filter_string = f"name='{model_name}'"
            versions = list(client.search_model_versions(filter_string, max_results=100))
            # Filter by stage if specified
            if target_stage and target_stage != "None":
                versions = [v for v in versions if v.current_stage == target_stage]
            if not versions:
                # Fall back to any version
                versions = list(client.search_model_versions(filter_string, max_results=100))
            if not versions:
                raise ValueError(f"No versions found for model: {model_name}")
            # Get the latest version (highest version number)
            model_version = max(versions, key=lambda v: int(v.version))

        # Download and load the model
        model_uri = f"models:/{model_name}/{model_version.version}"

        # Try to load as MLflow pyfunc model first
        try:
            return mlflow.pyfunc.load_model(model_uri)
        except Exception:  # noqa: BLE001
            pass

        # Fall back to downloading artifacts and loading manually
        import tempfile  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as tmp_dir:
            local_path = mlflow.artifacts.download_artifacts(
                artifact_uri=model_uri,
                dst_path=tmp_dir,
            )
            # Look for model files in the downloaded directory
            local_path = Path(local_path)
            for pattern in ["*.pkl", "*.pt", "*.pth", "model.pkl"]:
                matches = list(local_path.rglob(pattern))
                if matches:
                    return load_artifact(str(matches[0]))

        raise ValueError(f"Could not find model artifact in {model_uri}")

    except ImportError as e:
        logger.error("MLflow not installed. Run: pixi add mlflow")
        raise ImportError("MLflow is required to load models from registry") from e


def _is_mlforecast(model: Any) -> bool:
    """Check if model is an MLForecast instance (has models_ and preprocess)."""
    return (
        hasattr(model, "models_")
        and hasattr(model, "preprocess")
        and isinstance(getattr(model, "models_", None), dict)
    )


def _predict_mlforecast(
    model: Any,
    df: pl.DataFrame,
    label: str,
    feature_cols: list[str],
) -> tuple[np.ndarray, pl.Series]:
    """Run prediction for MLForecast using preprocess + underlying model.

    MLForecast.predict() is for forecasting (needs horizon), not scoring.
    We use preprocess() + the underlying LGBMClassifier instead.

    Returns (predictions, ds_series) where ds_series has timestamps for each
    prediction (preprocess may drop rows, so length matches preds).
    """
    from mlfx.training.backends.mlf import prepare_nixtla_df

    subset, _ = prepare_nixtla_df(df, label)
    if subset.is_empty():
        return np.array([], dtype=np.int64), pl.Series("ds", [])
    df_pd = subset.to_pandas()
    df_preps = model.preprocess(df_pd, static_features=[])
    X_prep = df_preps.drop(columns=["unique_id", "ds", "y"])
    underlying = next(iter(model.models_.values()))
    preds = np.asarray(underlying.predict(X_prep))
    ds_series = pl.Series("ds", df_preps["ds"].values)
    return preds, ds_series


def predict_labels(
    model: Any,
    X: np.ndarray,
    *,
    df: pl.DataFrame | None = None,
    label: str | None = None,
    feature_cols: list[str] | None = None,
) -> np.ndarray:
    """Run prediction with best-effort adaptation by artifact type.

    Returns class labels in backend-native encoding (typically 0..4).

    For MLForecast models, pass df, label, and feature_cols to use
    preprocess + underlying model (MLForecast.predict is for forecasting only).
    """
    # MLForecast: use preprocess + underlying model, not predict(horizon).
    if _is_mlforecast(model):
        if df is not None and label and feature_cols:
            preds, ds_series = _predict_mlforecast(model, df, label, feature_cols)
            if len(preds) == 0:
                return np.full(len(df), 2, dtype=np.int64)  # neutral for all
            pred_lookup = pl.DataFrame({"ds": ds_series, "_pred": preds})
            if df["timestamp"].dtype != pred_lookup["ds"].dtype:
                pred_lookup = pred_lookup.with_columns(
                    pl.col("ds").dt.replace_time_zone("UTC")
                )
            aligned = (
                df.join(pred_lookup, left_on="timestamp", right_on="ds", how="left")
                .select(pl.col("_pred").fill_null(2))
                .to_numpy()
                .flatten()
            )
            return aligned.astype(np.int64)
        raise ValueError(
            "MLForecast models require batch inference with full labelled history; "
            "single-row API prediction is not supported. Use batch-predict instead."
        )

    # Most sklearn/nixtla objects.
    if hasattr(model, "predict"):
        return np.asarray(model.predict(X))

    # Online SGD backend saves {"clf": clf, "scaler": scaler}.
    if isinstance(model, dict) and "clf" in model and "scaler" in model:
        clf = model["clf"]
        scaler = model["scaler"]
        X_scaled = scaler.transform(X)
        return np.asarray(clf.predict(X_scaled))

    # PyTorch backends save {"state_dict": ..., "metrics": ...}.
    if (
        isinstance(model, dict)
        and "state_dict" in model
        and "metrics" in model
    ):
        from mlfx.serving.torch_adapters import predict_with_torch_model, rebuild_torch_model

        rebuilt = rebuild_torch_model(model)
        seq_len = model["metrics"].get("seq_len", 60)
        return predict_with_torch_model(rebuilt, X, seq_len)

    raise TypeError(
        "Unsupported artifact format for serving. "
        "Expected object with predict(X), dict with clf/scaler, or torch state_dict payload."
    )
