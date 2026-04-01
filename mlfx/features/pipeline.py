"""Feature engineering pipeline orchestration.

This module provides high-level functions for building and running
the complete feature engineering pipeline on OHLCV data.

Available functions:
- build_feature_pipeline: Transform a single DataFrame with all features
- run_feature_pipeline: Process OHLCV files and persist feature parquets
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import polars as pl

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths
from mlfx.features.ta import (
    add_atr,
    add_ema,
    add_macd,
    add_normalized_distances,
    add_rsi,
)
from mlfx.features.technical.killzone import add_killzone_features
from mlfx.features.technical.sr_pp import add_sr_pp_features

if TYPE_CHECKING:
    from mlfx.config.schema import FeatureConfig

logger = logging.getLogger(__name__)


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

    Transforms OHLCV data by adding:
    - Killzone session features (London, NY, Asian)
    - Support/Resistance and Pivot Point features
    - RSI indicator
    - MACD indicator
    - ATR indicator
    - EMA indicators
    - Normalized distance features

    All indicator hyper-parameters default to the canonical values. Pass
    explicit values (or unpack a ``FeatureConfig`` instance) to override them.

    Args:
        ohlcv: DataFrame with timestamp, open, high, low, close columns.
        pivot_type: Pivot-point calculation method ('traditional' or 'fibonacci').
        pivot_anchor: Period used for pivot-point anchoring ('daily', 'weekly', etc.).
        ema_periods: List of EMA periods to calculate.
        avg_range_n: Number of bars for average range calculation in killzone.
        rsi_period: RSI period.
        atr_period: ATR period.
        macd_fast: MACD fast EMA period.
        macd_slow: MACD slow EMA period.
        macd_signal: MACD signal line period.

    Returns:
        DataFrame with all feature columns added.
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

    Reads OHLCV parquet files from the input directory, applies the feature
    engineering pipeline, and writes the results to the output directory.

    Args:
        symbol: Instrument symbol (e.g., 'XAUUSD').
        tf: Timeframe string (e.g., '1H', '4H', '1D').
        pivot_type: Pivot-point calculation method.
        pivot_anchor: Period used for pivot-point anchoring.
        force: Reprocess existing output files when ``True``.
        paths: ``ProjectPaths`` instance for path resolution.
        feature_cfg: Optional ``FeatureConfig`` with indicator hyper-parameters.
            Defaults to ``FeatureConfig()`` (canonical values) when ``None``.

    Returns:
        Dictionary with processing statistics:
        - processed: Number of files processed
        - skipped: Number of files skipped
        - total_bars: Total number of bars processed
        - total_features: Number of feature columns generated
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
