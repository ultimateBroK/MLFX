"""
Core feature engineering pipeline moved from the legacy `pipeline/features.py`.
"""

from __future__ import annotations

import logging

import numpy as np
import polars as pl
import pyarrow.parquet as pq
import talib

from mlfx.config.paths import DEFAULT_PATHS
from mlfx.features.indicators.killzone import add_killzone_features
from mlfx.features.indicators.sr_pp import add_sr_pp_features

logger = logging.getLogger(__name__)

OHLCV_DIR = DEFAULT_PATHS.ohlcv_root
FEATURES_DIR = DEFAULT_PATHS.features_root


def _add_ta(df: pl.DataFrame, name: str, values: np.ndarray) -> pl.DataFrame:
    """Append a TA-Lib result array as a Float64 column."""
    return df.with_columns(pl.Series(name, values, dtype=pl.Float64))


def add_rsi(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
    """Calculate RSI."""
    return _add_ta(df, f"rsi_{period}", talib.RSI(df["close"].to_numpy(), timeperiod=period))


def add_macd(
    df: pl.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
) -> pl.DataFrame:
    """Calculate MACD, signal, and histogram."""
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
    """Calculate ATR."""
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


def add_ema(df: pl.DataFrame, periods: list[int] = [20, 50, 200]) -> pl.DataFrame:
    """Calculate one or more EMAs."""
    close = df["close"].to_numpy()
    for period in periods:
        df = _add_ta(df, f"ema_{period}", talib.EMA(close, timeperiod=period))
    return df


def add_order_blocks(df: pl.DataFrame, swing_threshold: float = 1.5) -> pl.DataFrame:
    """Detect simplified bullish/bearish order-block zones."""
    body = (pl.col("close") - pl.col("open")).abs()
    bull = pl.col("close") > pl.col("open")
    bear = pl.col("close") < pl.col("open")
    avg_body = body.rolling_mean(window_size=5, min_samples=1)
    big_bull = bull & (body > avg_body * swing_threshold)
    big_bear = bear & (body > avg_body * swing_threshold)

    df = df.with_columns(
        (big_bull.shift(-1).fill_null(False) & bear).alias("ob_bullish"),
        (big_bear.shift(-1).fill_null(False) & bull).alias("ob_bearish"),
    )

    bull_high = pl.when(pl.col("ob_bullish")).then(pl.col("high")).otherwise(None).forward_fill()
    bull_low = pl.when(pl.col("ob_bullish")).then(pl.col("low")).otherwise(None).forward_fill()
    bear_high = pl.when(pl.col("ob_bearish")).then(pl.col("high")).otherwise(None).forward_fill()
    bear_low = pl.when(pl.col("ob_bearish")).then(pl.col("low")).otherwise(None).forward_fill()

    df = df.with_columns(
        bull_high.alias("ob_bull_high"),
        bull_low.alias("ob_bull_low"),
        bear_high.alias("ob_bear_high"),
        bear_low.alias("ob_bear_low"),
    )

    close = pl.col("close")
    return df.with_columns(
        ((close >= pl.col("ob_bull_low")) & (close <= pl.col("ob_bull_high"))).alias(
            "price_in_bull_ob"
        ),
        ((close >= pl.col("ob_bear_low")) & (close <= pl.col("ob_bear_high"))).alias(
            "price_in_bear_ob"
        ),
    )


def add_fair_value_gaps(df: pl.DataFrame) -> pl.DataFrame:
    """Detect simple bullish/bearish fair-value gaps."""
    high_2 = pl.col("high").shift(2)
    low_2 = pl.col("low").shift(2)
    low_0 = pl.col("low")
    high_0 = pl.col("high")

    df = df.with_columns(
        (low_0 > high_2).alias("fvg_bullish"),
        (high_0 < low_2).alias("fvg_bearish"),
    )

    bull_top = pl.when(pl.col("fvg_bullish")).then(low_0).otherwise(None).forward_fill()
    bull_bot = pl.when(pl.col("fvg_bullish")).then(high_2).otherwise(None).forward_fill()
    bear_top = pl.when(pl.col("fvg_bearish")).then(low_2).otherwise(None).forward_fill()
    bear_bot = pl.when(pl.col("fvg_bearish")).then(high_0).otherwise(None).forward_fill()

    df = df.with_columns(
        bull_top.alias("fvg_bull_top"),
        bull_bot.alias("fvg_bull_bot"),
        bear_top.alias("fvg_bear_top"),
        bear_bot.alias("fvg_bear_bot"),
    )

    close = pl.col("close")
    return df.with_columns(
        ((close >= pl.col("fvg_bull_bot")) & (close <= pl.col("fvg_bull_top"))).alias(
            "price_in_bull_fvg"
        ),
        ((close >= pl.col("fvg_bear_bot")) & (close <= pl.col("fvg_bear_top"))).alias(
            "price_in_bear_fvg"
        ),
    )


def add_normalized_distances(df: pl.DataFrame, atr_col: str = "atr_14") -> pl.DataFrame:
    """Normalize price-distance columns by ATR."""
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


def build_feature_pipeline(
    ohlcv: pl.DataFrame,
    pivot_type: str = "traditional",
    pivot_anchor: str = "daily",
    ema_periods: list[int] | None = None,
    avg_range_n: int = 5,
) -> pl.DataFrame:
    """Apply the complete feature engineering pipeline."""
    if ema_periods is None:
        ema_periods = [20, 50, 200]
    if ohlcv.is_empty():
        return ohlcv
    if ohlcv["timestamp"].dtype in (pl.Datetime("us", None), pl.Datetime("ns", None)):
        ohlcv = ohlcv.with_columns(pl.col("timestamp").dt.replace_time_zone("UTC"))

    ohlcv = ohlcv.sort("timestamp")
    ohlcv = add_killzone_features(ohlcv, avg_range_n=avg_range_n)
    ohlcv = add_sr_pp_features(ohlcv, pivot_type=pivot_type, anchor=pivot_anchor)
    ohlcv = add_rsi(ohlcv, period=14)
    ohlcv = add_macd(ohlcv)
    ohlcv = add_atr(ohlcv, period=14)
    ohlcv = add_ema(ohlcv, periods=ema_periods)
    ohlcv = add_order_blocks(ohlcv)
    ohlcv = add_fair_value_gaps(ohlcv)
    return add_normalized_distances(ohlcv)


def run_feature_pipeline(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    pivot_type: str = "traditional",
    pivot_anchor: str = "daily",
    force: bool = False,
) -> dict:
    """Build and persist feature parquet files for one symbol/timeframe."""
    in_dir = OHLCV_DIR / symbol / tf
    out_dir = FEATURES_DIR / symbol / tf
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {"processed": 0, "skipped": 0, "total_bars": 0, "total_features": 0}
    parquet_files = sorted(in_dir.glob("*.parquet")) if in_dir.exists() else []
    if not parquet_files:
        logger.warning("No OHLCV files found for %s %s in %s", symbol, tf, in_dir)
        return stats

    for in_file in parquet_files:
        out_file = out_dir / in_file.name
        if out_file.exists() and not force:
            stats["skipped"] += 1
            continue

        ohlcv = pl.read_parquet(in_file)
        if ohlcv.is_empty():
            continue

        features = build_feature_pipeline(
            ohlcv,
            pivot_type=pivot_type,
            pivot_anchor=pivot_anchor,
        )
        pq.write_table(features.to_arrow(), str(out_file), compression="snappy")

        stats["processed"] += 1
        stats["total_bars"] += len(features)
        stats["total_features"] = len(features.columns)
    return stats
