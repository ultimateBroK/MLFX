"""
indicator/killzone.py
====================
Python translation of EMA_RSI.pine (ICT Killzone indicator).

Converts Pine Script ICT Killzone logic into Polars-based feature engineering:
- 5 Killzone sessions (Asia, London, NY AM, NY Lunch, NY PM)
- Killzone pivot High/Low per session
- Day / Week / Month open, high, low levels
- Per-bar feature columns ready for ML consumption

Input DataFrame must have columns:
    timestamp (Datetime, UTC), open, high, low, close, [volume]

All session times are defined in America/New_York (ET).
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

import polars as pl

# ── Timezone ──────────────────────────────────────────────────────────────────
TZ_ET = ZoneInfo("America/New_York")
TZ_UTC = ZoneInfo("UTC")

# ── Killzone definitions (ET local time, HH:MM-HH:MM) ─────────────────────────
# Stored as (start_hour, start_min, end_hour, end_min) in ET.
# End is exclusive — a bar's ET hour must satisfy start <= h < end.
KILLZONES: dict[str, tuple[int, int, int, int]] = {
    "asia": (20, 0, 0, 0),  # 20:00 → 00:00 (next day)
    "london": (2, 0, 5, 0),  # 02:00 → 05:00
    "nyam": (9, 30, 11, 0),  # 09:30 → 11:00
    "nylunch": (12, 0, 13, 0),  # 12:00 → 13:00
    "nypm": (13, 30, 16, 0),  # 13:30 → 16:00
}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _ensure_utc(df: pl.DataFrame) -> pl.DataFrame:
    """Ensure timestamp column is UTC datetime."""
    ts = df["timestamp"]
    if ts.dtype == pl.Datetime("us", "UTC") or ts.dtype == pl.Datetime("ns", "UTC"):
        return df
    if ts.dtype in (
        pl.Datetime("us", None),
        pl.Datetime("ns", None),
        pl.Datetime("ms", None),
    ):
        return df.with_columns(pl.col("timestamp").dt.replace_time_zone("UTC"))
    return df


def _add_et_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Add ET-local hour, minute, weekday, date columns (used for session math)."""
    return df.with_columns(
        pl.col("timestamp").dt.convert_time_zone("America/New_York").alias("_ts_et")
    ).with_columns(
        pl.col("_ts_et").dt.hour().alias("_et_hour"),
        pl.col("_ts_et").dt.minute().alias("_et_min"),
        pl.col("_ts_et").dt.weekday().alias("_et_dow"),  # Mon=1 … Sun=7
        pl.col("_ts_et").dt.date().alias("_et_date"),
    )


def _in_session_expr(sh: int, sm: int, eh: int, em: int, name: str) -> pl.Expr:
    """
    Return a boolean Polars expression that is True when the bar falls inside
    the killzone [start, end) in ET local time.

    Asia session wraps midnight: 20:00–24:00 | 00:00–00:00
    """
    start_min = sh * 60 + sm
    end_min = eh * 60 + em

    bar_min = pl.col("_et_hour") * 60 + pl.col("_et_min")

    if name == "asia":
        # Asia: 20:00 ET → 00:00 ET next day  (wraps midnight)
        # True when bar_min >= 1200 OR bar_min < 0 (i.e., 00:00 exactly excluded)
        # Pine: "2000-0000" means 20:00 to 00:00 (midnight), so 20:00 <= t < 24:00
        expr = bar_min >= start_min
    elif start_min < end_min:
        expr = (bar_min >= start_min) & (bar_min < end_min)
    else:
        # wrap-around (should not happen for remaining KZs, but guard anyway)
        expr = (bar_min >= start_min) | (bar_min < end_min)

    return expr.alias(f"in_{name}")


# ── Killzone Session Flags ────────────────────────────────────────────────────


def add_session_flags(df: pl.DataFrame) -> pl.DataFrame:
    """
    Add boolean columns for each killzone:
        in_asia, in_london, in_nyam, in_nylunch, in_nypm

    Args:
        df: OHLCV DataFrame with UTC `timestamp`.

    Returns:
        df with 5 additional boolean columns.
    """
    df = _ensure_utc(df)
    df = _add_et_columns(df)

    exprs = [
        _in_session_expr(sh, sm, eh, em, name)
        for name, (sh, sm, eh, em) in KILLZONES.items()
    ]
    df = df.with_columns(exprs)
    # drop helper columns
    return df.drop(["_ts_et", "_et_hour", "_et_min", "_et_dow", "_et_date"])


