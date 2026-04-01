"""Unit tests for cross_validation module.

Tests for Purged K-Fold, Purged TimeSeriesSplit, and Walk-Forward validators.
"""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.model_selection import TimeSeriesSplit

from mlfx.training.cross_validation import (
    PurgedKFold,
    PurgedTimeSeriesSplit,
    WalkForwardValidator,
    get_cross_validator,
)


class TestPurgedKFold:
    """Tests for PurgedKFold cross-validator."""

    def test_basic_split(self):
        """Test that PurgedKFold produces correct number of splits."""
        X = np.random.randn(1000, 10)
        cv = PurgedKFold(n_splits=5, label_horizon=10, embargo_pct=0.01)

        splits = list(cv.split(X))
        assert len(splits) == 5

    def test_get_n_splits(self):
        """Test get_n_splits returns correct value."""
        cv = PurgedKFold(n_splits=5, label_horizon=10, embargo_pct=0.01)
        assert cv.get_n_splits() == 5

    def test_purging_removes_overlapping_samples(self):
        """Test that purging removes samples whose labels overlap with test set."""
        X = np.random.randn(1000, 10)
        label_horizon = 10
        cv = PurgedKFold(n_splits=5, label_horizon=label_horizon, embargo_pct=0.0)

        for train_idx, test_idx in cv.split(X):
            # No training sample should be within label_horizon of test start
            # because those samples' labels would use test period information
            test_start = test_idx[0]
            # Training samples before test should end at least label_horizon before test
            train_before_test = train_idx[train_idx < test_start]
            if len(train_before_test) > 0:
                assert train_before_test[-1] < test_start - label_horizon

    def test_embargo_applied(self):
        """Test that embargo is correctly applied after test set."""
        X = np.random.randn(1000, 10)
        embargo_pct = 0.02
        cv = PurgedKFold(n_splits=5, label_horizon=10, embargo_pct=embargo_pct)

        embargo_size = int(1000 * embargo_pct)
        for train_idx, test_idx in cv.split(X):
            test_end = test_idx[-1]
            # Training samples after embargo should start after test_end + embargo
            train_after_test = train_idx[train_idx > test_end]
            if len(train_after_test) > 0:
                assert train_after_test[0] >= test_end + embargo_size

    def test_no_data_leakage(self):
        """Test that there's no overlap between train and test indices."""
        X = np.random.randn(1000, 10)
        cv = PurgedKFold(n_splits=5, label_horizon=10, embargo_pct=0.01)

        for train_idx, test_idx in cv.split(X):
            # No overlap between train and test
            assert len(np.intersect1d(train_idx, test_idx)) == 0

    def test_invalid_parameters(self):
        """Test that invalid parameters raise errors."""
        # n_splits < 2
        with pytest.raises(ValueError, match="n_splits must be >= 2"):
            PurgedKFold(n_splits=1)

        # label_horizon < 1
        with pytest.raises(ValueError, match="label_horizon must be >= 1"):
            PurgedKFold(label_horizon=0)

        # embargo_pct out of range
        with pytest.raises(ValueError, match="embargo_pct must be in"):
            PurgedKFold(embargo_pct=1.0)


class TestPurgedTimeSeriesSplit:
    """Tests for PurgedTimeSeriesSplit cross-validator."""

    def test_basic_split(self):
        """Test that PurgedTimeSeriesSplit produces correct number of splits."""
        X = np.random.randn(1000, 10)
        cv = PurgedTimeSeriesSplit(n_splits=5, label_horizon=10, embargo_pct=0.01)

        splits = list(cv.split(X))
        assert len(splits) == 5

    def test_expanding_window(self):
        """Test that training window expands over time."""
        X = np.random.randn(1000, 10)
        cv = PurgedTimeSeriesSplit(n_splits=5, label_horizon=10, embargo_pct=0.0)

        train_sizes = []
        for train_idx, test_idx in cv.split(X):
            train_sizes.append(len(train_idx))
            # Test set should come after training set
            assert train_idx[-1] < test_idx[0]

        # Training window should expand
        assert train_sizes == sorted(train_sizes)

    def test_purging_applied(self):
        """Test that purging is correctly applied."""
        X = np.random.randn(1000, 10)
        label_horizon = 10
        cv = PurgedTimeSeriesSplit(n_splits=5, label_horizon=label_horizon, embargo_pct=0.0)

        for train_idx, test_idx in cv.split(X):
            # Last training sample should be at least label_horizon before test start
            assert train_idx[-1] < test_idx[0] - label_horizon

    def test_no_data_leakage(self):
        """Test that there's no overlap between train and test indices."""
        X = np.random.randn(1000, 10)
        cv = PurgedTimeSeriesSplit(n_splits=5, label_horizon=10, embargo_pct=0.01)

        for train_idx, test_idx in cv.split(X):
            assert len(np.intersect1d(train_idx, test_idx)) == 0


