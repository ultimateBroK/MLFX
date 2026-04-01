"""Purged K-Fold and Walk-Forward cross-validation for financial time series.

This module implements cross-validation strategies from Marcos Lopez de Prado's
"Advances in Financial Machine Learning" to prevent data leakage in financial
time series ML training.

Key Concepts:
- Purging: Remove training samples whose labels overlap with test set labels
- Embargo: Add a buffer period after each test set to prevent serial correlation
- Walk-Forward: Simulate real trading by periodically refitting the model
"""

from __future__ import annotations

import logging
from typing import Iterator

import numpy as np
from sklearn.model_selection import BaseCrossValidator

logger = logging.getLogger(__name__)


class PurgedKFold(BaseCrossValidator):
    """K-Fold with purging and embargo for financial time series.

    Purging removes training samples whose labels overlap with test set labels.
    Embargo adds a buffer period after each test set to prevent serial correlation.

    This addresses the data leakage problem in financial ML where labels are
    computed using future information (e.g., label_10 uses close[i] and close[i+10]).

    Parameters
    ----------
    n_splits : int
        Number of folds.
    label_horizon : int
        Number of bars ahead used in label generation (e.g., 10 for label_10).
    embargo_pct : float
        Percentage of data to embargo after each test fold (default 0.01 = 1%).

    Examples
    --------
    >>> import numpy as np
    >>> X = np.random.randn(1000, 10)
    >>> cv = PurgedKFold(n_splits=5, label_horizon=10, embargo_pct=0.01)
    >>> for train_idx, test_idx in cv.split(X):
    ...     print(f"Train: {len(train_idx)}, Test: {len(test_idx)}")
    """

    def __init__(
        self,
        n_splits: int = 5,
        label_horizon: int = 10,
        embargo_pct: float = 0.01,
    ) -> None:
        if n_splits < 2:
            raise ValueError("n_splits must be >= 2")
        if label_horizon < 1:
            raise ValueError("label_horizon must be >= 1")
        if not 0.0 <= embargo_pct < 1.0:
            raise ValueError("embargo_pct must be in [0, 1)")

        self.n_splits = n_splits
        self.label_horizon = label_horizon
        self.embargo_pct = embargo_pct

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        """Returns the number of splitting iterations in the cross-validator."""
        return self.n_splits

    def split(self, X, y=None, groups=None) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        """Generate indices to split data into training and test set.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,), optional
            The target variable for supervised learning problems.
        groups : array-like of shape (n_samples,), optional
            Group labels for the samples used while splitting.

        Yields
        ------
        train : ndarray
            The training set indices for that split.
        test : ndarray
            The testing set indices for that split.
        """
        n_samples = len(X)
        indices = np.arange(n_samples)
        fold_size = n_samples // self.n_splits
        embargo_size = int(n_samples * self.embargo_pct)

        for i in range(self.n_splits):
            # Test set indices
            test_start = i * fold_size
            test_end = test_start + fold_size if i < self.n_splits - 1 else n_samples
            test_indices = indices[test_start:test_end]

            # Purge: remove training samples whose labels overlap with test
            # A sample at index j has label using info from j to j+label_horizon
            # So we purge samples where j+label_horizon >= test_start
            # This means we purge samples from (test_start - label_horizon) onwards
            purge_start = max(0, test_start - self.label_horizon)

            # Embargo: add buffer after test set
            embargo_end = min(n_samples, test_end + embargo_size)

            # Training indices (exclude purged and embargoed)
            # Train on data before the purge point and after the embargo
            train_indices = np.concatenate([
                indices[:purge_start],
                indices[embargo_end:],
            ])

            yield train_indices, test_indices


