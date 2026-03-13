"""Shared dataset loading helpers for training backends and evaluation."""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

import numpy as np
import polars as pl

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths
from mlfx.training.feature_selection import select_numeric_feature_columns

logger = logging.getLogger(__name__)


def _normalize_timestamp_bound(
    value: str | dt.date | dt.datetime | None,
    *,
    end_of_day: bool,
) -> dt.datetime | None:
    """Normalize a compact YYYYMMDD date bound into a naive datetime."""
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        if end_of_day:
            return value.replace(hour=23, minute=59, second=59, microsecond=999999)
        return value.replace(hour=0, minute=0, second=0, microsecond=0)
    if isinstance(value, dt.date):
        if end_of_day:
            return dt.datetime.combine(value, dt.time.max)
        return dt.datetime.combine(value, dt.time.min)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if len(text) != 8 or not text.isdigit():
            raise ValueError(
                f"Unsupported date format '{text}'. Expected compact YYYYMMDD, e.g. 20240131."
            )
        parsed_date = dt.datetime.strptime(text, "%Y%m%d").date()
        if end_of_day:
            return dt.datetime.combine(parsed_date, dt.time.max)
        return dt.datetime.combine(parsed_date, dt.time.min)
    raise TypeError(f"Unsupported timestamp bound type: {type(value)!r}")


def _match_timestamp_timezone(
    value: dt.datetime | None,
    timestamp_dtype: pl.DataType,
) -> dt.datetime | None:
    """Align a datetime bound with the timezone-awareness of the timestamp column."""
    if value is None:
        return None

    timezone: str | None = None
    if isinstance(timestamp_dtype, pl.Datetime):
        timezone = timestamp_dtype.time_zone

    if timezone is None:
        if value.tzinfo is not None:
            return value.astimezone(dt.UTC).replace(tzinfo=None)
        return value

    if value.tzinfo is None:
        return value.replace(tzinfo=dt.timezone.utc)

    return value.astimezone(dt.timezone.utc)


def _filter_dataset_by_timestamp(
    df: pl.DataFrame,
    *,
    train_start: str | dt.date | dt.datetime | None = None,
    train_end: str | dt.date | dt.datetime | None = None,
) -> pl.DataFrame:
    """Filter a dataset by an inclusive timestamp range when bounds are provided."""
    if df.is_empty() or "timestamp" not in df.columns:
        return df

    timestamp_dtype = df.schema["timestamp"]
    start_ts = _match_timestamp_timezone(
        _normalize_timestamp_bound(train_start, end_of_day=False),
        timestamp_dtype,
    )
    end_ts = _match_timestamp_timezone(
        _normalize_timestamp_bound(train_end, end_of_day=True),
        timestamp_dtype,
    )

    if start_ts is None and end_ts is None:
        return df

    if start_ts is not None and end_ts is not None and start_ts > end_ts:
        raise ValueError(
            f"train_start must be <= train_end, got {start_ts.isoformat()} > {end_ts.isoformat()}"
        )

    filtered = df
    if start_ts is not None:
        filtered = filtered.filter(pl.col("timestamp") >= pl.lit(start_ts))
    if end_ts is not None:
        filtered = filtered.filter(pl.col("timestamp") <= pl.lit(end_ts))
    return filtered


def load_labelled_dataset(
    symbol: str,
    tf: str,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
    train_start: str | dt.date | dt.datetime | None = None,
    train_end: str | dt.date | dt.datetime | None = None,
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

    df = pl.concat(frames).sort("timestamp")
    df = _filter_dataset_by_timestamp(
        df,
        train_start=train_start,
        train_end=train_end,
    )
    if df.is_empty():
        return None
    return df


def prepare_tabular_data(
    symbol: str,
    tf: str,
    label: str,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
    train_start: str | dt.date | dt.datetime | None = None,
    train_end: str | dt.date | dt.datetime | None = None,
) -> tuple[np.ndarray, np.ndarray, list[str]] | None:
    """Load, select features, drop nulls, map labels.

    Returns (X, y, feature_cols) or None if data unavailable.
    Labels are mapped from {-2,-1,0,1,2} to {0,1,2,3,4}.
    """
    df = load_labelled_dataset(
        symbol,
        tf,
        paths=paths,
        train_start=train_start,
        train_end=train_end,
    )
    if df is None or label not in df.columns:
        return None

    feature_cols = select_numeric_feature_columns(df)
    subset = df.select(feature_cols + [label]).drop_nulls()
    if subset.is_empty():
        return None

    X = subset.select(feature_cols).to_numpy().astype(np.float32)
    y = (subset[label].to_numpy() + 2).astype(np.int64)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    return X, y, feature_cols


def build_model_output_path(
    artifact_name: str,
    symbol: str,
    tf: str,
    label: str,
    *,
    suffix: str,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> Path:
    """Build a canonical model artifact path under a label-specific outputs directory."""
    return paths.models_dir(symbol, tf) / label / f"{artifact_name}{suffix}"
