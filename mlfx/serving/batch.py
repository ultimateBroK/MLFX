"""Batch inference runner.

Reads the latest OHLCV / feature data for a symbol, runs the feature pipeline,
loads the best registered model, and writes predictions to a parquet file.

Usage::

    from mlfx.serving.batch import run_batch_inference

    result = run_batch_inference(symbol="XAUUSD", tf="1H", label_col="label_10")
    print(result)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths
from mlfx.serving.features import load_feature_dataset, select_numeric_feature_columns
from mlfx.serving.inference import load_artifact, predict_labels

logger = logging.getLogger(__name__)


def run_batch_inference(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label_col: str = "label_10",
    output_path: Path | None = None,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> dict[str, Any]:
    """Run batch inference over the latest feature data.

    1. Load the feature + label dataset from disk.
    2. Look up the best registered model.
    3. Run inference and append a ``prediction`` column.
    4. Write results to *output_path* (or ``outputs/predictions/``).

    Returns
    -------
    dict
        Summary with ``rows``, ``artifact_path``, and ``output_path``.
    """
    from mlfx.registry.models import get_registry  # noqa: PLC0415
    df = load_feature_dataset(symbol, tf, paths=paths)
    if df is None or df.is_empty():
        logger.error("No feature data found for %s %s", symbol, tf)
        return {"rows": 0, "artifact_path": "", "output_path": ""}

    reg = get_registry()
    entry = reg.best_model(symbol=symbol, tf=tf, label_col=label_col)
    if entry is None:
        logger.error("No registered model for %s/%s/%s", symbol, tf, label_col)
        return {"rows": 0, "artifact_path": "", "output_path": ""}

    artifact_path = entry.get("artifact_path", "")
    if not artifact_path or not Path(artifact_path).exists():
        logger.error("Artifact not found: %s", artifact_path)
        return {"rows": 0, "artifact_path": artifact_path, "output_path": ""}

    model = load_artifact(artifact_path)
    feature_cols = entry.get("feature_columns") or select_numeric_feature_columns(df)
    missing = [column for column in feature_cols if column not in df.columns]
    if missing:
        logger.error("Missing feature columns required by model: %s", missing[:10])
        return {"rows": 0, "artifact_path": artifact_path, "output_path": ""}
    X = df.select(feature_cols).to_numpy()

    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    raw_preds = predict_labels(model, X)
    predictions = (raw_preds - 2).tolist()  # remap [0,4] → [-2,2]

    result_df = df.with_columns(pl.Series("prediction", predictions, dtype=pl.Int8))

    out_dir = output_path or (paths.outputs_root / "predictions" / symbol / tf)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{label_col}_predictions.parquet"
    result_df.write_parquet(out_file)
    logger.info("Batch inference complete: %d rows → %s", len(result_df), out_file)

    return {
        "rows": len(result_df),
        "artifact_path": artifact_path,
        "output_path": str(out_file),
    }