# ── Killzone Pivot High / Low ─────────────────────────────────────────────────


def compute_killzone_pivots(df: pl.DataFrame) -> pl.DataFrame:
    """
    For each killzone session compute the session's pivot high and low.
    A new "session group" starts when the `in_<kz>` flag transitions False→True.

    Adds columns (per killzone `kz` in asia/london/nyam/nylunch/nypm):
        kz_{kz}_high        — running high of the current/last killzone session
        kz_{kz}_low         — running low of the current/last killzone session
        kz_{kz}_mid         — midpoint of high and low
        kz_{kz}_range       — range (high - low) of the current/last session
        kz_{kz}_session_id  — monotonically increasing session counter

    Outside a session the values reflect the *previous* completed session,
    mirroring Pine Script's behaviour of extending pivot lines.

    Args:
        df: DataFrame with in_{kz} boolean columns (output of add_session_flags).

    Returns:
        df with additional killzone pivot columns.
    """
    new_cols: list[pl.Expr] = []

    for kz in KILLZONES:
        in_col = f"in_{kz}"

        # session_id increments each time in_kz goes False→True
        session_id = (
            (pl.col(in_col).cast(pl.Int8) - pl.col(in_col).shift(1).cast(pl.Int8))
            .clip(0, 1)
            .cum_sum()
            .alias(f"kz_{kz}_session_id")
        )

        # running high / low within each session group
        # We group by session_id and use cum_max/cum_min
        high_expr = pl.when(pl.col(in_col)).then(pl.col("high")).otherwise(None)
        low_expr = pl.when(pl.col(in_col)).then(pl.col("low")).otherwise(None)

        new_cols += [
            session_id,
            high_expr.alias(f"_raw_{kz}_high"),
            low_expr.alias(f"_raw_{kz}_low"),
        ]

    df = df.with_columns(new_cols)

    # For each kz, group rolling max/min by session_id, then forward-fill
    pivot_cols: list[pl.Expr] = []
    for kz in KILLZONES:
        sid = f"kz_{kz}_session_id"

        kz_high = (
            pl.col(f"_raw_{kz}_high")
            .over(sid)
            .forward_fill()
            .backward_fill()
            .alias(f"kz_{kz}_high")
        )
        kz_low = (
            pl.col(f"_raw_{kz}_low")
            .over(sid)
            .forward_fill()
            .backward_fill()
            .alias(f"kz_{kz}_low")
        )

        # We need max/min within session group; use map_elements-free trick:
        # Polars window functions don't have agg-over directly for partial groups,
        # so we compute cumulative max/min within the session.
        pivot_cols += [kz_high, kz_low]

    df = df.with_columns(pivot_cols)

    # Compute actual running max/min within session using group_by + over
    final_cols: list[pl.Expr] = []
    for kz in KILLZONES:
        sid = f"kz_{kz}_session_id"

        # cummax / cummin per session window
        kz_cum_high = pl.col("high").cum_max().over(sid).alias(f"kz_{kz}_high")
        kz_cum_low = pl.col("low").cum_min().over(sid).alias(f"kz_{kz}_low")
        final_cols += [kz_cum_high, kz_cum_low]

    df = df.with_columns(final_cols)

    # mid, range, distance features
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

    # clean raw helper columns
    raw_cols = [c for c in df.columns if c.startswith("_raw_")]
    return df.drop(raw_cols)


# ── DWM Levels (Day / Week / Month) ──────────────────────────────────────────


