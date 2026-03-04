"""
indicator/sr_pp.py
==================
Python translation of SR_PP.pine (Support/Resistance + Pivot Points indicator).

Converts Pine Script S/R and Pivot Point logic into Polars-based feature engineering:

A. Support / Resistance Boxes
    - Pattern r  (single-bar resistance): strong bearish candle breaks below low[2]
    - Pattern r2 (two-bar resistance)   : combined two-bar bearish breakout
    - Pattern s  (single-bar support)   : strong bullish candle breaks above high[2]
    - Pattern s2 (two-bar support)      : combined two-bar bullish breakout
    - Role reversal: resistance → support when price closes above, vice-versa

B. Pivot Points (multi-type)
    - Traditional, Fibonacci, Woodie, Classic, DM, Camarilla
    - Anchor timeframes: Daily, Weekly, Monthly, Quarterly, Yearly

Input DataFrame must have columns:
    timestamp (Datetime, UTC), open, high, low, close

Output: additional feature columns appended to the input DataFrame.
"""

from __future__ import annotations

import polars as pl

# ── Helpers ───────────────────────────────────────────────────────────────────


def _ensure_utc(df: pl.DataFrame) -> pl.DataFrame:
    ts = df["timestamp"]
    if ts.dtype in (
        pl.Datetime("us", "UTC"),
        pl.Datetime("ns", "UTC"),
        pl.Datetime("ms", "UTC"),
    ):
        return df
    if ts.dtype in (
        pl.Datetime("us", None),
        pl.Datetime("ns", None),
        pl.Datetime("ms", None),
    ):
        return df.with_columns(pl.col("timestamp").dt.replace_time_zone("UTC"))
    return df


# ──────────────────────────────────────────────────────────────────────────────
# A. SUPPORT / RESISTANCE PATTERN DETECTION
# ──────────────────────────────────────────────────────────────────────────────


