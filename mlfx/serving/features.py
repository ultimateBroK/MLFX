"""Serving-side feature loading and selection helpers.

This module intentionally avoids importing from ``mlfx.training.*`` so batch
inference stays decoupled from training internals.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths

FEATURE_BLACKLIST = {
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "tick_count",
    "close_ahead_5",
    "close_ahead_10",
    "close_ahead_20",
    "label_5",
    "label_10",
    "label_20",
}

NUMERIC_DTYPES = (pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int16, pl.Int8)


def load_feature_dataset(
    symbol: str,
    tf: str,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> pl.DataFrame | None:
    """Load and concatenate monthly feature parquet files in chronological order."""
    in_dir = paths.features_dir(symbol, tf)
    files = sorted(Path(in_dir).glob("*.parquet"))
    if not files:
        return None
    frames = [pl.read_parquet(file_path) for file_path in files]
    return pl.concat(frames).sort("timestamp")


def select_numeric_feature_columns(
    df: pl.DataFrame,
    *,
    blacklist: set[str] | None = None,
) -> list[str]:
    """Select numeric model-input columns while excluding raw target/price fields."""
    active_blacklist = blacklist or FEATURE_BLACKLIST
    return [
        column
        for column in df.columns
        if column not in active_blacklist and df[column].dtype in NUMERIC_DTYPES
    ]
