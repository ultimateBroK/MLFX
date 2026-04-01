"""Technical Analysis indicator functions using TA-Lib.

This module provides technical analysis indicator functions that operate
on Polars DataFrames containing OHLCV data.

Available functions:
- add_rsi: Relative Strength Index
- add_macd: Moving Average Convergence Divergence
- add_atr: Average True Range
- add_ema: Exponential Moving Average
- add_normalized_distances: Normalize price distances by ATR
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import polars as pl
import talib

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _add_ta(df: pl.DataFrame, name: str, values: np.ndarray) -> pl.DataFrame:
    """Append a TA-Lib result array as a Float64 column."""
    return df.with_columns(pl.Series(name, values, dtype=pl.Float64))


def add_rsi(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
    """Calculate RSI (Relative Strength Index).

    Args:
        df: DataFrame with 'close' column.
        period: RSI period (default: 14).

    Returns:
        DataFrame with 'rsi_{period}' column added.
    """
    return _add_ta(df, f"rsi_{period}", talib.RSI(df["close"].to_numpy(), timeperiod=period))


def add_macd(
    df: pl.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
) -> pl.DataFrame:
    """Calculate MACD (Moving Average Convergence Divergence).

    Args:
        df: DataFrame with 'close' column.
        fast: Fast EMA period (default: 12).
        slow: Slow EMA period (default: 26).
        signal: Signal line period (default: 9).

    Returns:
        DataFrame with 'macd', 'macd_signal', 'macd_hist' columns added.
    """
    macd, sig, hist = talib.MACD(
        df["close"].to_numpy(),
        fastperiod=fast,
        slowperiod=slow,
        signalperiod=signal,
    )
    return (
        df.pipe(_add_ta, "macd", macd)
        .pipe(_add_ta, "macd_signal", sig)
        .pipe(_add_ta, "macd_hist", hist)
    )


def add_atr(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
    """Calculate ATR (Average True Range).

    Args:
        df: DataFrame with 'high', 'low', 'close' columns.
        period: ATR period (default: 14).

    Returns:
        DataFrame with 'atr_{period}' column added.
    """
    return _add_ta(
        df,
        f"atr_{period}",
        talib.ATR(
            df["high"].to_numpy(),
            df["low"].to_numpy(),
            df["close"].to_numpy(),
            timeperiod=period,
        ),
    )


def add_ema(df: pl.DataFrame, periods: list[int] | None = None) -> pl.DataFrame:
    """Calculate one or more EMAs (Exponential Moving Averages).

    Args:
        df: DataFrame with 'close' column.
        periods: List of EMA periods (default: [20, 50, 200]).

    Returns:
        DataFrame with 'ema_{period}' columns added.
    """
    if periods is None:
        periods = [20, 50, 200]
    close = df["close"].to_numpy()
    for period in periods:
        df = _add_ta(df, f"ema_{period}", talib.EMA(close, timeperiod=period))
    return df


def add_normalized_distances(df: pl.DataFrame, atr_col: str = "atr_14") -> pl.DataFrame:
    """Normalize price-distance columns by ATR.

    Divides all columns starting with 'dist_to_' or 'pp_dist_' by the ATR column
    to create ATR-normalized distance features.

    Args:
        df: DataFrame with distance columns and ATR column.
        atr_col: Name of the ATR column to use for normalization (default: 'atr_14').

    Returns:
        DataFrame with '{distance_col}_atr' columns added.
    """
    if atr_col not in df.columns:
        logger.warning("Column '%s' not found — skipping normalization", atr_col)
        return df

    distance_cols = [
        col for col in df.columns if col.startswith("dist_to_") or col.startswith("pp_dist_")
    ]
    exprs = [
        (pl.col(col) / pl.col(atr_col)).alias(f"{col}_atr")
        for col in distance_cols
    ]
    return df.with_columns(exprs) if exprs else df