class PurgedTimeSeriesSplit(BaseCrossValidator):
    """TimeSeriesSplit with purging and embargo.

    Expanding window approach with purging and embargo for realistic evaluation.
    This is the recommended cross-validator for financial time series HPO.

    The training window expands over time, and each test fold is followed by
    an embargo period to prevent serial correlation from contaminating results.

    Parameters
    ----------
    n_splits : int
        Number of splits.
    label_horizon : int
        Number of bars ahead used in label generation.
    embargo_pct : float
        Percentage of data to embargo after each validation fold.

    Examples
    --------
    >>> import numpy as np
    >>> X = np.random.randn(1000, 10)
    >>> cv = PurgedTimeSeriesSplit(n_splits=5, label_horizon=10, embargo_pct=0.01)
    >>> for train_idx, test_idx in cv.split(X):
    ...     print(f"Train: {len(train_idx)}, Test: {len(test_idx)}")
    """

    def __init__(
        self,
        n_splits: int = 5,
        label_horizon: int = 10,
        embargo_pct: float = 0.01,
    ) -> None:
        if n_splits < 2:
            raise ValueError("n_splits must be >= 2")
        if label_horizon < 1:
            raise ValueError("label_horizon must be >= 1")
        if not 0.0 <= embargo_pct < 1.0:
            raise ValueError("embargo_pct must be in [0, 1)")

        self.n_splits = n_splits
        self.label_horizon = label_horizon
        self.embargo_pct = embargo_pct

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        """Returns the number of splitting iterations in the cross-validator."""
        return self.n_splits

    def split(self, X, y=None, groups=None) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        """Generate indices to split data into training and test set.

        Uses an expanding window approach where the training set grows over time.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,), optional
            The target variable for supervised learning problems.
        groups : array-like of shape (n_samples,), optional
            Group labels for the samples used while splitting.

        Yields
        ------
        train : ndarray
            The training set indices for that split.
        test : ndarray
            The testing set indices for that split.
        """
        n_samples = len(X)
        indices = np.arange(n_samples)
        embargo_size = int(n_samples * self.embargo_pct)

        # Calculate test fold size
        test_size = n_samples // (self.n_splits + 1)

        for i in range(self.n_splits):
            # Expanding training window
            train_end = n_samples - (self.n_splits - i) * test_size
            test_start = train_end
            test_end = test_start + test_size

            # Apply embargo after test set
            embargoed_test_end = min(n_samples, test_end + embargo_size)

            # Purge: remove samples whose labels would use test period info
            # A sample at index j uses info from j to j+label_horizon
            # We need j+label_horizon < test_start for sample j to be safe
            # So j < test_start - label_horizon
            purge_end = min(train_end, test_start - self.label_horizon)

            train_indices = indices[:purge_end]
            test_indices = indices[test_start:embargoed_test_end]

            yield train_indices, test_indices


