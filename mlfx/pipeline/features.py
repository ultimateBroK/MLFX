"""
Core feature engineering pipeline moved from the legacy `pipeline/features.py`.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import polars as pl
import talib

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths
from mlfx.features.indicators.killzone import add_killzone_features
from mlfx.features.indicators.sr_pp import add_sr_pp_features

if TYPE_CHECKING:
    from mlfx.config.schema import FeatureConfig

logger = logging.getLogger(__name__)


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


def add_ema(df: pl.DataFrame, periods: list[int] | None = None) -> pl.DataFrame:
    """Calculate one or more EMAs."""
    if periods is None:
        periods = [20, 50, 200]
    close = df["close"].to_numpy()
    for period in periods:
        df = _add_ta(df, f"ema_{period}", talib.EMA(close, timeperiod=period))
    return df


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
    rsi_period: int = 14,
    atr_period: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
) -> pl.DataFrame:
    """Apply the complete feature engineering pipeline.

    All indicator hyper-parameters default to the canonical values.  Pass
    explicit values (or unpack a ``FeatureConfig`` instance) to override them.
    """
    if ema_periods is None:
        ema_periods = [20, 50, 200]
    if ohlcv.is_empty():
        return ohlcv
    if ohlcv["timestamp"].dtype in (pl.Datetime("us", None), pl.Datetime("ns", None)):
        ohlcv = ohlcv.with_columns(pl.col("timestamp").dt.replace_time_zone("UTC"))

    ohlcv = ohlcv.sort("timestamp")
    ohlcv = add_killzone_features(ohlcv, avg_range_n=avg_range_n)
    ohlcv = add_sr_pp_features(ohlcv, pivot_type=pivot_type, anchor=pivot_anchor)
    ohlcv = add_rsi(ohlcv, period=rsi_period)
    ohlcv = add_macd(ohlcv, fast=macd_fast, slow=macd_slow, signal=macd_signal)
    ohlcv = add_atr(ohlcv, period=atr_period)
    ohlcv = add_ema(ohlcv, periods=ema_periods)
    return add_normalized_distances(ohlcv, atr_col=f"atr_{atr_period}")


def run_feature_pipeline(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    pivot_type: str = "traditional",
    pivot_anchor: str = "daily",
    force: bool = False,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
    feature_cfg: FeatureConfig | None = None,
) -> dict:
    """Build and persist feature parquet files for one symbol/timeframe.

    Args:
        symbol: Instrument symbol.
        tf: Timeframe string.
        pivot_type: Pivot-point calculation method.
        pivot_anchor: Period used for pivot-point anchoring.
        force: Reprocess existing output files when ``True``.
        paths: ``ProjectPaths`` instance.
        feature_cfg: Optional ``FeatureConfig`` with indicator hyper-parameters.
            Defaults to ``FeatureConfig()`` (canonical values) when ``None``.
    """
    from mlfx.config.schema import FeatureConfig as _FeatureConfig  # lazy — avoids import at module load
    from mlfx.pipeline._parquet_loop import process_parquet_files

    cfg = feature_cfg if feature_cfg is not None else _FeatureConfig()

    in_dir = paths.ohlcv_dir(symbol, tf)
    out_dir = paths.features_dir(symbol, tf)

    if not in_dir.exists():
        logger.warning("No OHLCV files found for %s %s in %s", symbol, tf, in_dir)
        return {"processed": 0, "skipped": 0, "total_bars": 0, "total_features": 0}

    def transform(ohlcv: pl.DataFrame) -> pl.DataFrame:
        return build_feature_pipeline(
            ohlcv,
            pivot_type=pivot_type,
            pivot_anchor=pivot_anchor,
            rsi_period=cfg.rsi_period,
            atr_period=cfg.atr_period,
            macd_fast=cfg.macd_fast,
            macd_slow=cfg.macd_slow,
            macd_signal=cfg.macd_signal,
            ema_periods=list(cfg.ema_periods),
            avg_range_n=cfg.avg_range_n,
        )

    stats = process_parquet_files(
        in_dir,
        out_dir,
        transform,
        force=force,
        on_processed=lambda df: {"total_features": len(df.columns)},
    )
    if "total_features" not in stats:
        stats["total_features"] = 0
    return stats
