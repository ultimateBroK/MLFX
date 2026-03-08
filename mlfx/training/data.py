"""Shared dataset loading helpers for training backends and evaluation."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import polars as pl

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths
from mlfx.training.feature_selection import select_numeric_feature_columns

logger = logging.getLogger(__name__)


def load_labelled_dataset(
    symbol: str,
    tf: str,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> pl.DataFrame | None:
    """Load and timestamp-sort all label parquet files for a symbol/timeframe.

    Skips files that fail to load (logs a warning) so that corrupt or
    unreadable files do not block loading the rest.
    """
    labels_dir = paths.labels_dir(symbol, tf)
    parquet_files = sorted(labels_dir.glob("*.parquet")) if labels_dir.exists() else []
    if not parquet_files:
        return None

    frames: list[pl.DataFrame] = []
    for file_path in parquet_files:
        try:
            frames.append(pl.read_parquet(file_path))
        except (OSError, ValueError, RuntimeError) as exc:
            # Broad catch: one corrupt or unreadable file must not block loading the rest.
            logger.warning("Failed to load %s: %s", file_path, exc)

    if not frames:
        return None

    return pl.concat(frames).sort("timestamp")


def prepare_tabular_data(
    symbol: str,
    tf: str,
    label_col: str,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> tuple[np.ndarray, np.ndarray, list[str]] | None:
    """Load, select features, drop nulls, map labels.

    Returns (X, y, feature_cols) or None if data unavailable.
    Labels are mapped from {-2,-1,0,1,2} to {0,1,2,3,4}.
    """
    df = load_labelled_dataset(symbol, tf, paths=paths)
    if df is None or label_col not in df.columns:
        return None

    feature_cols = select_numeric_feature_columns(df)
    subset = df.select(feature_cols + [label_col]).drop_nulls()
    if subset.is_empty():
        return None

    X = subset.select(feature_cols).to_numpy().astype(np.float32)
    y = (subset[label_col].to_numpy() + 2).astype(np.int64)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    return X, y, feature_cols


def build_model_output_path(
    artifact_name: str,
    symbol: str,
    tf: str,
    *,
    suffix: str,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> Path:
    """Build a canonical model artifact path under the shared outputs directory."""
    return paths.models_dir(symbol, tf) / f"{artifact_name}{suffix}"
