"""OHLCV and tick data fixtures for MLFX tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random

import polars as pl
import pytest


# ── OHLCV Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def sample_ohlcv() -> pl.DataFrame:
    """20 1H bars of synthetic XAUUSD data (ascending close, UTC)."""
    base = datetime(2024, 1, 8, 0, tzinfo=timezone.utc)
    n = 20
    opens = [2020.0 + i * 0.5 for i in range(n)]
    closes = [o + 1.0 for o in opens]
    highs = [c + 2.0 for c in closes]
    lows = [o - 2.0 for o in opens]
    return pl.DataFrame(
        {
            "timestamp": [base + timedelta(hours=i) for i in range(n)],
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "tick_count": [1000 + i * 50 for i in range(n)],
        }
    )


@pytest.fixture
def sample_ticks() -> pl.DataFrame:
    """288 x 5-minute synthetic tick records for one day."""
    base = datetime(2024, 1, 8, 0, tzinfo=timezone.utc)
    n = 288

    random.seed(42)
    bids = [2020.0 + random.uniform(-5, 5) for _ in range(n)]
    asks = [b + 0.3 for b in bids]
    return pl.DataFrame(
        {
            "timestamp": [base + timedelta(minutes=i * 5) for i in range(n)],
            "bid": bids,
            "ask": asks,
            "bid_volume": [1.0] * n,
            "ask_volume": [1.0] * n,
        }
    )


@pytest.fixture
def london_bars(sample_ohlcv) -> pl.DataFrame:
    """Filter bars in London killzone hours (07-09 UTC as proxy for test)."""
    return sample_ohlcv.filter(pl.col("timestamp").dt.hour().is_between(7, 9))
