"""
Core labeling logic moved from the legacy `pipeline/labels.py` module.
"""

from __future__ import annotations

import logging

import polars as pl

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths

logger = logging.getLogger(__name__)

HORIZONS: list[int] = [5, 10, 20]
ATR_MULT: float = 0.5


def add_labels(
    df: pl.DataFrame,
    horizons: list[int] = HORIZONS,
    atr_col: str = "atr_14",
    atr_mult: float = ATR_MULT,
) -> pl.DataFrame:
    """Add forward-looking ordinal labels for each horizon."""
    if atr_col not in df.columns:
        raise ValueError(f"Column '{atr_col}' not found. Run feature pipeline first.")

    for horizon in horizons:
        ahead_col = f"close_ahead_{horizon}"
        label_col = f"label_{horizon}"
        threshold = atr_mult * pl.col(atr_col)
        strong_threshold = 2.0 * threshold

        df = df.with_columns(pl.col("close").shift(-horizon).alias(ahead_col)).with_columns(
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


def compute_class_balance(df: pl.DataFrame, label_col: str) -> dict:
    """Compute class counts and ratios for a label column."""
    valid = df.drop_nulls(label_col)[label_col]
    total = len(valid)
    if total == 0:
        empty = {-2: 0, -1: 0, 0: 0, 1: 0, 2: 0}
        return {"counts": empty, "ratios": {key: 0.0 for key in empty}}

    counts = {key: int(valid.filter(valid == key).len()) for key in (-2, -1, 0, 1, 2)}
    ratios = {key: round(value / total, 4) for key, value in counts.items()}
    return {"counts": counts, "ratios": ratios}


def stratified_train_test_split(
    df: pl.DataFrame,
    label_col: str,
    test_size: float = 0.2,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Chronological train/test split with balance logging."""
    cut = int(len(df) * (1.0 - test_size))
    train_df = df[:cut]
    test_df = df[cut:]
    train_balance = compute_class_balance(train_df.drop_nulls(label_col), label_col)
    test_balance = compute_class_balance(test_df.drop_nulls(label_col), label_col)
    logger.info("Train split: %d rows  class dist: %s", len(train_df), train_balance["ratios"])
    logger.info("Test split: %d rows  class dist: %s", len(test_df), test_balance["ratios"])
    return train_df, test_df


def run_label_pipeline(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    horizons: list[int] = HORIZONS,
    atr_period: int = 14,
    atr_mult: float = ATR_MULT,
    force: bool = False,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> dict:
    """Read feature parquet files, add labels, and persist outputs."""
    from mlfx.pipeline._parquet_loop import process_parquet_files

    in_dir = paths.features_dir(symbol, tf)
    out_dir = paths.labels_dir(symbol, tf)
    atr_col = f"atr_{atr_period}"
    label_cols = [f"label_{n}" for n in horizons]

    if not in_dir.exists():
        logger.warning("No feature files found for %s %s in %s", symbol, tf, in_dir)
        return {"processed": 0, "skipped": 0, "total_bars": 0, "label_cols": label_cols}

    def transform(df: pl.DataFrame) -> pl.DataFrame:
        if df.is_empty() or atr_col not in df.columns:
            return pl.DataFrame()
        return add_labels(df, horizons=horizons, atr_col=atr_col, atr_mult=atr_mult)

    stats = process_parquet_files(
        in_dir,
        out_dir,
        transform,
        force=force,
        on_processed=lambda _: {"label_cols": label_cols},
    )
    if "label_cols" not in stats:
        stats["label_cols"] = label_cols
    return stats
