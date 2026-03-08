"""
Killzone feature engineering moved from the legacy `indicators/` package.
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

import polars as pl

from ._utils import _ensure_utc

TZ_ET = ZoneInfo("America/New_York")
TZ_UTC = ZoneInfo("UTC")

KILLZONES: dict[str, tuple[int, int, int, int]] = {
    "asia": (20, 0, 0, 0),
    "london": (2, 0, 5, 0),
    "nyam": (9, 30, 11, 0),
    "nylunch": (12, 0, 13, 0),
    "nypm": (13, 30, 16, 0),
}


def _add_et_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Add ET-local hour, minute, weekday, date columns (used for session math)."""
    return df.with_columns(
        pl.col("timestamp").dt.convert_time_zone("America/New_York").alias("_ts_et")
    ).with_columns(
        pl.col("_ts_et").dt.hour().alias("_et_hour"),
        pl.col("_ts_et").dt.minute().alias("_et_min"),
        pl.col("_ts_et").dt.weekday().alias("_et_dow"),
        pl.col("_ts_et").dt.date().alias("_et_date"),
    )


def _in_session_expr(sh: int, sm: int, eh: int, em: int, name: str) -> pl.Expr:
    """Return a boolean expression indicating whether a bar is inside a session."""
    start_min = sh * 60 + sm
    end_min = eh * 60 + em
    bar_min = pl.col("_et_hour") * 60 + pl.col("_et_min")

    if name == "asia":
        expr = bar_min >= start_min
    elif start_min < end_min:
        expr = (bar_min >= start_min) & (bar_min < end_min)
    else:
        expr = (bar_min >= start_min) | (bar_min < end_min)

    return expr.alias(f"in_{name}")


def add_session_flags(df: pl.DataFrame) -> pl.DataFrame:
    """Add boolean session flag columns for each killzone."""
    df = _ensure_utc(df)
    df = _add_et_columns(df)

    exprs = [
        _in_session_expr(sh, sm, eh, em, name)
        for name, (sh, sm, eh, em) in KILLZONES.items()
    ]
    df = df.with_columns(exprs)
    return df.drop(["_ts_et", "_et_hour", "_et_min", "_et_dow", "_et_date"])


def compute_killzone_pivots(df: pl.DataFrame) -> pl.DataFrame:
    """Compute per-session pivot levels and derived distance features."""
    new_cols: list[pl.Expr] = []

    for kz in KILLZONES:
        in_col = f"in_{kz}"
        session_id = (
            (pl.col(in_col).cast(pl.Int8) - pl.col(in_col).shift(1).cast(pl.Int8))
            .clip(0, 1)
            .cum_sum()
            .alias(f"kz_{kz}_session_id")
        )
        high_expr = pl.when(pl.col(in_col)).then(pl.col("high")).otherwise(None)
        low_expr = pl.when(pl.col(in_col)).then(pl.col("low")).otherwise(None)
        new_cols += [
            session_id,
            high_expr.alias(f"_raw_{kz}_high"),
            low_expr.alias(f"_raw_{kz}_low"),
        ]

    df = df.with_columns(new_cols)

    pivot_cols: list[pl.Expr] = []
    for kz in KILLZONES:
        sid = f"kz_{kz}_session_id"
        pivot_cols += [
            pl.col(f"_raw_{kz}_high")
            .over(sid)
            .forward_fill()
            .backward_fill()
            .alias(f"kz_{kz}_high"),
            pl.col(f"_raw_{kz}_low")
            .over(sid)
            .forward_fill()
            .backward_fill()
            .alias(f"kz_{kz}_low"),
        ]

    df = df.with_columns(pivot_cols)

    final_cols: list[pl.Expr] = []
    for kz in KILLZONES:
        sid = f"kz_{kz}_session_id"
        final_cols += [
            pl.col("high").cum_max().over(sid).alias(f"kz_{kz}_high"),
            pl.col("low").cum_min().over(sid).alias(f"kz_{kz}_low"),
        ]

    df = df.with_columns(final_cols)

    derived: list[pl.Expr] = []
    for kz in KILLZONES:
        h = pl.col(f"kz_{kz}_high")
        lo = pl.col(f"kz_{kz}_low")
        derived += [
            ((h + lo) / 2).alias(f"kz_{kz}_mid"),
            (h - lo).alias(f"kz_{kz}_range"),
            (pl.col("close") - h).alias(f"dist_to_{kz}_high"),
            (pl.col("close") - lo).alias(f"dist_to_{kz}_low"),
        ]

    df = df.with_columns(derived)
    raw_cols = [c for c in df.columns if c.startswith("_raw_")]
    return df.drop(raw_cols)


