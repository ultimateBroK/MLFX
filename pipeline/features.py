"""
pipeline/features.py
====================
Full feature engineering pipeline for XAUUSD OHLCV data.

Steps per bar:
  1. ICT Killzone features     — indicator/killzone.py → add_killzone_features()
  2. S/R + Pivot Point features— indicator/sr_pp.py   → add_sr_pp_features()
  3. TA-Lib momentum/volatility— RSI(14), MACD(12/26/9), ATR(14), EMA(20/50/200)
  4. Order Blocks              — last opposing candle before a strong impulsive move
  5. Fair Value Gaps (FVG)     — 3-candle imbalance pattern
  6. Feature normalization     — ATR-normalized price distances

Output: data/features/{symbol}/{tf}/*.parquet

Skill: @skill:talib-indicators
  resources: talib-playbook.md    → add_ta_column() + RSI/MACD/ATR/EMA patterns
  resources: combined-usecase.md  → feature matrix blueprint
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq
import talib

from indicator.killzone import add_killzone_features
from indicator.sr_pp import add_sr_pp_features

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────

OHLCV_DIR = Path("data/ohlcv")
FEATURES_DIR = Path("data/features")


# ── TA-Lib helpers ────────────────────────────────────────────────────────────


def _add_ta(df: pl.DataFrame, name: str, values: np.ndarray) -> pl.DataFrame:
    """Append a TA-Lib NumPy result array as a Polars Float64 column."""
    return df.with_columns(pl.Series(name, values, dtype=pl.Float64))


def add_rsi(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
    c = df["close"].to_numpy()
    return _add_ta(df, f"rsi_{period}", talib.RSI(c, timeperiod=period))


def add_macd(
    df: pl.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
) -> pl.DataFrame:
    c = df["close"].to_numpy()
    macd, sig, hist = talib.MACD(
        c, fastperiod=fast, slowperiod=slow, signalperiod=signal
    )
    return (
        df.pipe(_add_ta, "macd", macd)
        .pipe(_add_ta, "macd_signal", sig)
        .pipe(_add_ta, "macd_hist", hist)
    )


def add_atr(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
    h, lo, c = df["high"].to_numpy(), df["low"].to_numpy(), df["close"].to_numpy()
    return _add_ta(df, f"atr_{period}", talib.ATR(h, lo, c, timeperiod=period))


def add_ema(df: pl.DataFrame, periods: list[int] = [20, 50, 200]) -> pl.DataFrame:
    c = df["close"].to_numpy()
    for p in periods:
        df = _add_ta(df, f"ema_{p}", talib.EMA(c, timeperiod=p))
    return df


# ── Order Block detection ─────────────────────────────────────────────────────


def add_order_blocks(df: pl.DataFrame, swing_threshold: float = 1.5) -> pl.DataFrame:
    """
    Detect Order Blocks (OB) — ICT concept:
      Bullish OB: last bearish candle (red) before a strong bullish impulse.
      Bearish OB: last bullish candle (green) before a strong bearish impulse.

    Definition used:
      - Impulse = candle body > swing_threshold × previous 5-bar avg body
      - OB = the candle immediately before the impulse, opposing direction

    Adds columns:
        ob_bullish      — bool: bar is a bullish order block
        ob_bearish      — bool: bar is a bearish order block
        ob_bull_high    — float: OB zone high (forward-filled from last bullish OB)
        ob_bull_low     — float: OB zone low
        ob_bear_high    — float: OB zone high (forward-filled from last bearish OB)
        ob_bear_low     — float: OB zone low
        price_in_bull_ob— bool: current close is inside last bullish OB zone
        price_in_bear_ob— bool: current close is inside last bearish OB zone
    """
    body = (pl.col("close") - pl.col("open")).abs()
    bull = pl.col("close") > pl.col("open")  # bullish candle
    bear = pl.col("close") < pl.col("open")  # bearish candle

    avg_body = body.rolling_mean(window_size=5, min_periods=1)
    big_bull = bull & (body > avg_body * swing_threshold)
    big_bear = bear & (body > avg_body * swing_threshold)

    # OB = the candle BEFORE the impulse (shift(1) looks back 1 bar)
    ob_bull = big_bull.shift(-1).fill_null(False) & bear  # last red before strong green
    ob_bear = big_bear.shift(-1).fill_null(False) & bull  # last green before strong red

    df = df.with_columns(
        [
            ob_bull.alias("ob_bullish"),
            ob_bear.alias("ob_bearish"),
        ]
    )

    # Forward-fill OB zone boundaries
    bull_high = (
        pl.when(pl.col("ob_bullish"))
        .then(pl.col("high"))
        .otherwise(None)
        .forward_fill()
    )
    bull_low = (
        pl.when(pl.col("ob_bullish")).then(pl.col("low")).otherwise(None).forward_fill()
    )
    bear_high = (
        pl.when(pl.col("ob_bearish"))
        .then(pl.col("high"))
        .otherwise(None)
        .forward_fill()
    )
    bear_low = (
        pl.when(pl.col("ob_bearish")).then(pl.col("low")).otherwise(None).forward_fill()
    )

    df = df.with_columns(
        [
            bull_high.alias("ob_bull_high"),
            bull_low.alias("ob_bull_low"),
            bear_high.alias("ob_bear_high"),
            bear_low.alias("ob_bear_low"),
        ]
    )

    # Is current price inside OB zone?
    c = pl.col("close")
    df = df.with_columns(
        [
            ((c >= pl.col("ob_bull_low")) & (c <= pl.col("ob_bull_high"))).alias(
                "price_in_bull_ob"
            ),
            ((c >= pl.col("ob_bear_low")) & (c <= pl.col("ob_bear_high"))).alias(
                "price_in_bear_ob"
            ),
        ]
    )

    return df


# ── Fair Value Gap (FVG) detection ────────────────────────────────────────────


def add_fair_value_gaps(df: pl.DataFrame) -> pl.DataFrame:
    """
    Detect Fair Value Gaps (FVG) — 3-candle imbalance pattern.

    Bullish FVG: low[0] > high[2]  (gap between bar-2 high and bar-0 low)
    Bearish FVG: high[0] < low[2]  (gap between bar-2 low and bar-0 high)

    Index convention (Pine-style, looking backward):
      bar-2 = shift(2), bar-1 = shift(1), bar-0 = current

    Adds columns:
        fvg_bullish     — bool: bullish FVG present at this bar
        fvg_bearish     — bool: bearish FVG present at this bar
        fvg_bull_top    — float: upper edge of last bullish FVG (forward-filled)
        fvg_bull_bot    — float: lower edge of last bullish FVG
        fvg_bear_top    — float: upper edge of last bearish FVG
        fvg_bear_bot    — float: lower edge of last bearish FVG
        price_in_bull_fvg — bool: price is inside a bullish FVG zone
        price_in_bear_fvg — bool: price is inside a bearish FVG zone
    """
    h2 = pl.col("high").shift(2)
    lo2 = pl.col("low").shift(2)
    lo0 = pl.col("low")
    h0 = pl.col("high")

    bull_fvg = lo0 > h2  # current low above bar-2 high → gap below
    bear_fvg = h0 < lo2  # current high below bar-2 low → gap above

    df = df.with_columns(
        [
            bull_fvg.alias("fvg_bullish"),
            bear_fvg.alias("fvg_bearish"),
        ]
    )

    # FVG zone edges: bullish gap is [high[2], low[0]]
    bull_top = pl.when(pl.col("fvg_bullish")).then(lo0).otherwise(None).forward_fill()
    bull_bot = pl.when(pl.col("fvg_bullish")).then(h2).otherwise(None).forward_fill()
    # Bearish gap is [high[0], low[2]]
    bear_top = pl.when(pl.col("fvg_bearish")).then(lo2).otherwise(None).forward_fill()
    bear_bot = pl.when(pl.col("fvg_bearish")).then(h0).otherwise(None).forward_fill()

    df = df.with_columns(
        [
            bull_top.alias("fvg_bull_top"),
            bull_bot.alias("fvg_bull_bot"),
            bear_top.alias("fvg_bear_top"),
            bear_bot.alias("fvg_bear_bot"),
        ]
    )

    c = pl.col("close")
    df = df.with_columns(
        [
            ((c >= pl.col("fvg_bull_bot")) & (c <= pl.col("fvg_bull_top"))).alias(
                "price_in_bull_fvg"
            ),
            ((c >= pl.col("fvg_bear_bot")) & (c <= pl.col("fvg_bear_top"))).alias(
                "price_in_bear_fvg"
            ),
        ]
    )

    return df


# ── ATR normalization ─────────────────────────────────────────────────────────


def add_normalized_distances(df: pl.DataFrame, atr_col: str = "atr_14") -> pl.DataFrame:
    """
    Normalize key price distances by ATR to make them scale-invariant.

    Requires `atr_14` and `pp_dist_to_p`, `pp_dist_to_r1`, `pp_dist_to_s1` columns.
    Adds `*_atr` suffix variants for each distance column.
    """
    if atr_col not in df.columns:
        logger.warning("Column '%s' not found — skipping normalization", atr_col)
        return df

    distance_cols = [
        c for c in df.columns if c.startswith("dist_to_") or c.startswith("pp_dist_")
    ]

    norm_exprs = [
        (pl.col(d) / pl.col(atr_col)).alias(f"{d}_atr")
        for d in distance_cols
        if d in df.columns
    ]
    if norm_exprs:
        df = df.with_columns(norm_exprs)

    return df


# ── Full feature pipeline ─────────────────────────────────────────────────────


def build_feature_pipeline(
    ohlcv: pl.DataFrame,
    pivot_type: str = "traditional",
    pivot_anchor: str = "daily",
    ema_periods: list[int] | None = None,
    avg_range_n: int = 5,
) -> pl.DataFrame:
    """
    Apply the complete feature engineering pipeline to an OHLCV DataFrame.

    Pipeline steps:
        1. ICT Killzone features
        2. S/R + Pivot Points features
        3. TA-Lib: RSI(14), MACD, ATR(14), EMA(20/50/200)
        4. Order Blocks
        5. Fair Value Gaps
        6. ATR-normalized distances

    Args:
        ohlcv:        OHLCV DataFrame with columns [timestamp, open, high, low, close].
                      Must have UTC timestamps.
        pivot_type:   Pivot calculation type (default "traditional").
        pivot_anchor: Pivot anchor timeframe (default "daily").
        ema_periods:  EMA periods to compute (default [20, 50, 200]).
        avg_range_n:  Killzone avg range lookback sessions (default 5).

    Returns:
        Enriched DataFrame with all feature columns appended.
    """
    if ema_periods is None:
        ema_periods = [20, 50, 200]

    if ohlcv.is_empty():
        logger.warning("build_feature_pipeline received empty DataFrame")
        return ohlcv

    # Ensure UTC timezone
    if ohlcv["timestamp"].dtype in (pl.Datetime("us", None), pl.Datetime("ns", None)):
        ohlcv = ohlcv.with_columns(pl.col("timestamp").dt.replace_time_zone("UTC"))

    ohlcv = ohlcv.sort("timestamp")

    logger.debug("Step 1/6 — ICT Killzone features (%d bars)", len(ohlcv))
    ohlcv = add_killzone_features(ohlcv, avg_range_n=avg_range_n)

    logger.debug("Step 2/6 — S/R + Pivot Point features")
    ohlcv = add_sr_pp_features(ohlcv, pivot_type=pivot_type, anchor=pivot_anchor)

    logger.debug("Step 3/6 — TA-Lib indicators")
    ohlcv = add_rsi(ohlcv, period=14)
    ohlcv = add_macd(ohlcv)
    ohlcv = add_atr(ohlcv, period=14)
    ohlcv = add_ema(ohlcv, periods=ema_periods)

    logger.debug("Step 4/6 — Order Blocks")
    ohlcv = add_order_blocks(ohlcv)

    logger.debug("Step 5/6 — Fair Value Gaps")
    ohlcv = add_fair_value_gaps(ohlcv)

    logger.debug("Step 6/6 — ATR normalization")
    ohlcv = add_normalized_distances(ohlcv)

    return ohlcv


# ── File-based runner ─────────────────────────────────────────────────────────


def run_feature_pipeline(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    pivot_type: str = "traditional",
    pivot_anchor: str = "daily",
    force: bool = False,
) -> dict:
    """
    Read all OHLCV Parquet files for a symbol/tf, apply the feature pipeline,
    and write enriched Parquet to data/features/{symbol}/{tf}/.

    Args:
        symbol:       Trading pair (default "XAUUSD").
        tf:           Timeframe key (default "1H").
        pivot_type:   Pivot type for sr_pp (default "traditional").
        pivot_anchor: Pivot anchor (default "daily").
        force:        Overwrite existing feature files.

    Returns:
        Summary dict: {"processed": int, "skipped": int, "total_bars": int, "total_features": int}
    """
    in_dir = OHLCV_DIR / symbol / tf
    out_dir = FEATURES_DIR / symbol / tf
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {"processed": 0, "skipped": 0, "total_bars": 0, "total_features": 0}

    parquet_files = sorted(in_dir.glob("*.parquet")) if in_dir.exists() else []
    if not parquet_files:
        logger.warning("No OHLCV files found for %s %s in %s", symbol, tf, in_dir)
        return stats

    # Process month files individually (memory-efficient)
    for in_file in parquet_files:
        out_file = out_dir / in_file.name
        if out_file.exists() and not force:
            stats["skipped"] += 1
            logger.debug("Skip %s (exists)", out_file)
            continue

        ohlcv = pl.read_parquet(in_file)
        if ohlcv.is_empty():
            continue

        features = build_feature_pipeline(
            ohlcv,
            pivot_type=pivot_type,
            pivot_anchor=pivot_anchor,
        )

        pq.write_table(
            features.to_arrow(),
            str(out_file),
            compression="snappy",
        )

        n_bars = len(features)
        n_feat = len(features.columns)
        stats["processed"] += 1
        stats["total_bars"] += n_bars
        stats["total_features"] = n_feat  # same for all files
        logger.info(
            "✓ %s %s %s → %d bars × %d features → %s",
            symbol,
            tf,
            in_file.stem,
            n_bars,
            n_feat,
            out_file,
        )

    return stats


# ── CLI entrypoint ────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Build feature pipeline for XAUUSD")
    parser.add_argument("--symbol", default="XAUUSD", help="Symbol name")
    parser.add_argument("--tf", default="1H", help="Timeframe (e.g. 1H)")
    parser.add_argument("--pivot", default="traditional", help="Pivot type")
    parser.add_argument("--anchor", default="daily", help="Pivot anchor TF")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    result = run_feature_pipeline(
        symbol=args.symbol,
        tf=args.tf,
        pivot_type=args.pivot,
        pivot_anchor=args.anchor,
        force=args.force,
    )
    print(
        f"Processed: {result['processed']}  Skipped: {result['skipped']}  "
        f"Bars: {result['total_bars']}  Features: {result['total_features']}"
    )
