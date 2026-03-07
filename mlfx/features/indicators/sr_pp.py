"""
Support/resistance and pivot-point feature engineering moved from legacy `indicators/`.
"""

from __future__ import annotations

import polars as pl


def _ensure_utc(df: pl.DataFrame) -> pl.DataFrame:
    """Ensure the DataFrame timestamp column has a UTC timezone."""
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


def detect_sr_patterns(df: pl.DataFrame) -> pl.DataFrame:
    """Detect the four S/R price patterns from the legacy indicator."""
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

    r_raw = (h < lo2 - rng2) & ((c1 - o1).abs() > rng2 * 2)
    r2_raw = (h < rng34_min - rng34) & ((c1 - o2).abs() > rng34 * 2)
    s_raw = (lo > h2 - rng2) & ((c1 - o1).abs() > rng2 * 2)
    s2_raw = (lo > rng34_max + rng34) & ((c1 - o2).abs() > rng34 * 2)

    df = df.with_columns(
        r_raw.alias("_r_raw"),
        r2_raw.alias("_r2_raw"),
        s_raw.alias("_s_raw"),
        s2_raw.alias("_s2_raw"),
    )

    def _dedup(col: str, n: int = 4) -> pl.Expr:
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


def compute_sr_zones(df: pl.DataFrame) -> pl.DataFrame:
    """Build active support/resistance zones and distance features."""
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
    return df.with_columns(
        ((c >= pl.col("nearest_resist_low")) & (c <= pl.col("nearest_resist_high"))).alias(
            "in_resist_zone"
        ),
        ((c >= pl.col("nearest_support_low")) & (c <= pl.col("nearest_support_high"))).alias(
            "in_support_zone"
        ),
        (c - pl.col("nearest_resist_low")).alias("dist_to_nearest_resist"),
        (pl.col("nearest_support_high") - c).alias("dist_to_nearest_support"),
        pl.when(c > pl.col("nearest_resist_high"))
        .then(pl.lit(1))
        .when(c < pl.col("nearest_support_low"))
        .then(pl.lit(-1))
        .otherwise(pl.lit(0))
        .cast(pl.Int8)
        .alias("sr_role_reversal"),
    )


PIVOT_TYPE_LEVELS: dict[str, int] = {
    "traditional": 11,
    "fibonacci": 7,
    "woodie": 9,
    "classic": 9,
    "dm": 3,
    "camarilla": 11,
}


def _ohlc_for_period(df: pl.DataFrame, freq: str) -> pl.DataFrame:
    """Resample OHLC to the given anchor frequency."""
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
    return _calc_traditional(o, h, lo, c)


def _calc_dm(o: float, h: float, lo: float, c: float) -> dict[str, float]:
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


def compute_pivot_points(
    df: pl.DataFrame,
    pivot_type: str = "traditional",
    anchor: str = "daily",
    prefix: str = "pp",
) -> pl.DataFrame:
    """Compute pivot levels from the previous completed anchor period."""
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
    period_ohlc = _ohlc_for_period(df, freq)

    pivot_rows = []
    for row in period_ohlc.iter_rows(named=True):
        levels = calc(row["open"], row["high"], row["low"], row["close"])
        entry = {"_period_start": row["timestamp"]}
        entry.update({f"{prefix}_{k}": v for k, v in levels.items()})
        pivot_rows.append(entry)

    if not pivot_rows:
        return df

    pivot_df = (
        pl.DataFrame(pivot_rows)
        .sort("_period_start")
        .with_columns(pl.col("_period_start").shift(-1).alias("_valid_from"))
        .filter(pl.col("_valid_from").is_not_null())
    )

    merged = (
        df.sort("timestamp")
        .join_asof(
            pivot_df.sort("_valid_from"),
            left_on="timestamp",
            right_on="_valid_from",
            strategy="backward",
        )
        .drop(["_period_start", "_valid_from"])
    )

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


def add_sr_pp_features(
    df: pl.DataFrame,
    pivot_type: str = "traditional",
    anchor: str = "daily",
    pivot_prefix: str = "pp",
) -> pl.DataFrame:
    """Run the complete S/R and pivot-point feature pipeline."""
    df = _ensure_utc(df)
    df = df.sort("timestamp")
    df = detect_sr_patterns(df)
    df = compute_sr_zones(df)
    df = compute_pivot_points(
        df, pivot_type=pivot_type, anchor=anchor, prefix=pivot_prefix
    )
    return df