def compute_dwm_levels(df: pl.DataFrame) -> pl.DataFrame:
    """Compute day/week/month running levels and previous period levels."""
    df = _ensure_utc(df)

    df = df.with_columns(
        pl.col("timestamp").dt.convert_time_zone("America/New_York").alias("_ts_et")
    ).with_columns(
        pl.col("_ts_et").dt.date().alias("_day"),
        pl.col("_ts_et").dt.year().alias("_year"),
        pl.col("_ts_et").dt.month().alias("_month"),
        (pl.col("_ts_et").dt.year() * 100 + pl.col("_ts_et").dt.week()).alias("_week"),
        (pl.col("_ts_et").dt.year() * 100 + pl.col("_ts_et").dt.month()).alias(
            "_yearmonth"
        ),
    )

    df = df.with_columns(
        pl.col("open").first().over("_day").alias("d_open"),
        pl.col("high").cum_max().over("_day").alias("d_high"),
        pl.col("low").cum_min().over("_day").alias("d_low"),
        pl.col("open").first().over("_week").alias("w_open"),
        pl.col("high").cum_max().over("_week").alias("w_high"),
        pl.col("low").cum_min().over("_week").alias("w_low"),
        pl.col("open").first().over("_yearmonth").alias("m_open"),
        pl.col("high").cum_max().over("_yearmonth").alias("m_high"),
        pl.col("low").cum_min().over("_yearmonth").alias("m_low"),
    )

    day_summary = (
        df.group_by("_day")
        .agg(pl.col("high").max().alias("_dh"), pl.col("low").min().alias("_dl"))
        .sort("_day")
        .with_columns(
            pl.col("_dh").shift(1).alias("pd_high"),
            pl.col("_dl").shift(1).alias("pd_low"),
        )
        .select(["_day", "pd_high", "pd_low"])
    )
    week_summary = (
        df.group_by("_week")
        .agg(pl.col("high").max().alias("_wh"), pl.col("low").min().alias("_wl"))
        .sort("_week")
        .with_columns(
            pl.col("_wh").shift(1).alias("pw_high"),
            pl.col("_wl").shift(1).alias("pw_low"),
        )
        .select(["_week", "pw_high", "pw_low"])
    )
    month_summary = (
        df.group_by("_yearmonth")
        .agg(pl.col("high").max().alias("_mh"), pl.col("low").min().alias("_ml"))
        .sort("_yearmonth")
        .with_columns(
            pl.col("_mh").shift(1).alias("pm_high"),
            pl.col("_ml").shift(1).alias("pm_low"),
        )
        .select(["_yearmonth", "pm_high", "pm_low"])
    )

    df = (
        df.join(day_summary, on="_day", how="left")
        .join(week_summary, on="_week", how="left")
        .join(month_summary, on="_yearmonth", how="left")
    )

    helper_cols = ["_ts_et", "_day", "_year", "_month", "_week", "_yearmonth"]
    return df.drop([c for c in helper_cols if c in df.columns])


def compute_killzone_avg_range(df: pl.DataFrame, n: int = 5) -> pl.DataFrame:
    """Compute rolling average range over the last `n` sessions."""
    for kz in KILLZONES:
        sid_col = f"kz_{kz}_session_id"
        range_col = f"kz_{kz}_range"

        if sid_col not in df.columns or range_col not in df.columns:
            continue

        session_ranges = (
            df.filter(pl.col(f"in_{kz}") | pl.col(f"in_{kz}").shift(-1).is_null())
            .group_by(sid_col)
            .agg(pl.col(range_col).max().alias("_sr"))
            .sort(sid_col)
            .with_columns(
                pl.col("_sr")
                .rolling_mean(window_size=n, min_samples=1)
                .alias(f"kz_{kz}_avg_range")
            )
            .select([sid_col, f"kz_{kz}_avg_range"])
        )

        df = df.join(session_ranges, on=sid_col, how="left")

    return df


def add_killzone_features(df: pl.DataFrame, avg_range_n: int = 5) -> pl.DataFrame:
    """Complete ICT Killzone feature engineering pipeline."""
    df = _ensure_utc(df)
    df = add_session_flags(df)
    df = compute_killzone_pivots(df)
    df = compute_killzone_avg_range(df, n=avg_range_n)
    df = compute_dwm_levels(df)
    return df
