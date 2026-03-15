"""
Shared utilities for indicator feature engineering.
"""

from __future__ import annotations

import polars as pl


def _ensure_utc(df: pl.DataFrame, ts_col: str = "timestamp") -> pl.DataFrame:
    """Ensure the DataFrame timestamp column has a UTC timezone."""
    ts = df[ts_col]
    if ts.dtype in (
        pl.Datetime("us", "UTC"),
        pl.Datetime("ns", "UTC"),
        pl.Datetime("ms", "UTC"),
    ):
        return df
    if ts.dtype in (
        pl.Datetime("us", None),
        pl.Datetime("ns", None),
        pl.Datetime("ms", None),
    ):
        return df.with_columns(pl.col(ts_col).dt.replace_time_zone("UTC"))
    return df
