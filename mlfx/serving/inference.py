"""Model loading and prediction adapters for serving.

Provides a minimal compatibility layer across currently persisted artifact
formats:
- sklearn/nixtla objects exposing ``predict(X)``
- MLForecast (uses underlying LGBMClassifier + preprocess)
- dict payloads containing ``clf`` and ``scaler`` (online SGD backend)
- PyTorch state_dict payloads (LSTM, BiLSTM, CNN-LSTM, Transformer)

Security
--------
Only load artifacts from trusted sources (local disk, user-configured paths).
Both ``pickle.load`` and ``torch.load(weights_only=False)`` can execute
arbitrary code if the file is tampered with.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl


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
    label_col: str,
    feature_cols: list[str],
) -> tuple[np.ndarray, pl.Series]:
    """Run prediction for MLForecast using preprocess + underlying model.

    MLForecast.predict() is for forecasting (needs horizon), not scoring.
    We use preprocess() + the underlying LGBMClassifier instead.

    Returns (predictions, ds_series) where ds_series has timestamps for each
    prediction (preprocess may drop rows, so length matches preds).
    """
    from mlfx.training.backends.mlforecast import prepare_nixtla_df

    subset, _ = prepare_nixtla_df(df, label_col)
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
    label_col: str | None = None,
    feature_cols: list[str] | None = None,
) -> np.ndarray:
    """Run prediction with best-effort adaptation by artifact type.

    Returns class labels in backend-native encoding (typically 0..4).

    For MLForecast models, pass df, label_col, and feature_cols to use
    preprocess + underlying model (MLForecast.predict is for forecasting only).
    """
    # MLForecast: use preprocess + underlying model, not predict(horizon).
    if _is_mlforecast(model):
        if df is not None and label_col and feature_cols:
            preds, ds_series = _predict_mlforecast(model, df, label_col, feature_cols)
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
