"""
Core resampling logic moved from the legacy `pipeline/resample.py` module.
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq

from mlfx.config.paths import DEFAULT_PATHS

logger = logging.getLogger(__name__)

RAW_DIR = DEFAULT_PATHS.raw_root
OHLCV_DIR = DEFAULT_PATHS.ohlcv_root

TIMEFRAMES: dict[str, str] = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1H": "1h",
    "2H": "2h",
    "4H": "4h",
    "1D": "1d",
}

MIN_TICKS = 5


def resample_to_ohlcv(
    tick_df: pl.DataFrame,
    period: str = "1h",
    min_ticks: int = MIN_TICKS,
) -> pl.DataFrame:
    """Resample tick data to OHLCV bars using mid-price."""
    if tick_df.is_empty():
        return pl.DataFrame(
            schema={
                "timestamp": pl.Datetime("us", "UTC"),
                "open": pl.Float64,
                "high": pl.Float64,
                "low": pl.Float64,
                "close": pl.Float64,
                "volume": pl.Float64,
                "tick_count": pl.Int32,
            }
        )

    mid = (pl.col("bid") + pl.col("ask")) / 2
    ohlcv = (
        tick_df.sort("timestamp")
        .group_by_dynamic("timestamp", every=period, closed="left")
        .agg(
            mid.first().alias("open"),
            mid.max().alias("high"),
            mid.min().alias("low"),
            mid.last().alias("close"),
            ((pl.col("ask_volume") + pl.col("bid_volume")) / 2).sum().alias("volume"),
            pl.len().cast(pl.Int32).alias("tick_count"),
        )
        .sort("timestamp")
    )
    ohlcv = ohlcv.filter(pl.col("tick_count") >= min_ticks)
    ohlcv = ohlcv.filter(
        (pl.col("high") >= pl.col("low")) & (pl.col("close") > 0) & (pl.col("open") > 0)
    )
    return ohlcv


def detect_gaps(ohlcv: pl.DataFrame, period: str) -> pl.DataFrame:
    """Identify missing-bar gaps in an OHLCV series."""
    if len(ohlcv) < 2:
        return pl.DataFrame(
            schema={
                "gap_start": pl.Datetime("us", "UTC"),
                "gap_end": pl.Datetime("us", "UTC"),
                "gap_bars": pl.Int64,
            }
        )

    duration_ms = {
        "1m": 60_000,
        "5m": 300_000,
        "15m": 900_000,
        "1h": 3_600_000,
        "4h": 14_400_000,
        "1d": 86_400_000,
    }
    step_ms = duration_ms.get(period.lower(), 3_600_000)
    return (
        ohlcv.with_columns(
            pl.col("timestamp").diff().dt.total_milliseconds().alias("diff_ms"),
            pl.col("timestamp").shift(1).alias("prev_ts"),
        )
        .filter(pl.col("diff_ms") > step_ms * 1.5)
        .select(
            pl.col("prev_ts").alias("gap_start"),
            pl.col("timestamp").alias("gap_end"),
            (pl.col("diff_ms") / step_ms).cast(pl.Int64).alias("gap_bars"),
        )
    )


def _load_month_ticks(parquet_file: Path) -> pl.DataFrame | None:
    """Load a single monthly Parquet file into a tick DataFrame."""
    if not parquet_file.exists():
        return None

    df = pl.read_parquet(parquet_file)
    if df.is_empty():
        return None

    if df["timestamp"].dtype in (
        pl.Datetime("us", None),
        pl.Datetime("ms", None),
        pl.Datetime("ns", None),
    ):
        df = df.with_columns(
            pl.col("timestamp").dt.replace_time_zone("UTC").dt.cast_time_unit("us")
        )
    return df.sort("timestamp")


def resample_symbol_tf(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    force: bool = False,
) -> dict:
    """Resample all raw monthly tick files for one symbol/timeframe."""
    if tf not in TIMEFRAMES:
        raise ValueError(f"Unknown timeframe '{tf}'. Choose from: {list(TIMEFRAMES)}")

    period = TIMEFRAMES[tf]
    out_dir = OHLCV_DIR / symbol / tf
    raw_root = RAW_DIR / symbol
    out_dir.mkdir(parents=True, exist_ok=True)

    if not raw_root.exists():
        logger.warning("Raw directory not found: %s", raw_root)
        return {"processed": 0, "skipped": 0, "total_bars": 0}

    raw_files = sorted(raw_root.glob("????-??.parquet"))
    if not raw_files:
        logger.warning("No raw Parquet files found in %s", raw_root)
        return {"processed": 0, "skipped": 0, "total_bars": 0}

    stats = {"processed": 0, "skipped": 0, "total_bars": 0}
    for raw_file in raw_files:
        ym = raw_file.stem
        out_file = out_dir / f"{ym}.parquet"
        if out_file.exists() and not force:
            stats["skipped"] += 1
            continue

        ticks = _load_month_ticks(raw_file)
        if ticks is None or ticks.is_empty():
            continue

        ohlcv = resample_to_ohlcv(ticks, period=period)
        if ohlcv.is_empty():
            continue

        pq.write_table(
            ohlcv.to_arrow(),
            str(out_file),
            compression="snappy",
            row_group_size=50_000,
        )

        stats["processed"] += 1
        stats["total_bars"] += len(ohlcv)
        logger.info("✓ %s %s %s → %d bars → %s", symbol, tf, ym, len(ohlcv), out_file)

    return stats


def resample_all_timeframes(
    symbol: str = "XAUUSD",
    timeframes: list[str] | None = None,
    force: bool = False,
) -> dict[str, dict]:
    """Resample one symbol into all requested timeframes."""
    targets = timeframes or list(TIMEFRAMES)
    results: dict[str, dict] = {}
    for tf in targets:
        results[tf] = resample_symbol_tf(symbol=symbol, tf=tf, force=force)
    return results
