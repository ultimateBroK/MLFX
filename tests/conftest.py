"""
tests/conftest.py
=================
Shared pytest fixtures for MLFX test suite.

Skill: @skill:pytest-ml-fx
  resources: pytest-playbook.md → Polars fixtures, network marker
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
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
    """288 × 5-minute synthetic tick records for one day."""
    base = datetime(2024, 1, 8, 0, tzinfo=timezone.utc)
    n = 288
    import random

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
    """Filter bars in London killzone hours (07–09 UTC as proxy for test)."""
    return sample_ohlcv.filter(pl.col("timestamp").dt.hour().is_between(7, 9))


# ── Training Fixtures ─────────────────────────────────────────────────────────

_N_ROWS = 300
_N_FEATURES = 20


@pytest.fixture
def fake_feature_cols() -> list[str]:
    """20 synthetic feature column names: feat_00 … feat_19."""
    return [f"feat_{i:02d}" for i in range(_N_FEATURES)]


@pytest.fixture
def fake_X(fake_feature_cols) -> np.ndarray:
    """(300, 20) float32 feature matrix with a fixed seed."""
    rng = np.random.default_rng(42)
    return rng.standard_normal((_N_ROWS, len(fake_feature_cols))).astype(np.float32)


@pytest.fixture
def fake_y() -> np.ndarray:
    """300-element int64 label array, values in {0, 1, 2, 3, 4} (post-mapping)."""
    rng = np.random.default_rng(42)
    return rng.integers(0, 5, size=_N_ROWS).astype(np.int64)


@pytest.fixture
def fake_label_series() -> np.ndarray:
    """300-element int64 raw-label array, values in {-2, -1, 0, 1, 2} (pre-mapping)."""
    rng = np.random.default_rng(42)
    return rng.integers(-2, 3, size=_N_ROWS).astype(np.int64)


@pytest.fixture
def fake_feature_df(fake_feature_cols) -> pl.DataFrame:
    """Polars DataFrame with 20 feature cols + common blacklisted OHLCV/label cols."""
    rng = np.random.default_rng(42)
    data: dict = {col: rng.standard_normal(_N_ROWS).tolist() for col in fake_feature_cols}
    # Blacklisted price/target columns that must NOT appear in selected features.
    data["open"] = rng.standard_normal(_N_ROWS).tolist()
    data["high"] = rng.standard_normal(_N_ROWS).tolist()
    data["low"] = rng.standard_normal(_N_ROWS).tolist()
    data["close"] = rng.standard_normal(_N_ROWS).tolist()
    data["tick_count"] = rng.integers(100, 1000, size=_N_ROWS).tolist()
    data["label_10"] = rng.integers(-2, 3, size=_N_ROWS).tolist()
    return pl.DataFrame(data)


# Import additional synthetic fixtures
from tests.fixtures.synthetic import (
    generate_synthetic_ohlcv,
    generate_synthetic_ticks,
    generate_synthetic_features,
    generate_multi_month_data,
    sample_ohlcv_large,
    sample_ohlcv_month,
    sample_ticks_large,
    sample_features_large,
    multi_month_fixture,
    mock_project_paths,
    synthetic_ohlcv_generator,
    synthetic_features_generator,
)