class WalkForwardValidator(BaseCrossValidator):
    """Walk-forward validation with periodic refitting.

    Simulates real trading by periodically refitting the model on a rolling
    or expanding window. This provides the most realistic evaluation of
    trading strategy performance.

    Parameters
    ----------
    train_window : int
        Number of bars in training window. Use 0 for expanding window.
    refit_frequency : int
        Number of bars between refits (test period size).
    label_horizon : int
        Number of bars ahead used in label generation.
    embargo_pct : float
        Percentage of data to embargo after each test period.
    min_train_size : int
        Minimum number of samples required for initial training.

    Examples
    --------
    >>> import numpy as np
    >>> X = np.random.randn(1000, 10)
    >>> # Expanding window
    >>> cv = WalkForwardValidator(train_window=0, refit_frequency=100, label_horizon=10)
    >>> for train_idx, test_idx in cv.split(X):
    ...     print(f"Train: {len(train_idx)}, Test: {len(test_idx)}")
    >>> # Rolling window
    >>> cv = WalkForwardValidator(train_window=500, refit_frequency=100, label_horizon=10)
    >>> for train_idx, test_idx in cv.split(X):
    ...     print(f"Train: {len(train_idx)}, Test: {len(test_idx)}")
    """

    def __init__(
        self,
        train_window: int = 0,
        refit_frequency: int = 500,
        label_horizon: int = 10,
        embargo_pct: float = 0.01,
        min_train_size: int = 1000,
    ) -> None:
        if train_window < 0:
            raise ValueError("train_window must be >= 0")
        if refit_frequency < 1:
            raise ValueError("refit_frequency must be >= 1")
        if label_horizon < 1:
            raise ValueError("label_horizon must be >= 1")
        if not 0.0 <= embargo_pct < 1.0:
            raise ValueError("embargo_pct must be in [0, 1)")

        self.train_window = train_window
        self.refit_frequency = refit_frequency
        self.label_horizon = label_horizon
        self.embargo_pct = embargo_pct
        self.min_train_size = min_train_size
        self._n_splits = None

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        """Returns the number of splitting iterations in the cross-validator."""
        if X is not None:
            n_samples = len(X)
            start = self.train_window if self.train_window > 0 else self.min_train_size
            self._n_splits = max(1, (n_samples - start) // self.refit_frequency)
        return self._n_splits or 1

    def split(self, X, y=None, groups=None) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        """Generate indices to split data into training and test set.

        Uses a walk-forward approach where the model is refitted periodically.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,), optional
            The target variable for supervised learning problems.
        groups : array-like of shape (n_samples,), optional
            Group labels for the samples used while splitting.

        Yields
        ------
        train : ndarray
            The training set indices for that split.
        test : ndarray
            The testing set indices for that split.
        """
        n_samples = len(X)
        indices = np.arange(n_samples)
        embargo_size = int(n_samples * self.embargo_pct)

        # Start after minimum training window
        start = self.train_window if self.train_window > 0 else self.min_train_size

        split_count = 0
        for split_point in range(start, n_samples - self.label_horizon, self.refit_frequency):
            # Training window (expanding or rolling)
            if self.train_window > 0:
                train_start = max(0, split_point - self.train_window)
            else:
                train_start = 0

            # Purge samples whose labels overlap with test
            # A sample at index j uses info from j to j+label_horizon
            # We need j+label_horizon < split_point for sample j to be safe
            train_end = split_point - self.label_horizon

            # Test period (after embargo)
            test_start = split_point + embargo_size
            test_end = min(n_samples, test_start + self.refit_frequency)

            if train_end <= train_start or test_end <= test_start:
                continue

            train_indices = indices[train_start:train_end]
            test_indices = indices[test_start:test_end]

            split_count += 1
            yield train_indices, test_indices

        self._n_splits = split_count


def get_cross_validator(
    method: str,
    n_splits: int = 5,
    label_horizon: int = 10,
    embargo_pct: float = 0.01,
    train_window: int = 0,
    refit_frequency: int = 500,
) -> BaseCrossValidator:
    """Factory function to create cross-validator by method name.

    Parameters
    ----------
    method : str
        One of:
        - "purged_kfold": K-Fold with purging and embargo
        - "purged_timeseries": TimeSeriesSplit with purging and embargo (recommended)
        - "walk_forward": Walk-forward validation with periodic refitting
        - "timeseries": Standard sklearn TimeSeriesSplit (backward compatible)
    n_splits : int
        Number of splits for K-Fold and TimeSeriesSplit methods.
    label_horizon : int
        Number of bars ahead used in label generation (e.g., 10 for label_10).
    embargo_pct : float
        Percentage of data to embargo after each test fold.
    train_window : int
        Number of bars in training window for walk_forward (0 = expanding).
    refit_frequency : int
        Number of bars between refits for walk_forward.

    Returns
    -------
    BaseCrossValidator
        The cross-validator instance.

    Examples
    --------
    >>> cv = get_cross_validator("purged_timeseries", n_splits=5, label_horizon=10)
    >>> for train_idx, test_idx in cv.split(X):
    ...     model.fit(X[train_idx], y[train_idx])
    """
    method_lower = method.lower().strip()

    if method_lower == "purged_kfold":
        logger.info(
            "Using PurgedKFold: n_splits=%d, label_horizon=%d, embargo_pct=%.4f",
            n_splits, label_horizon, embargo_pct
        )
        return PurgedKFold(
            n_splits=n_splits,
            label_horizon=label_horizon,
            embargo_pct=embargo_pct,
        )
    elif method_lower == "purged_timeseries":
        logger.info(
            "Using PurgedTimeSeriesSplit: n_splits=%d, label_horizon=%d, embargo_pct=%.4f",
            n_splits, label_horizon, embargo_pct
        )
        return PurgedTimeSeriesSplit(
            n_splits=n_splits,
            label_horizon=label_horizon,
            embargo_pct=embargo_pct,
        )
    elif method_lower == "walk_forward":
        logger.info(
            "Using WalkForwardValidator: train_window=%d, refit_frequency=%d, label_horizon=%d",
            train_window, refit_frequency, label_horizon
        )
        return WalkForwardValidator(
            train_window=train_window,
            refit_frequency=refit_frequency,
            label_horizon=label_horizon,
            embargo_pct=embargo_pct,
        )
    else:
        # Fallback to standard TimeSeriesSplit for backward compatibility
        from sklearn.model_selection import TimeSeriesSplit
        logger.info("Using standard TimeSeriesSplit: n_splits=%d", n_splits)
        return TimeSeriesSplit(n_splits=n_splits)
