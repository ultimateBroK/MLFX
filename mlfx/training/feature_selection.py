"""Shared feature-selection helpers for training backends."""

from __future__ import annotations

import polars as pl

from mlfx.features.columns import (
    FEATURE_BLACKLIST,
    NUMERIC_DTYPES,
    select_numeric_feature_columns as _select_numeric_feature_columns,
)

DEFAULT_FEATURE_BLACKLIST = FEATURE_BLACKLIST


def select_numeric_feature_columns(
    df: pl.DataFrame,
    blacklist: set[str] | None = None,
) -> list[str]:
    """Select numeric feature columns while excluding price/target fields."""
    return _select_numeric_feature_columns(df, blacklist=blacklist)
