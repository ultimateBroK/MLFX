"""Enhanced test fixtures for MLFX to replace production data dependency.

This module provides comprehensive synthetic data fixtures that can replace
the 3.1GB production dataset in tests, dramatically improving test performance.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import random
import string
from typing import Generator

import numpy as np
import polars as pl
import pytest


# ── Constants for Synthetic Data Generation ──────────────────────────────────

DEFAULT_SEED = 42
DEFAULT_SYMBOL = "XAUUSD"
DEFAULT_TIMEFRAME = "1H"
DEFAULT_START_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)

# OHLCV column schema
OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "tick_count"]

# Tick data column schema
TICK_COLUMNS = ["timestamp", "bid", "ask", "bid_volume", "ask_volume"]

# Feature columns that mirror production data
FEATURE_COLUMNS = [
    "timestamp",
    "open",
    "high", 
    "low",
    "close",
    "tick_count",
    "returns",
    "log_returns",
    "volatility_14",
    "rsi_14",
    "sma_20",
    "ema_12",
    "macd",
    "macd_signal",
    "bb_upper",
    "bb_lower",
    "atr_14",
    "volume_sma_20",
    "price_momentum",
    "trend_strength",
]

# Label columns for classification
LABEL_COLUMNS = ["label_5", "label_10", "label_20"]


# ── Factory Functions for Synthetic Data ─────────────────────────────────────


def generate_synthetic_ohlcv(
    n_rows: int = 1000,
    start_date: datetime | None = None,
    timeframe_minutes: int = 60,
    base_price: float = 2000.0,
    volatility: float = 5.0,
    seed: int = DEFAULT_SEED,
) -> pl.DataFrame:
    """Generate synthetic OHLCV data with realistic price movements.
    
    Args:
        n_rows: Number of bars to generate
        start_date: Starting timestamp (defaults to DEFAULT_START_DATE)
        timeframe_minutes: Bar interval in minutes
        base_price: Starting price level
        volatility: Price volatility factor
        seed: Random seed for reproducibility
        
    Returns:
        Polars DataFrame with OHLCV columns
    """
    rng = np.random.default_rng(seed)
    start = start_date or DEFAULT_START_DATE
    
    # Generate timestamps
    timestamps = [
        start + timedelta(minutes=i * timeframe_minutes)
        for i in range(n_rows)
    ]
    
    # Generate random walk for close prices
    returns = rng.normal(0, volatility / base_price, n_rows)
    closes = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC from close with realistic spreads
    spreads = rng.uniform(0.5, 2.0, n_rows)  # Bid-ask spread
    highs = closes + rng.uniform(0, spreads, n_rows)
    lows = closes - rng.uniform(0, spreads, n_rows)
    opens = lows + rng.uniform(0, highs - lows, n_rows)
    
    # Ensure OHLC relationships: low <= open <= high, low <= close <= high
    opens = np.clip(opens, lows, highs)
    closes = np.clip(closes, lows, highs)
    
    # Generate tick counts (volume proxy)
    tick_counts = rng.integers(500, 5000, n_rows)
    
    return pl.DataFrame({
        "timestamp": timestamps,
        "open": opens.astype(np.float64),
        "high": highs.astype(np.float64),
        "low": lows.astype(np.float64),
        "close": closes.astype(np.float64),
        "tick_count": tick_counts.astype(np.int64),
    })


def generate_synthetic_ticks(
    n_ticks: int = 10000,
    start_date: datetime | None = None,
    duration_minutes: int = 60,
    base_price: float = 2000.0,
    spread_pips: float = 0.3,
    seed: int = DEFAULT_SEED,
) -> pl.DataFrame:
    """Generate synthetic tick data with bid/ask prices.
    
    Args:
        n_ticks: Number of ticks to generate
        start_date: Starting timestamp
        duration_minutes: Time span for all ticks
        base_price: Starting price level
        spread_pips: Typical bid-ask spread
        seed: Random seed for reproducibility
        
    Returns:
        Polars DataFrame with tick columns
    """
    rng = np.random.default_rng(seed)
    start = start_date or DEFAULT_START_DATE
    
    # Random timestamps within duration
    random_offsets = rng.integers(0, duration_minutes * 60 * 1000, n_ticks)  # milliseconds
    timestamps = [start + timedelta(milliseconds=int(ms)) for ms in random_offsets]
    timestamps.sort()
    
    # Generate bid prices with random walk
    returns = rng.normal(0, 0.0001, n_ticks)
    bids = base_price * np.exp(np.cumsum(returns))
    
    # Ask is bid + spread
    spread = rng.uniform(spread_pips * 0.5, spread_pips * 1.5, n_ticks)
    asks = bids + spread
    
    # Volumes
    bid_volumes = rng.uniform(0.1, 10.0, n_ticks)
    ask_volumes = rng.uniform(0.1, 10.0, n_ticks)
    
    return pl.DataFrame({
        "timestamp": timestamps,
        "bid": bids.astype(np.float64),
        "ask": asks.astype(np.float64),
        "bid_volume": bid_volumes.astype(np.float64),
        "ask_volume": ask_volumes.astype(np.float64),
    })


def generate_synthetic_features(
    n_rows: int = 1000,
    start_date: datetime | None = None,
    n_feature_cols: int = 20,
    include_labels: bool = True,
    seed: int = DEFAULT_SEED,
) -> pl.DataFrame:
    """Generate synthetic feature-engineered data for ML training.
    
    Args:
        n_rows: Number of rows to generate
        start_date: Starting timestamp
        n_feature_cols: Number of feature columns
        include_labels: Whether to include label columns
        seed: Random seed for reproducibility
        
    Returns:
        Polars DataFrame with features and optional labels
    """
    rng = np.random.default_rng(seed)
    start = start_date or DEFAULT_START_DATE
    
    # Generate timestamps (hourly by default)
    timestamps = [start + timedelta(hours=i) for i in range(n_rows)]
    
    # Generate base OHLCV
    ohlcv = generate_synthetic_ohlcv(n_rows, start, seed=seed)
    
    # Generate technical indicators as features
    features = {
        "timestamp": timestamps,
        "open": ohlcv["open"].to_list(),
        "high": ohlcv["high"].to_list(),
        "low": ohlcv["low"].to_list(),
        "close": ohlcv["close"].to_list(),
        "tick_count": ohlcv["tick_count"].to_list(),
    }
    
    # Add calculated features
    closes = ohlcv["close"].to_numpy()
    returns = np.diff(closes, prepend=closes[0]) / closes
    
    features["returns"] = returns.tolist()
    features["log_returns"] = np.log1p(returns).tolist()
    
    # Add synthetic technical indicators
    for i in range(n_feature_cols - 10):  # Subtract base columns
        col_name = f"feat_{i:02d}"
        features[col_name] = rng.normal(0, 1, n_rows).tolist()
    
    # Add volatility and momentum features
    features["volatility_14"] = rng.uniform(0.5, 2.0, n_rows).tolist()
    features["rsi_14"] = rng.uniform(0, 100, n_rows).tolist()
    features["price_momentum"] = rng.normal(0, 1, n_rows).tolist()
    features["trend_strength"] = rng.uniform(-1, 1, n_rows).tolist()
    
    df = pl.DataFrame(features)
    
    # Add labels if requested (classification targets: -2 to 2)
    if include_labels:
        for horizon in [5, 10, 20]:
            df = df.with_columns(
                pl.Series(
                    f"label_{horizon}",
                    rng.integers(-2, 3, n_rows).astype(np.int64)
                )
            )
    
    return df


def generate_multi_month_data(
    symbol: str = DEFAULT_SYMBOL,
    timeframe: str = DEFAULT_TIMEFRAME,
    n_months: int = 3,
    bars_per_day: int = 24,  # For 1H timeframe
    seed: int = DEFAULT_SEED,
) -> Generator[tuple[str, pl.DataFrame], None, None]:
    """Generate partitioned data for multiple months.
    
    Args:
        symbol: Symbol name
        timeframe: Timeframe string
        n_months: Number of months to generate
        bars_per_day: Bars per day (24 for hourly)
        seed: Random seed
        
    Yields:
        Tuples of (year-month string, DataFrame)
    """
    rng = np.random.default_rng(seed)
    base_date = DEFAULT_START_DATE
    
    for month_idx in range(n_months):
        year_month = (base_date + timedelta(days=month_idx * 30)).strftime("%Y-%m")
        month_start = datetime(
            int(year_month[:4]), int(year_month[5:7]), 1,
            tzinfo=timezone.utc
        )
        
        # Generate ~30 days of data per month
        n_rows = 30 * bars_per_day
        df = generate_synthetic_features(
            n_rows=n_rows,
            start_date=month_start,
            seed=seed + month_idx,  # Vary seed per month
        )
        
        yield year_month, df


# ── Pytest Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_ohlcv_large() -> pl.DataFrame:
    """Large synthetic OHLCV dataset (1000 bars) for integration tests."""
    return generate_synthetic_ohlcv(n_rows=1000)


@pytest.fixture
def sample_ohlcv_month() -> pl.DataFrame:
    """One month of synthetic hourly OHLCV data (~720 bars)."""
    return generate_synthetic_ohlcv(n_rows=720)


@pytest.fixture
def sample_ticks_large() -> pl.DataFrame:
    """Large synthetic tick dataset (10,000 ticks)."""
    return generate_synthetic_ticks(n_ticks=10000)


@pytest.fixture
def sample_features_large() -> pl.DataFrame:
    """Large synthetic feature dataset with labels."""
    return generate_synthetic_features(n_rows=1000, include_labels=True)


@pytest.fixture
def multi_month_fixture(tmp_path: Path) -> Path:
    """Create temporary multi-month parquet files for testing.
    
    Returns path to temporary data directory with structure:
        tmp_path/
          labels/
            XAUUSD/
              1H/
                2024-01.parquet
                2024-02.parquet
                2024-03.parquet
    """
    labels_dir = tmp_path / "labels" / DEFAULT_SYMBOL / DEFAULT_TIMEFRAME
    labels_dir.mkdir(parents=True, exist_ok=True)
    
    for year_month, df in generate_multi_month_data(n_months=3):
        df.write_parquet(labels_dir / f"{year_month}.parquet")
    
    return tmp_path


@pytest.fixture
def mock_project_paths(tmp_path: Path):
    """Create a ProjectPaths instance pointing to temporary directory."""
    from mlfx.config.paths import ProjectPaths
    
    paths = ProjectPaths(project_root=tmp_path)
    
    # Create necessary subdirectories
    paths.data_root.mkdir(parents=True, exist_ok=True)
    paths.outputs_root.mkdir(parents=True, exist_ok=True)
    paths.raw_root.mkdir(parents=True, exist_ok=True)
    paths.ohlcv_root.mkdir(parents=True, exist_ok=True)
    paths.features_root.mkdir(parents=True, exist_ok=True)
    paths.labels_root.mkdir(parents=True, exist_ok=True)
    paths.models_root.mkdir(parents=True, exist_ok=True)
    paths.reports_root.mkdir(parents=True, exist_ok=True)
    
    return paths


@pytest.fixture
def synthetic_ohlcv_generator():
    """Factory fixture for generating OHLCV data with custom parameters."""
    def _generator(**kwargs):
        return generate_synthetic_ohlcv(**kwargs)
    return _generator


@pytest.fixture
def synthetic_features_generator():
    """Factory fixture for generating feature data with custom parameters."""
    def _generator(**kwargs):
        return generate_synthetic_features(**kwargs)
    return _generator
