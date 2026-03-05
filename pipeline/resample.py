"""
pipeline/resample.py
====================
Resample raw XAUUSD tick Parquet files into OHLCV bars.

Supported timeframes: 1m, 5m, 15m, 30m, 1H, 2H, 4H, 1D
Output: data/ohlcv/{symbol}/{tf}/*.parquet

Skill: @skill:polars-dataframes
  resources: polars-playbook.md  → group_by_dynamic pattern
  resources: pyarrow-playbook.md → partitioned Parquet write
  resources: combined-usecase.md → end-to-end blueprint
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

RAW_DIR = Path("data/raw")
OHLCV_DIR = Path("data/ohlcv")

# Polars group_by_dynamic duration strings
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

# Minimum ticks required for a bar to be considered valid (avoid ghost bars)
MIN_TICKS = 5


# ── Core resample function ────────────────────────────────────────────────────


def resample_to_ohlcv(
    tick_df: pl.DataFrame,
    period: str = "1h",
    min_ticks: int = MIN_TICKS,
) -> pl.DataFrame:
    """
    Resample a tick DataFrame (bid/ask) into OHLCV bars.

    Uses mid-price: (bid + ask) / 2.
    Handles gaps: bars with fewer than `min_ticks` are filtered.
    Result is sorted ascending by timestamp.

    Args:
        tick_df:    DataFrame with columns [timestamp (Datetime UTC), bid, ask].
        period:     Polars duration string — "1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d".
        min_ticks:  Discard bars with fewer ticks (default 5).

    Returns:
        OHLCV DataFrame with columns:
            timestamp, open, high, low, close, volume, tick_count
    """
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
            [
                mid.first().alias("open"),
                mid.max().alias("high"),
                mid.min().alias("low"),
                mid.last().alias("close"),
                ((pl.col("ask_volume") + pl.col("bid_volume")) / 2)
                .sum()
                .alias("volume"),
                pl.len().cast(pl.Int32).alias("tick_count"),
            ]
        )
        .sort("timestamp")
    )

    # Drop bars with too few ticks (weekend gaps, data holes)
    ohlcv = ohlcv.filter(pl.col("tick_count") >= min_ticks)

    # Sanity check: high >= low, no negative prices
    ohlcv = ohlcv.filter(
        (pl.col("high") >= pl.col("low")) & (pl.col("close") > 0) & (pl.col("open") > 0)
    )

    return ohlcv


# ── Gap detection ─────────────────────────────────────────────────────────────


def detect_gaps(ohlcv: pl.DataFrame, period: str) -> pl.DataFrame:
    """
    Identify gaps (missing bars) in an OHLCV DataFrame.

    Args:
        ohlcv:  Sorted OHLCV DataFrame with `timestamp` column.
        period: Expected bar duration (e.g. "1h").

    Returns:
        DataFrame of gap rows with columns [gap_start, gap_end, gap_bars].
    """
    if len(ohlcv) < 2:
        return pl.DataFrame(
            schema={
                "gap_start": pl.Datetime("us", "UTC"),
                "gap_end": pl.Datetime("us", "UTC"),
                "gap_bars": pl.Int64,
            }
        )

    # Duration in milliseconds for the period
    _duration_ms = {
        "1m": 60_000,
        "5m": 300_000,
        "15m": 900_000,
        "1h": 3_600_000,
        "4h": 14_400_000,
        "1d": 86_400_000,
    }
    step_ms = _duration_ms.get(period.lower(), 3_600_000)

    diff = (
        ohlcv.with_columns(
            [
                pl.col("timestamp").diff().dt.total_milliseconds().alias("diff_ms"),
                pl.col("timestamp").shift(1).alias("prev_ts"),
            ]
        )
        .filter(pl.col("diff_ms") > step_ms * 1.5)  # gap = more than 1.5× expected step
        .select(
            [
                pl.col("prev_ts").alias("gap_start"),
                pl.col("timestamp").alias("gap_end"),
                (pl.col("diff_ms") / step_ms).cast(pl.Int64).alias("gap_bars"),
            ]
        )
    )
    return diff


# ── Month-file loader ─────────────────────────────────────────────────────────


def _load_month_ticks(parquet_file: Path) -> pl.DataFrame | None:
    """Load a single monthly Parquet file into a tick DataFrame."""
    if not parquet_file.exists():
        return None

    df = pl.read_parquet(parquet_file)
    if df.is_empty():
        return None

    # Ensure UTC timezone tag
    ts_col = "timestamp"
    if df[ts_col].dtype in (
        pl.Datetime("us", None),
        pl.Datetime("ms", None),
        pl.Datetime("ns", None),
    ):
        df = df.with_columns(
            pl.col(ts_col).dt.replace_time_zone("UTC").dt.cast_time_unit("us")
        )

    return df.sort(ts_col)


# ── Single-timeframe resample for a symbol ────────────────────────────────────


def resample_symbol_tf(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    force: bool = False,
) -> dict:
    """
    Resample all raw tick data for a symbol into one OHLCV Parquet per month
    at the given timeframe. Skips already-processed months unless `force=True`.

    Args:
        symbol: Trading pair name (default "XAUUSD").
        tf:     Timeframe key from TIMEFRAMES (default "1H").
        force:  Overwrite existing output files.

    Returns:
        Summary dict: {"processed": int, "skipped": int, "total_bars": int}
    """
    if tf not in TIMEFRAMES:
        raise ValueError(f"Unknown timeframe '{tf}'. Choose from: {list(TIMEFRAMES)}")

    period = TIMEFRAMES[tf]
    out_dir = OHLCV_DIR / symbol / tf
    raw_root = RAW_DIR / symbol

    out_dir.mkdir(parents=True, exist_ok=True)

    if not raw_root.exists():
        logger.warning("Raw directory not found: %s", raw_root)
        return {"processed": 0, "skipped": 0, "total_bars": 0}

    # Discover flat Parquet files: data/raw/XAUUSD/2015-01.parquet
    raw_files = sorted(raw_root.glob("????-??.parquet"))
    if not raw_files:
        logger.warning("No raw Parquet files found in %s", raw_root)
        return {"processed": 0, "skipped": 0, "total_bars": 0}

    stats = {"processed": 0, "skipped": 0, "total_bars": 0}

    for raw_file in raw_files:
        ym = raw_file.stem  # e.g. "2024-01"
        out_file = out_dir / f"{ym}.parquet"

        if out_file.exists() and not force:
            logger.debug("Skip %s %s %s (already exists)", symbol, tf, ym)
            stats["skipped"] += 1
            continue

        ticks = _load_month_ticks(raw_file)
        if ticks is None or ticks.is_empty():
            logger.warning("No tick data in %s", raw_file)
            continue

        ohlcv = resample_to_ohlcv(ticks, period=period)
        if ohlcv.is_empty():
            logger.warning("Empty OHLCV after resample: %s %s %s", symbol, tf, ym)
            continue

        pq.write_table(
            ohlcv.to_arrow(),
            str(out_file),
            compression="snappy",
            row_group_size=50_000,
        )

        n_bars = len(ohlcv)
        stats["processed"] += 1
        stats["total_bars"] += n_bars
        logger.info("✓ %s %s %s → %d bars → %s", symbol, tf, ym, n_bars, out_file)

    return stats


# ── Full multi-TF resample ────────────────────────────────────────────────────


def resample_all_timeframes(
    symbol: str = "XAUUSD",
    timeframes: list[str] | None = None,
    force: bool = False,
) -> dict[str, dict]:
    """
    Resample raw tick data for a symbol into all supported timeframes.

    Args:
        symbol:     Trading pair (default "XAUUSD").
        timeframes: Subset of TIMEFRAMES to compute (default: all).
        force:      Overwrite existing output files.

    Returns:
        Dict mapping tf → summary stats.
    """
    targets = timeframes or list(TIMEFRAMES)
    results: dict[str, dict] = {}

    for tf in targets:
        logger.info("Resampling %s %s ...", symbol, tf)
        results[tf] = resample_symbol_tf(symbol=symbol, tf=tf, force=force)

    total = sum(v["total_bars"] for v in results.values())
    logger.info(
        "Done — %d timeframes | %d total bars",
        len([v for v in results.values() if v["processed"] > 0]),
        total,
    )
    return results


# ── CLI entrypoint ────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Resample XAUUSD tick data to OHLCV")
    parser.add_argument("--symbol", default="XAUUSD", help="Symbol name")
    parser.add_argument(
        "--tf", default=None, help="Single timeframe (e.g. 1H). Default: all"
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    if args.tf:
        stats = resample_symbol_tf(symbol=args.symbol, tf=args.tf, force=args.force)
        print(stats)
    else:
        stats = resample_all_timeframes(symbol=args.symbol, force=args.force)
        for tf, s in stats.items():
            print(
                f"  {tf:4s}  processed={s['processed']}  skipped={s['skipped']}  bars={s['total_bars']}"
            )
