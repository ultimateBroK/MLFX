"""Training data fixtures for MLFX tests."""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest


# ── Training Fixtures ─────────────────────────────────────────────────────────

_N_ROWS = 300
_N_FEATURES = 20


@pytest.fixture
def fake_feature_cols() -> list[str]:
    """20 synthetic feature column names: feat_00 ... feat_19."""
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
