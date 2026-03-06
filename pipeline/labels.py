"""
pipeline/labels.py
==================
ATR-based labeling pipeline for XAUUSD OHLCV feature data.

Label classes (5-class ordinal):
  +2  STRONG LONG  — close_ahead > close * (1 + 2 × atr_mult × atr / close)
  +1  WEAK LONG    — close_ahead > close * (1 + atr_mult × atr / close)
   0  NEUTRAL      — otherwise
  −1  WEAK SHORT   — close_ahead < close * (1 − atr_mult × atr / close)
  −2  STRONG SHORT — close_ahead < close * (1 − 2 × atr_mult × atr / close)

Output: data/labels/{symbol}/{tf}/*.parquet

Skill: @skill:polars-dataframes
  resources: polars-playbook.md → shift() to create look-ahead target
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

FEATURES_DIR = Path("data/features")
LABELS_DIR = Path("data/labels")

HORIZONS: list[int] = [5, 10, 20]
ATR_MULT: float = 0.5  # threshold = atr_mult × atr_14


# ── Core labeling ─────────────────────────────────────────────────────────────


def add_labels(
    df: pl.DataFrame,
    horizons: list[int] = HORIZONS,
    atr_col: str = "atr_14",
    atr_mult: float = ATR_MULT,
) -> pl.DataFrame:
    """
    Add forward-looking ordinal labels for each horizon N.

    For horizon N:
        close_ahead_N  = close.shift(-N)
        threshold      = close × (atr_mult × atr_14 / close)
                       = atr_mult × atr_14          (additive ATR band)
        strong_threshold = 2.0 × threshold

        label_N = +2  if close_ahead_N > close + strong_threshold
                = +1  if close_ahead_N > close + threshold (but not strong)
                = −2  if close_ahead_N < close - strong_threshold
                = −1  if close_ahead_N < close - threshold (but not strong)
                = 0   otherwise (or if close_ahead_N is null)

    Args:
        df:       OHLCV DataFrame with [close, atr_14] columns.
        horizons: List of look-ahead bar counts.
        atr_col:  ATR column to use for threshold.
        atr_mult: ATR multiplier to scale the threshold.

    Returns:
        DataFrame with additional columns: close_ahead_N, label_N per horizon.
    """
    if atr_col not in df.columns:
        raise ValueError(f"Column '{atr_col}' not found. Run feature pipeline first.")

    for n in horizons:
        ahead_col = f"close_ahead_{n}"
        label_col = f"label_{n}"
        threshold = atr_mult * pl.col(atr_col)
        strong_threshold = 2.0 * threshold

        df = df.with_columns(pl.col("close").shift(-n).alias(ahead_col)).with_columns(
            pl.when(pl.col(ahead_col).is_null())
            .then(pl.lit(None, dtype=pl.Int8))
            .when(pl.col(ahead_col) > pl.col("close") + strong_threshold)
            .then(pl.lit(2, dtype=pl.Int8))
            .when(pl.col(ahead_col) > pl.col("close") + threshold)
            .then(pl.lit(1, dtype=pl.Int8))
            .when(pl.col(ahead_col) < pl.col("close") - strong_threshold)
            .then(pl.lit(-2, dtype=pl.Int8))
            .when(pl.col(ahead_col) < pl.col("close") - threshold)
            .then(pl.lit(-1, dtype=pl.Int8))
            .otherwise(pl.lit(0, dtype=pl.Int8))
            .alias(label_col)
        )

    return df


# ── Class balance ─────────────────────────────────────────────────────────────


def compute_class_balance(df: pl.DataFrame, label_col: str) -> dict:
    """
    Compute class counts and ratios for a label column.

    Args:
        df:        DataFrame containing the label column.
        label_col: Column name (e.g. 'label_10').

    Returns:
        Dict with keys 'counts' and 'ratios':
          counts: {-1: int, 0: int, 1: int}
          ratios: {-1: float, 0: float, 1: float}
    """
    valid = df.drop_nulls(label_col)[label_col]
    total = len(valid)
    if total == 0:
        return {"counts": {-2: 0, -1: 0, 0: 0, 1: 0, 2: 0}, "ratios": {-2: 0.0, -1: 0.0, 0: 0.0, 1: 0.0, 2: 0.0}}

    counts_series = valid.value_counts().sort(
        "label_col" if "label_col" in valid.name else label_col
    )
    # Use explicit groupby-style aggregation
    counts = {k: int(valid.filter(valid == k).len()) for k in (-2, -1, 0, 1, 2)}
    ratios = {k: round(v / total, 4) for k, v in counts.items()}
    return {"counts": counts, "ratios": ratios}


# ── Stratified train/test split (time-aware) ──────────────────────────────────


def stratified_train_test_split(
    df: pl.DataFrame,
    label_col: str,
    test_size: float = 0.2,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Time-aware train/test split — chronological cutoff, no shuffle.

    The test set is always the LAST `test_size` fraction of rows.
    Reports class distribution in both splits.

    Args:
        df:         DataFrame sorted by timestamp.
        label_col:  Label column name.
        test_size:  Fraction of data to use as test (default 0.2).

    Returns:
        (train_df, test_df)
    """
    n = len(df)
    cut = int(n * (1.0 - test_size))
    train_df = df[:cut]
    test_df = df[cut:]

    train_balance = compute_class_balance(train_df.drop_nulls(label_col), label_col)
    test_balance = compute_class_balance(test_df.drop_nulls(label_col), label_col)

    logger.info(
        "Train split: %d rows  class dist: %s", len(train_df), train_balance["ratios"]
    )
    logger.info(
        "Test  split: %d rows  class dist: %s", len(test_df), test_balance["ratios"]
    )

    return train_df, test_df