class TestWalkForwardValidator:
    """Tests for WalkForwardValidator cross-validator."""

    def test_basic_split(self):
        """Test that WalkForwardValidator produces splits."""
        X = np.random.randn(2000, 10)
        cv = WalkForwardValidator(
            train_window=0,  # Expanding
            refit_frequency=200,
            label_horizon=10,
            embargo_pct=0.01,
        )

        splits = list(cv.split(X))
        assert len(splits) >= 1

    def test_expanding_window(self):
        """Test expanding window (train_window=0)."""
        X = np.random.randn(2000, 10)
        cv = WalkForwardValidator(
            train_window=0,
            refit_frequency=200,
            label_horizon=10,
        )

        train_sizes = []
        for train_idx, test_idx in cv.split(X):
            train_sizes.append(len(train_idx))

        # Training window should expand
        assert train_sizes == sorted(train_sizes)

    def test_rolling_window(self):
        """Test rolling window (train_window > 0)."""
        X = np.random.randn(2000, 10)
        train_window = 500
        cv = WalkForwardValidator(
            train_window=train_window,
            refit_frequency=200,
            label_horizon=10,
        )

        for train_idx, test_idx in cv.split(X):
            # Training window should be approximately train_window size
            # (may be slightly less due to purging)
            assert len(train_idx) <= train_window

    def test_purging_applied(self):
        """Test that purging is correctly applied."""
        X = np.random.randn(2000, 10)
        label_horizon = 10
        cv = WalkForwardValidator(
            train_window=0,
            refit_frequency=200,
            label_horizon=label_horizon,
            embargo_pct=0.0,
        )

        for train_idx, test_idx in cv.split(X):
            # Last training sample should be at least label_horizon before test start
            if len(train_idx) > 0 and len(test_idx) > 0:
                assert train_idx[-1] < test_idx[0] - label_horizon

    def test_no_data_leakage(self):
        """Test that there's no overlap between train and test indices."""
        X = np.random.randn(2000, 10)
        cv = WalkForwardValidator(
            train_window=0,
            refit_frequency=200,
            label_horizon=10,
            embargo_pct=0.01,
        )

        for train_idx, test_idx in cv.split(X):
            assert len(np.intersect1d(train_idx, test_idx)) == 0

    def test_get_n_splits(self):
        """Test get_n_splits returns correct value."""
        X = np.random.randn(2000, 10)
        cv = WalkForwardValidator(
            train_window=0,
            refit_frequency=200,
            label_horizon=10,
        )

        n_splits = cv.get_n_splits(X)
        assert n_splits >= 1


class TestGetCrossValidator:
    """Tests for get_cross_validator factory function."""

    def test_returns_purged_kfold(self):
        """Test that 'purged_kfold' returns PurgedKFold instance."""
        cv = get_cross_validator("purged_kfold", n_splits=5, label_horizon=10)
        assert isinstance(cv, PurgedKFold)
        assert cv.n_splits == 5
        assert cv.label_horizon == 10

    def test_returns_purged_timeseries(self):
        """Test that 'purged_timeseries' returns PurgedTimeSeriesSplit instance."""
        cv = get_cross_validator("purged_timeseries", n_splits=5, label_horizon=10)
        assert isinstance(cv, PurgedTimeSeriesSplit)
        assert cv.n_splits == 5
        assert cv.label_horizon == 10

    def test_returns_walk_forward(self):
        """Test that 'walk_forward' returns WalkForwardValidator instance."""
        cv = get_cross_validator(
            "walk_forward",
            train_window=500,
            refit_frequency=200,
            label_horizon=10,
        )
        assert isinstance(cv, WalkForwardValidator)
        assert cv.train_window == 500
        assert cv.refit_frequency == 200

    def test_returns_timeseries_fallback(self):
        """Test that unknown method returns standard TimeSeriesSplit."""
        cv = get_cross_validator("timeseries", n_splits=5)
        assert isinstance(cv, TimeSeriesSplit)
        assert cv.n_splits == 5

    def test_case_insensitive(self):
        """Test that method name is case-insensitive."""
        cv1 = get_cross_validator("PURGED_KFOLD")
        cv2 = get_cross_validator("Purged_KFold")
        cv3 = get_cross_validator("purged_kfold")
        assert isinstance(cv1, PurgedKFold)
        assert isinstance(cv2, PurgedKFold)
        assert isinstance(cv3, PurgedKFold)


class TestIntegration:
    """Integration tests for cross-validation with realistic data."""

    def test_purged_kfold_with_label_horizon(self):
        """Test PurgedKFold with different label horizons."""
        X = np.random.randn(1000, 10)

        for horizon in [5, 10, 20]:
            cv = PurgedKFold(n_splits=5, label_horizon=horizon, embargo_pct=0.01)
            for train_idx, test_idx in cv.split(X):
                # Verify purging distance
                test_start = test_idx[0]
                train_before = train_idx[train_idx < test_start]
                if len(train_before) > 0:
                    assert train_before[-1] < test_start - horizon

    def test_comparison_with_standard_timeseries(self):
        """Compare purged CV with standard TimeSeriesSplit."""
        X = np.random.randn(1000, 10)

        # Standard TimeSeriesSplit
        tscv = TimeSeriesSplit(n_splits=5)
        standard_train_sizes = [len(train) for train, _ in tscv.split(X)]

        # Purged TimeSeriesSplit
        pcv = PurgedTimeSeriesSplit(n_splits=5, label_horizon=10, embargo_pct=0.01)
        purged_train_sizes = [len(train) for train, _ in pcv.split(X)]

        # Purged should have smaller training sets due to purging/embargo
        for std, purged in zip(standard_train_sizes, purged_train_sizes):
            assert purged <= std
