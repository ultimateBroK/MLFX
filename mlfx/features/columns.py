"""Shared feature-column selection helpers used by training and serving."""

from __future__ import annotations

import polars as pl

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

NUMERIC_DTYPES = (
    pl.Float64,
    pl.Float32,
    pl.Int64,
    pl.Int32,
    pl.Int16,
    pl.Int8,
)


def select_numeric_feature_columns(
    df: pl.DataFrame,
    blacklist: set[str] | None = None,
) -> list[str]:
    """Return numeric model-input columns excluding target/price fields."""
    active_blacklist = blacklist or FEATURE_BLACKLIST
    return [
        column
        for column in df.columns
        if column not in active_blacklist and df[column].dtype in NUMERIC_DTYPES
    ]