# ── File-level runner ─────────────────────────────────────────────────────────


def run_label_pipeline(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    horizons: list[int] = HORIZONS,
    atr_mult: float = ATR_MULT,
    force: bool = False,
) -> dict:
    """
    Read feature Parquet files for symbol/tf, add labels, save to data/labels/.

    Args:
        symbol:   Trading pair (default 'XAUUSD').
        tf:       Timeframe (default '1H').
        horizons: Look-ahead bar counts.
        atr_mult: ATR threshold multiplier.
        force:    Overwrite existing label files.

    Returns:
        Summary dict: {processed, skipped, total_bars, label_cols}
    """
    in_dir = FEATURES_DIR / symbol / tf
    out_dir = LABELS_DIR / symbol / tf
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {"processed": 0, "skipped": 0, "total_bars": 0, "label_cols": []}

    parquet_files = sorted(in_dir.glob("*.parquet")) if in_dir.exists() else []
    if not parquet_files:
        logger.warning("No feature files found for %s %s in %s", symbol, tf, in_dir)
        return stats

    for in_file in parquet_files:
        out_file = out_dir / in_file.name
        if out_file.exists() and not force:
            stats["skipped"] += 1
            continue

        df = pl.read_parquet(in_file)
        if df.is_empty():
            continue

        if "atr_14" not in df.columns:
            logger.warning("'atr_14' not in %s — skipping", in_file.name)
            continue

        df = add_labels(df, horizons=horizons, atr_mult=atr_mult)

        pq.write_table(
            df.to_arrow(),
            str(out_file),
            compression="snappy",
        )

        label_cols = [f"label_{n}" for n in horizons]
        stats["processed"] += 1
        stats["total_bars"] += len(df)
        stats["label_cols"] = label_cols

        # Log class balance for middle horizon
        mid_horizon = horizons[len(horizons) // 2]
        balance = compute_class_balance(
            df.drop_nulls(f"label_{mid_horizon}"), f"label_{mid_horizon}"
        )
        logger.info(
            "✓ %s %s %s → %d bars  label_%d dist: %s",
            symbol,
            tf,
            in_file.stem,
            len(df),
            mid_horizon,
            balance["ratios"],
        )

    return stats


# ── CLI ───────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Label pipeline for ML_FX")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument(
        "--horizons",
        nargs="+",
        type=int,
        default=[5, 10, 20],
        help="Look-ahead bar counts",
    )
    parser.add_argument("--atr-mult", type=float, default=0.5)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    result = run_label_pipeline(
        symbol=args.symbol,
        tf=args.tf,
        horizons=args.horizons,
        atr_mult=args.atr_mult,
        force=args.force,
    )
    print(
        f"Processed: {result['processed']}  Skipped: {result['skipped']}  "
        f"Bars: {result['total_bars']}  Labels: {result['label_cols']}"
    )