def compute_dwm_levels(df: pl.DataFrame) -> pl.DataFrame:
    """
    Compute Day, Week, Month open / high / low levels, mirroring Pine Script
    DWM logic: each new period resets the open; running high/low accumulate.

    Adds columns:
        d_open, d_high, d_low   — current-day OHLC
        w_open, w_high, w_low   — current-week OHLC
        m_open, m_high, m_low   — current-month OHLC

        pd_high, pd_low         — *previous* day high/low (PDH/PDL)
        pw_high, pw_low         — previous week high/low
        pm_high, pm_low         — previous month high/low

    Args:
        df: OHLCV DataFrame with UTC `timestamp`.

    Returns:
        df with DWM columns added.
    """
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

    # Current period running high/low via window
    df = df.with_columns(
        # Day
        pl.col("open").first().over("_day").alias("d_open"),
        pl.col("high").cum_max().over("_day").alias("d_high"),
        pl.col("low").cum_min().over("_day").alias("d_low"),
        # Week
        pl.col("open").first().over("_week").alias("w_open"),
        pl.col("high").cum_max().over("_week").alias("w_high"),
        pl.col("low").cum_min().over("_week").alias("w_low"),
        # Month
        pl.col("open").first().over("_yearmonth").alias("m_open"),
        pl.col("high").cum_max().over("_yearmonth").alias("m_high"),
        pl.col("low").cum_min().over("_yearmonth").alias("m_low"),
    )

    # Previous period high/low (shift by 1 period)
    # Build a period-level summary then join back
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


# ── Killzone Average Range ────────────────────────────────────────────────────


def compute_killzone_avg_range(df: pl.DataFrame, n: int = 5) -> pl.DataFrame:
    """
    Compute the rolling average range of the last `n` completed killzone sessions.
    Mirrors Pine Script's `range_avg` input.

    Requires `kz_{kz}_range` and `kz_{kz}_session_id` columns from
    `compute_killzone_pivots`.

    Adds columns:
        kz_{kz}_avg_range  — rolling mean of the last n session ranges

    Args:
        df:  DataFrame with killzone pivot columns.
        n:   Number of past sessions to average (default 5).

    Returns:
        df with avg_range columns added.
    """
    for kz in KILLZONES:
        sid_col = f"kz_{kz}_session_id"
        range_col = f"kz_{kz}_range"

        if sid_col not in df.columns or range_col not in df.columns:
            continue

        # Extract one row per completed session (last bar of each session)
        session_ranges = (
            df.filter(pl.col(f"in_{kz}") | pl.col(f"in_{kz}").shift(-1).is_null())
            .group_by(sid_col)
            .agg(pl.col(range_col).max().alias("_sr"))
            .sort(sid_col)
            .with_columns(
                pl.col("_sr")
                .rolling_mean(window_size=n, min_periods=1)
                .alias(f"kz_{kz}_avg_range")
            )
            .select([sid_col, f"kz_{kz}_avg_range"])
        )

        df = df.join(session_ranges, on=sid_col, how="left")

    return df


# ── Top-level feature builder ─────────────────────────────────────────────────


def add_killzone_features(
    df: pl.DataFrame,
    avg_range_n: int = 5,
) -> pl.DataFrame:
    """
    Complete ICT Killzone feature engineering pipeline.

    Steps:
        1. Ensure UTC timestamps.
        2. Add session flags (in_asia, in_london, …).
        3. Compute killzone pivot high/low/mid/range per session.
        4. Compute rolling average range over last `avg_range_n` sessions.
        5. Compute DWM open/high/low and previous period high/low.

    Args:
        df:           OHLCV DataFrame with UTC `timestamp`.
        avg_range_n:  Sessions to look back for average range (default 5).

    Returns:
        DataFrame enriched with ICT Killzone features.

    Feature columns added:
        in_{kz}                   bool   — bar is inside killzone session
        kz_{kz}_session_id        int    — monotonic session counter
        kz_{kz}_high/low/mid      float  — session pivot levels
        kz_{kz}_range             float  — session price range
        kz_{kz}_avg_range         float  — rolling avg range (n sessions)
        dist_to_{kz}_high/low     float  — close minus pivot level
        d_open/high/low           float  — daily open, running high/low
        w_open/high/low           float  — weekly open, running high/low
        m_open/high/low           float  — monthly open, running high/low
        pd_high/low               float  — previous day high/low
        pw_high/low               float  — previous week high/low
        pm_high/low               float  — previous month high/low
    """
    df = _ensure_utc(df)
    df = add_session_flags(df)
    df = compute_killzone_pivots(df)
    df = compute_killzone_avg_range(df, n=avg_range_n)
    df = compute_dwm_levels(df)
    return df
