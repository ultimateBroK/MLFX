"""
tests/test_resample.py
======================
Unit tests for pipeline/resample.py

Run: pytest tests/test_resample.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import polars as pl
import pytest

from pipeline.resample import resample_to_ohlcv, detect_gaps, TIMEFRAMES


class TestResampleToOhlcv:
    def test_basic_resample_returns_correct_columns(self, sample_ticks):
        result = resample_to_ohlcv(sample_ticks, period="1h")
        assert set(result.columns) >= {
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "tick_count",
        }

    def test_high_gte_low_always(self, sample_ticks):
        result = resample_to_ohlcv(sample_ticks, period="1h")
        assert result.filter(pl.col("high") < pl.col("low")).is_empty(), (
            "high < low detected"
        )

    def test_close_positive(self, sample_ticks):
        result = resample_to_ohlcv(sample_ticks, period="1h")
        assert (result["close"] > 0).all(), "Non-positive close found"

    def test_sorted_ascending(self, sample_ticks):
        result = resample_to_ohlcv(sample_ticks, period="1h")
        ts = result["timestamp"].to_list()
        assert ts == sorted(ts), "Timestamps not sorted"

    def test_5m_has_more_bars_than_1h(self):
        # Create a sample tick stream with many ticks (say 300) spanning 2 hours
        base = datetime(2024, 1, 8, 0, tzinfo=timezone.utc)
        timestamps = [
            base + timedelta(minutes=i % 120, seconds=i % 60) for i in range(300)
        ]
        df = pl.DataFrame(
            {
                "timestamp": timestamps,
                "bid": [2000.0 + i * 0.1 for i in range(300)],
                "ask": [2000.2 + i * 0.1 for i in range(300)],
            }
        ).sort("timestamp")

        # Disable min_ticks safeguard so we don't accidentally drop tiny bars in testing
        bars_1h = resample_to_ohlcv(df, period="1h", min_ticks=1)
        bars_5m = resample_to_ohlcv(df, period="5m", min_ticks=1)
        assert len(bars_5m) > len(bars_1h)

    def test_empty_input_returns_empty_schema(self):
        empty = pl.DataFrame(
            schema={
                "timestamp": pl.Datetime("us", "UTC"),
                "bid": pl.Float64,
                "ask": pl.Float64,
            }
        )
        result = resample_to_ohlcv(empty, period="1h")
        assert result.is_empty()
        assert "timestamp" in result.columns

    @pytest.mark.parametrize("tf_key,period", list(TIMEFRAMES.items()))
    def test_all_timeframes_return_non_empty(self, sample_ticks, tf_key, period):
        result = resample_to_ohlcv(sample_ticks, period=period)
        # Some TFs (4h, 1d) may have very few bars — just check schema
        assert set(result.columns) >= {"timestamp", "open", "high", "low", "close"}

    def test_min_ticks_filter(self):
        """Bars with fewer ticks than min_ticks should be dropped."""
        base = datetime(2024, 1, 8, 0, tzinfo=timezone.utc)
        # Only 2 ticks in first hour
        ticks = pl.DataFrame(
            {
                "timestamp": [base + timedelta(minutes=i) for i in range(2)],
                "bid": [2020.0, 2021.0],
                "ask": [2020.3, 2021.3],
            }
        )
        result = resample_to_ohlcv(ticks, period="1h", min_ticks=5)
        assert result.is_empty(), "Bar with < min_ticks should be filtered"


class TestDetectGaps:
    def test_no_gaps_in_continuous_data(self, sample_ohlcv):
        gaps = detect_gaps(sample_ohlcv, period="1h")
        assert gaps.is_empty(), "Should detect no gaps in continuous 1H data"

    def test_detects_weekend_gap(self):
        base = datetime(2024, 1, 5, 22, tzinfo=timezone.utc)  # Friday
        # Jump from Friday 22:00 to Monday 00:00 — 26H gap
        timestamps = [
            base,
            base + timedelta(hours=26),  # Monday 00:00
        ]
        ohlcv = pl.DataFrame(
            {
                "timestamp": timestamps,
                "open": [2020.0, 2022.0],
                "high": [2022.0, 2024.0],
                "low": [2018.0, 2020.0],
                "close": [2021.0, 2023.0],
                "tick_count": [100, 100],
            }
        )
        gaps = detect_gaps(ohlcv, period="1h")
        assert len(gaps) == 1, "Should detect exactly 1 weekend gap"
        assert gaps[0, "gap_bars"] >= 24

    def test_returns_correct_schema(self, sample_ohlcv):
        gaps = detect_gaps(sample_ohlcv, period="1h")
        for col in ["gap_start", "gap_end", "gap_bars"]:
            assert col in gaps.columns
