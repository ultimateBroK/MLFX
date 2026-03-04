"""
tests/test_labels.py
====================
Unit tests for pipeline/labels.py

Run: pytest tests/test_labels.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import polars as pl
import pytest

from pipeline.labels import (
    add_labels,
    compute_class_balance,
    stratified_train_test_split,
)

HORIZONS = [5, 10, 20]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def ohlcv_with_atr() -> pl.DataFrame:
    """50 synthetic 1H bars with atr_14 column (required by add_labels)."""
    n = 50
    base = datetime(2024, 1, 8, 0, tzinfo=timezone.utc)
    closes = [2020.0 + i * 0.5 for i in range(n)]
    return pl.DataFrame(
        {
            "timestamp": [base + timedelta(hours=i) for i in range(n)],
            "open": [c - 0.3 for c in closes],
            "high": [c + 2.0 for c in closes],
            "low": [c - 2.0 for c in closes],
            "close": closes,
            "tick_count": [1000] * n,
            "atr_14": [3.0] * n,  # fixed ATR for predictable thresholds
        }
    )


# ── add_labels tests ──────────────────────────────────────────────────────────


class TestAddLabels:
    """Test standard evaluation criteria for trading label calculations."""

    def test_label_columns_created(self, ohlcv_with_atr):
        """Test insertion of new label horizon columns directly."""
        result = add_labels(ohlcv_with_atr, horizons=HORIZONS)
        for n in HORIZONS:
            assert f"label_{n}" in result.columns, f"label_{n} missing"

    def test_close_ahead_columns_created(self, ohlcv_with_atr):
        """Test corresponding trailing structural metrics generated out from calculations."""
        result = add_labels(ohlcv_with_atr, horizons=[5])
        assert "close_ahead_5" in result.columns

    @pytest.mark.parametrize("horizon", HORIZONS)
    def test_label_values_in_valid_set(self, ohlcv_with_atr, horizon):
        """All non-null labels must be in {-1, 0, 1}."""
        result = add_labels(ohlcv_with_atr, horizons=[horizon])
        col = f"label_{horizon}"
        valid_labels = result[col].drop_nulls().unique().to_list()
        for v in valid_labels:
            assert v in (-1, 0, 1), f"Unexpected label value: {v}"

    @pytest.mark.parametrize("horizon", HORIZONS)
    def test_last_n_rows_are_null(self, ohlcv_with_atr, horizon):
        """The last `horizon` rows must have null label (no future data)."""
        result = add_labels(ohlcv_with_atr, horizons=[horizon])
        col = f"label_{horizon}"
        tail = result.tail(horizon)[col]
        assert tail.is_null().all(), f"Last {horizon} rows of {col} must be null"

    def test_dtype_is_int8(self, ohlcv_with_atr):
        """Test proper typed format applied effectively against dataset generation operations."""
        result = add_labels(ohlcv_with_atr, horizons=[5])
        assert result["label_5"].dtype == pl.Int8

    def test_raises_without_atr(self, sample_ohlcv):
        """Should raise ValueError if atr_14 column is missing."""
        with pytest.raises(ValueError, match="atr_14"):
            add_labels(sample_ohlcv, horizons=[5])

    @pytest.mark.parametrize("horizon", HORIZONS)
    def test_multiple_horizons_independent(self, ohlcv_with_atr, horizon):
        """Each horizon's labels should be independently derived."""
        result = add_labels(ohlcv_with_atr, horizons=HORIZONS)
        col = f"label_{horizon}"
        non_null = result[col].drop_nulls()
        assert len(non_null) == len(ohlcv_with_atr) - horizon

    def test_high_atr_mult_yields_more_neutrals(self, ohlcv_with_atr):
        """Higher ATR multiplier → wider threshold → more NEUTRAL labels."""
        result_low = add_labels(ohlcv_with_atr, horizons=[10], atr_mult=0.01)
        result_high = add_labels(ohlcv_with_atr, horizons=[10], atr_mult=100.0)
        neutrals_low = (result_low["label_10"].drop_nulls() == 0).sum()
        neutrals_high = (result_high["label_10"].drop_nulls() == 0).sum()
        assert neutrals_high >= neutrals_low, (
            "High ATR mult should produce at least as many neutrals"
        )


# ── compute_class_balance tests ───────────────────────────────────────────────


class TestComputeClassBalance:
    """Suite to trace frequency distributions amongst labeled data pools."""

    def test_balance_keys_present(self, ohlcv_with_atr):
        """Test existence of basic count dictionaries outputs keys format requirement."""
        df = add_labels(ohlcv_with_atr, horizons=[10]).drop_nulls("label_10")
        balance = compute_class_balance(df, "label_10")
        assert "counts" in balance
        assert "ratios" in balance

    def test_counts_sum_to_total(self, ohlcv_with_atr):
        """Ensure absolute metrics calculate symmetrically across dimensions."""
        df = add_labels(ohlcv_with_atr, horizons=[10]).drop_nulls("label_10")
        balance = compute_class_balance(df, "label_10")
        assert sum(balance["counts"].values()) == len(df)

    def test_ratios_sum_to_one(self, ohlcv_with_atr):
        """Ensure probability density metric ratio elements equal unity."""
        df = add_labels(ohlcv_with_atr, horizons=[10]).drop_nulls("label_10")
        balance = compute_class_balance(df, "label_10")
        total = sum(balance["ratios"].values())
        assert abs(total - 1.0) < 0.01, f"Ratios sum {total} != 1.0"

    def test_empty_frame_returns_zeros(self):
        """Ensure missing entries fallback to zeroes explicitly."""
        empty = pl.DataFrame({"label_10": pl.Series([], dtype=pl.Int8)})
        balance = compute_class_balance(empty, "label_10")
        assert all(v == 0 for v in balance["counts"].values())


# ── stratified_train_test_split tests ─────────────────────────────────────────


class TestTrainTestSplit:
    """Ensure data splits allocate samples effectively preventing leakage occurrences."""

    def test_sizes_correct(self, ohlcv_with_atr):
        """Assert resulting allocation limits exactly map input fractions requirements."""
        df = add_labels(ohlcv_with_atr, horizons=[5])
        train, test = stratified_train_test_split(df, "label_5", test_size=0.2)
        n = len(df)
        assert len(train) == int(n * 0.8)
        assert len(test) == n - int(n * 0.8)

    def test_train_before_test_chronologically(self, ohlcv_with_atr):
        """Verify no temporal leakage — all train timestamps < test timestamps."""
        df = add_labels(ohlcv_with_atr, horizons=[5]).sort("timestamp")
        train, test = stratified_train_test_split(df, "label_5", test_size=0.2)
        assert train["timestamp"].max() <= test["timestamp"].min(), (
            "Train rows must be strictly before test rows"
        )

    def test_no_rows_lost(self, ohlcv_with_atr):
        """Validate sample total equality representing exact partitioning matching sizes."""
        df = add_labels(ohlcv_with_atr, horizons=[5])
        train, test = stratified_train_test_split(df, "label_5", test_size=0.2)
        assert len(train) + len(test) == len(df)
