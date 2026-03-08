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

import polars as pl

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths
from mlfx.serving.core import resolve_and_predict
from mlfx.serving.features import load_feature_dataset

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
    df = load_feature_dataset(symbol, tf, paths=paths)
    if df is None or df.is_empty():
        logger.error("No feature data found for %s %s", symbol, tf)
        return {"rows": 0, "artifact_path": "", "output_path": ""}

    result = resolve_and_predict(symbol, tf, label_col, df)
    if result is None:
        logger.error("No registered model or inference failed for %s/%s/%s", symbol, tf, label_col)
        return {"rows": 0, "artifact_path": "", "output_path": ""}

    predictions, artifact_path, _ = result
    result_df = df.with_columns(pl.Series("prediction", predictions.tolist(), dtype=pl.Int8))

    out_dir = output_path or paths.predictions_dir(symbol, tf)
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

