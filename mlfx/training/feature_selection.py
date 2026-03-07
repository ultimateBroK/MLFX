"""Shared feature-selection helpers for training backends."""

from __future__ import annotations

import polars as pl

DEFAULT_FEATURE_BLACKLIST = {
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

NUMERIC_DTYPES = (pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int8)


def select_numeric_feature_columns(
    df: pl.DataFrame,
    blacklist: set[str] | None = None,
) -> list[str]:
    """Select numeric feature columns while excluding price/target fields."""
    active_blacklist = blacklist or DEFAULT_FEATURE_BLACKLIST
    return [
        column
        for column in df.columns
        if column not in active_blacklist and df[column].dtype in NUMERIC_DTYPES
    ]