def detect_sr_patterns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Detect the four S/R price patterns from SR_PP.pine.

    Pine Script logic translated:
        r  = high < low[2]  - (high[2] - low[2])
             AND abs(close[1] - open[1]) > (high[2] - low[2]) * 2
        r2 = high < min(low[3], low[4]) - (max(high[3],high[4]) - min(low[3],low[4]))
             AND abs(close[1] - open[2]) > (max(high[3],high[4]) - min(low[3],low[4])) * 2
             AND r2 not True in last 4 bars   (de-duplicate)
        s  = low  > high[2] - (high[2] - low[2])          ... mirror of r
        s2 = low  > max(high[3],high[4]) + spread          ... mirror of r2

    Adds columns:
        sr_resist_1bar  — bool: single-bar resistance pattern
        sr_resist_2bar  — bool: two-bar resistance pattern
        sr_support_1bar — bool: single-bar support pattern
        sr_support_2bar — bool: two-bar support pattern

    Args:
        df: OHLCV DataFrame sorted by timestamp ascending.

    Returns:
        df with 4 boolean pattern columns appended.
    """
    h = pl.col("high")
    lo = pl.col("low")
    c = pl.col("close")
    o = pl.col("open")

    h2 = h.shift(2)
    lo2 = lo.shift(2)
    h3 = h.shift(3)
    lo3 = lo.shift(3)
    h4 = h.shift(4)
    lo4 = lo.shift(4)
    c1 = c.shift(1)
    o1 = o.shift(1)
    o2 = o.shift(2)

    rng2 = h2 - lo2
    rng34_max = pl.max_horizontal(h3, h4)
    rng34_min = pl.min_horizontal(lo3, lo4)
    rng34 = rng34_max - rng34_min

    # ── Resistance 1-bar (r) ──
    r_raw = (h < lo2 - rng2) & ((c1 - o1).abs() > rng2 * 2)

    # ── Resistance 2-bar (r2) ──
    r2_raw = (h < rng34_min - rng34) & ((c1 - o2).abs() > rng34 * 2)

    # ── Support 1-bar (s) ──
    s_raw = (lo > h2 - rng2) & ((c1 - o1).abs() > rng2 * 2)

    # ── Support 2-bar (s2) ──
    s2_raw = (lo > rng34_max + rng34) & ((c1 - o2).abs() > rng34 * 2)

    df = df.with_columns(
        r_raw.alias("_r_raw"),
        r2_raw.alias("_r2_raw"),
        s_raw.alias("_s_raw"),
        s2_raw.alias("_s2_raw"),
    )

    # De-duplicate: suppress if any of the last 4 bars also triggered
    # (equivalent to Pine's `for i = 1 to 4: r := r and r2[i] == false`)
    def _dedup(col: str, n: int = 4) -> pl.Expr:
        """True only if no trigger in the previous n bars."""
        expr = pl.col(col)
        for i in range(1, n + 1):
            expr = expr & pl.col(col).shift(i).fill_null(False).not_()
        return expr.alias(col.replace("_raw", ""))

    df = df.with_columns(
        _dedup("_r_raw").alias("sr_resist_1bar"),
        _dedup("_r2_raw").alias("sr_resist_2bar"),
        _dedup("_s_raw").alias("sr_support_1bar"),
        _dedup("_s2_raw").alias("sr_support_2bar"),
    )

    return df.drop(["_r_raw", "_r2_raw", "_s_raw", "_s2_raw"])


# ── S/R Zone Tracking ─────────────────────────────────────────────────────────


def compute_sr_zones(df: pl.DataFrame) -> pl.DataFrame:
    """
    Build per-bar S/R zone features from the detected patterns.

    For each bar, reports:
        nearest_resist_high / _low   — high/low of nearest active resistance zone
        nearest_support_high / _low  — high/low of nearest active support zone
        in_resist_zone               — close is inside a resistance box
        in_support_zone              — close is inside a support zone
        dist_to_nearest_resist       — close - nearest_resist_low (negative = below)
        dist_to_nearest_support      — nearest_support_high - close (negative = above)
        sr_role_reversal             — 1 = resist became support, -1 = support became resist

    Strategy (simplified, Pine-compatible):
        - When a resistance pattern fires, record high[2]/low[2] as the zone boundary.
        - When price closes above the resistance zone top → role reversal (now support).
        - Carry the last seen zone forward via forward-fill.

    Args:
        df: DataFrame with sr_resist_1bar / sr_support_1bar columns.

    Returns:
        df with S/R zone feature columns.
    """
    # ── Resistance zones ──────────────────────────────────────────────────────
    # Zone defined by high[2] / low[2] at the bar where pattern fired.
    resist_high = (
        pl.when(pl.col("sr_resist_1bar") | pl.col("sr_resist_2bar"))
        .then(pl.col("high").shift(2))
        .otherwise(None)
        .forward_fill()
    )
    resist_low = (
        pl.when(pl.col("sr_resist_1bar") | pl.col("sr_resist_2bar"))
        .then(pl.col("low").shift(2))
        .otherwise(None)
        .forward_fill()
    )

    # ── Support zones ──────────────────────────────────────────────────────────
    support_high = (
        pl.when(pl.col("sr_support_1bar") | pl.col("sr_support_2bar"))
        .then(pl.col("high").shift(2))
        .otherwise(None)
        .forward_fill()
    )
    support_low = (
        pl.when(pl.col("sr_support_1bar") | pl.col("sr_support_2bar"))
        .then(pl.col("low").shift(2))
        .otherwise(None)
        .forward_fill()
    )

    df = df.with_columns(
        resist_high.alias("nearest_resist_high"),
        resist_low.alias("nearest_resist_low"),
        support_high.alias("nearest_support_high"),
        support_low.alias("nearest_support_low"),
    )

    c = pl.col("close")
    df = df.with_columns(
        # Inside zone: close is between zone low and zone high
        (
            (c >= pl.col("nearest_resist_low")) & (c <= pl.col("nearest_resist_high"))
        ).alias("in_resist_zone"),
        (
            (c >= pl.col("nearest_support_low")) & (c <= pl.col("nearest_support_high"))
        ).alias("in_support_zone"),
        # Distance: positive = approaching, negative = already past
        (c - pl.col("nearest_resist_low")).alias("dist_to_nearest_resist"),
        (pl.col("nearest_support_high") - c).alias("dist_to_nearest_support"),
        # Role reversal:
        #   +1 → price closed above resistance (becomes support)
        #   -1 → price closed below support (becomes resistance)
        pl.when(c > pl.col("nearest_resist_high"))
        .then(pl.lit(1))
        .when(c < pl.col("nearest_support_low"))
        .then(pl.lit(-1))
        .otherwise(pl.lit(0))
        .cast(pl.Int8)
        .alias("sr_role_reversal"),
    )

    return df


# ──────────────────────────────────────────────────────────────────────────────
# B. PIVOT POINTS
# ──────────────────────────────────────────────────────────────────────────────

# Pivot type → number of levels (P + Rn + Sn)
PIVOT_TYPE_LEVELS: dict[str, int] = {
    "traditional": 11,  # P, R1-R5, S1-S5
    "fibonacci": 7,  # P, R1-R3, S1-R3
    "woodie": 9,  # P, R1-R4, S1-S4
    "classic": 9,
    "dm": 3,  # P only + R1/S1
    "camarilla": 11,
}


def _ohlc_for_period(df: pl.DataFrame, freq: str) -> pl.DataFrame:
    """
    Resample OHLCV to the given anchor frequency and return a period-indexed
    DataFrame of (period_start, open, high, low, close).

    freq is one of: "1d", "1w", "1mo", "3mo", "1y"
    """
    return (
        df.sort("timestamp")
        .group_by_dynamic("timestamp", every=freq, closed="left")
        .agg(
            pl.col("open").first().alias("open"),
            pl.col("high").max().alias("high"),
            pl.col("low").min().alias("low"),
            pl.col("close").last().alias("close"),
        )
        .sort("timestamp")
    )


def _calc_traditional(o: float, h: float, lo: float, c: float) -> dict[str, float]:
    p = (h + lo + c) / 3
    r1 = 2 * p - lo
    s1 = 2 * p - h
    r2 = p + (h - lo)
    s2 = p - (h - lo)
    r3 = h + 2 * (p - lo)
    s3 = lo - 2 * (h - p)
    r4 = r3 + (h - lo)
    s4 = s3 - (h - lo)
    r5 = r4 + (h - lo)
    s5 = s4 - (h - lo)
    return dict(
        p=p, r1=r1, r2=r2, r3=r3, r4=r4, r5=r5, s1=s1, s2=s2, s3=s3, s4=s4, s5=s5
    )


def _calc_fibonacci(o: float, h: float, lo: float, c: float) -> dict[str, float]:
    p = (h + lo + c) / 3
    rng = h - lo
    r1 = p + 0.382 * rng
    s1 = p - 0.382 * rng
    r2 = p + 0.618 * rng
    s2 = p - 0.618 * rng
    r3 = p + 1.000 * rng
    s3 = p - 1.000 * rng
    return dict(
        p=p,
        r1=r1,
        r2=r2,
        r3=r3,
        r4=None,
        r5=None,
        s1=s1,
        s2=s2,
        s3=s3,
        s4=None,
        s5=None,
    )


def _calc_woodie(o: float, h: float, lo: float, c: float) -> dict[str, float]:
    p = (h + lo + 2 * c) / 4
    r1 = 2 * p - lo
    s1 = 2 * p - h
    r2 = p + (h - lo)
    s2 = p - (h - lo)
    r3 = h + 2 * (p - lo)
    s3 = lo - 2 * (h - p)
    r4 = r3 + (h - lo)
    s4 = s3 - (h - lo)
    return dict(
        p=p, r1=r1, r2=r2, r3=r3, r4=r4, r5=None, s1=s1, s2=s2, s3=s3, s4=s4, s5=None
    )


def _calc_classic(o: float, h: float, lo: float, c: float) -> dict[str, float]:
    """Classic pivot = same formula as Traditional."""
    return _calc_traditional(o, h, lo, c)


def _calc_dm(o: float, h: float, lo: float, c: float) -> dict[str, float]:
    """DeMark pivot — only P, R1, S1."""
    if c < o:
        x = h + 2 * lo + c
    elif c > o:
        x = 2 * h + lo + c
    else:
        x = h + lo + 2 * c
    p = x / 4
    r1 = x / 2 - lo
    s1 = x / 2 - h
    return dict(
        p=p,
        r1=r1,
        r2=None,
        r3=None,
        r4=None,
        r5=None,
        s1=s1,
        s2=None,
        s3=None,
        s4=None,
        s5=None,
    )


def _calc_camarilla(o: float, h: float, lo: float, c: float) -> dict[str, float]:
    rng = h - lo
    r1 = c + rng * 1.1 / 12
    s1 = c - rng * 1.1 / 12
    r2 = c + rng * 1.1 / 6
    s2 = c - rng * 1.1 / 6
    r3 = c + rng * 1.1 / 4
    s3 = c - rng * 1.1 / 4
    r4 = c + rng * 1.1 / 2
    s4 = c - rng * 1.1 / 2
    r5 = (h / lo) * c
    s5 = c - (r5 - c)
    p = (h + lo + c) / 3
    return dict(
        p=p, r1=r1, r2=r2, r3=r3, r4=r4, r5=r5, s1=s1, s2=s2, s3=s3, s4=s4, s5=s5
    )


_PIVOT_CALCULATORS = {
    "traditional": _calc_traditional,
    "fibonacci": _calc_fibonacci,
    "woodie": _calc_woodie,
    "classic": _calc_classic,
    "dm": _calc_dm,
    "camarilla": _calc_camarilla,
}

_ANCHOR_FREQ: dict[str, str] = {
    "daily": "1d",
    "weekly": "1w",
    "monthly": "1mo",
    "quarterly": "3mo",
    "yearly": "1y",
}

_PIVOT_LEVELS = ["p", "r1", "r2", "r3", "r4", "r5", "s1", "s2", "s3", "s4", "s5"]


def compute_pivot_points(
    df: pl.DataFrame,
    pivot_type: str = "traditional",
    anchor: str = "daily",
    prefix: str = "pp",
) -> pl.DataFrame:
    """
    Compute Pivot Points for each bar by joining the *previous* period's OHLC.

    Mirrors SR_PP.pine's `isDailyBasedInput` = True behaviour: pivot levels are
    calculated from the previous completed period's data and are valid for the
    entire next period.

    Args:
        df:          OHLCV DataFrame with UTC `timestamp`.
        pivot_type:  One of traditional / fibonacci / woodie / classic / dm /
                     camarilla (case-insensitive).
        anchor:      Anchor timeframe: daily / weekly / monthly / quarterly /
                     yearly (case-insensitive).
        prefix:      Column name prefix (default "pp").

    Returns:
        df with columns:
            {prefix}_p
            {prefix}_r1 … {prefix}_r5   (None if not applicable for pivot_type)
            {prefix}_s1 … {prefix}_s5
            {prefix}_dist_to_p          — close - P
            {prefix}_dist_to_r1         — close - R1
            {prefix}_dist_to_s1         — close - S1
            {prefix}_above_p            — bool: close > P
    """
    ptype = pivot_type.lower()
    anchor = anchor.lower()

    if ptype not in _PIVOT_CALCULATORS:
        raise ValueError(
            f"Unknown pivot_type '{pivot_type}'. Choose from: {list(_PIVOT_CALCULATORS)}"
        )
    if anchor not in _ANCHOR_FREQ:
        raise ValueError(
            f"Unknown anchor '{anchor}'. Choose from: {list(_ANCHOR_FREQ)}"
        )

    freq = _ANCHOR_FREQ[anchor]
    calc = _PIVOT_CALCULATORS[ptype]

    df = _ensure_utc(df)

    # Build period-level pivot table from previous period OHLC
    period_ohlc = _ohlc_for_period(df, freq)

    # Compute pivot levels row-by-row (periods are few, not a bottleneck)
    pivot_rows = []
    for row in period_ohlc.iter_rows(named=True):
        levels = calc(row["open"], row["high"], row["low"], row["close"])
        entry = {"_period_start": row["timestamp"]}
        entry.update({f"{prefix}_{k}": v for k, v in levels.items()})
        pivot_rows.append(entry)

    if not pivot_rows:
        return df

    pivot_df = pl.DataFrame(pivot_rows)

    # Next period's start = this period's levels apply to bars *after* period_start
    # Shift by 1 so we use previous period's OHLC for current period prices
    period_starts = pivot_df["_period_start"].to_list()
    pivot_df = pivot_df.with_columns(
        # The pivot is *valid from* the next period start
        pl.Series("_valid_from", period_starts[1:] + [None])
    ).filter(pl.col("_valid_from").is_not_null())

    # Join each bar to its applicable pivot set via asof join
    df_sorted = df.sort("timestamp")
    pivot_sorted = pivot_df.sort("_valid_from")

    merged = df_sorted.join_asof(
        pivot_sorted,
        left_on="timestamp",
        right_on="_valid_from",
        strategy="backward",
    ).drop(["_period_start", "_valid_from"])

    # Distance & relative features
    p_col = f"{prefix}_p"
    r1_col = f"{prefix}_r1"
    s1_col = f"{prefix}_s1"

    dist_exprs: list[pl.Expr] = [
        (pl.col("close") - pl.col(p_col)).alias(f"{prefix}_dist_to_p"),
        (pl.col("close") > pl.col(p_col)).alias(f"{prefix}_above_p"),
    ]
    if r1_col in merged.columns:
        dist_exprs.append(
            (pl.col("close") - pl.col(r1_col)).alias(f"{prefix}_dist_to_r1")
        )
    if s1_col in merged.columns:
        dist_exprs.append(
            (pl.col("close") - pl.col(s1_col)).alias(f"{prefix}_dist_to_s1")
        )

    return merged.with_columns(dist_exprs)


# ──────────────────────────────────────────────────────────────────────────────
# Top-level feature builder
# ──────────────────────────────────────────────────────────────────────────────


def add_sr_pp_features(
    df: pl.DataFrame,
    pivot_type: str = "traditional",
    anchor: str = "daily",
    pivot_prefix: str = "pp",
) -> pl.DataFrame:
    """
    Complete Support/Resistance + Pivot Point feature engineering pipeline.

    Steps:
        1. Detect S/R price patterns (r, r2, s, s2).
        2. Build S/R zone tracking (zones, distances, role reversal).
        3. Compute Pivot Point levels and distance features.

    Args:
        df:            OHLCV DataFrame with UTC `timestamp`, sorted ascending.
        pivot_type:    Pivot calculation method (default "traditional").
        anchor:        Anchor timeframe for pivots (default "daily").
        pivot_prefix:  Prefix for pivot column names (default "pp").

    Returns:
        df enriched with all S/R and Pivot Point features.

    Feature columns added:
        sr_resist_1bar / sr_resist_2bar        bool — resistance pattern fired
        sr_support_1bar / sr_support_2bar      bool — support pattern fired
        nearest_resist_high / _low             float — active resistance zone
        nearest_support_high / _low            float — active support zone
        in_resist_zone / in_support_zone       bool — price inside zone
        dist_to_nearest_resist / _support      float — distance to zone edge
        sr_role_reversal                       int8  — 0 / +1 / -1
        {prefix}_p                             float — Pivot P
        {prefix}_r1 … r5 / s1 … s5            float — R/S levels
        {prefix}_dist_to_p / r1 / s1           float — close minus level
        {prefix}_above_p                       bool — close above pivot P
    """
    df = _ensure_utc(df)
    df = df.sort("timestamp")
    df = detect_sr_patterns(df)
    df = compute_sr_zones(df)
    df = compute_pivot_points(
        df, pivot_type=pivot_type, anchor=anchor, prefix=pivot_prefix
    )
    return df
