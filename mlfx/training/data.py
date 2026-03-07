"""Shared dataset loading helpers for training backends."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths


def load_labelled_dataset(
    symbol: str,
    tf: str,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> pl.DataFrame | None:
    """Load and timestamp-sort all label parquet files for a symbol/timeframe."""
    labels_dir = paths.labels_dir(symbol, tf)
    parquet_files = sorted(labels_dir.glob("*.parquet")) if labels_dir.exists() else []
    if not parquet_files:
        return None

    frames = [pl.read_parquet(file_path) for file_path in parquet_files]
    if not frames:
        return None

    return pl.concat(frames).sort("timestamp")


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
