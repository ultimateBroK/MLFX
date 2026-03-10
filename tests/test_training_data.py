"""Tests for training data-loading and feature-selection helpers.

Covers:
  - ``select_numeric_feature_columns`` blacklist enforcement
  - ``load_labelled_dataset`` null path (missing directory)
  - ``prepare_tabular_data`` null path (no data or missing label column)
  - ``prepare_tabular_data`` label-mapping: raw {-2,-1,0,1,2} → {0,1,2,3,4}
  - ``prepare_tabular_data`` NaN row-dropping
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from mlfx.training.data import load_labelled_dataset, prepare_tabular_data
from mlfx.training.feature_selection import (
    DEFAULT_FEATURE_BLACKLIST,
    select_numeric_feature_columns,
)


# ── feature_selection ─────────────────────────────────────────────────────────


def test_select_numeric_excludes_blacklisted_cols(fake_feature_df: pl.DataFrame) -> None:
    """Blacklisted price / target columns must not appear in selected features."""
    selected = select_numeric_feature_columns(fake_feature_df)
    for col in DEFAULT_FEATURE_BLACKLIST:
        assert col not in selected, f"Blacklisted column '{col}' must not be selected"


def test_select_numeric_returns_only_feature_cols(
    fake_feature_df: pl.DataFrame, fake_feature_cols: list[str]
) -> None:
    """All 20 feat_* columns should be returned and nothing extra."""
    selected = select_numeric_feature_columns(fake_feature_df)
    assert set(selected) == set(fake_feature_cols), (
        "Selected features must exactly match the 20 feat_* columns"
    )


def test_select_numeric_respects_custom_blacklist() -> None:
    """A caller-supplied blacklist overrides the default."""
    df = pl.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0], "c": [5.0, 6.0]})
    selected = select_numeric_feature_columns(df, blacklist={"b"})
    assert "b" not in selected
    assert "a" in selected
    assert "c" in selected


# ── load_labelled_dataset ─────────────────────────────────────────────────────


def test_load_labelled_dataset_returns_none_for_missing_symbol() -> None:
    """Non-existent symbol / timeframe must return None, not raise."""
    result = load_labelled_dataset("__NO_SUCH_SYMBOL__", "9M")
    assert result is None


# ── prepare_tabular_data ──────────────────────────────────────────────────────


def test_prepare_tabular_data_returns_none_when_no_files() -> None:
    """Non-existent symbol / timeframe must return None, not raise."""
    result = prepare_tabular_data("__NO_SUCH_SYMBOL__", "9M", "label_10")
    assert result is None


def test_prepare_tabular_data_label_mapping(monkeypatch) -> None:
    """Labels must be shifted by +2: raw {-2,-1,0,1,2} → encoded {0,1,2,3,4}."""
    raw_labels = [-2, -1, 0, 1, 2]
    df = pl.DataFrame({"feat_a": [1.0] * 5, "label_10": raw_labels})
    monkeypatch.setattr(
        "mlfx.training.data.load_labelled_dataset",
        lambda *a, **kw: df,
    )

    result = prepare_tabular_data("SYM", "1H", "label_10")

    assert result is not None, "Should return data when mock provides a valid DataFrame"
    _, y, _ = result
    expected = np.array([0, 1, 2, 3, 4], dtype=np.int64)
    np.testing.assert_array_equal(y, expected, err_msg="Label mapping raw+2 failed")


def test_prepare_tabular_data_drops_nan_rows(monkeypatch) -> None:
    """Rows that contain null in any feature column must be dropped."""
    df = pl.DataFrame(
        {
            "feat_a": pl.Series([1.0, None, 3.0], dtype=pl.Float32),
            "feat_b": pl.Series([4.0, 5.0, 6.0], dtype=pl.Float32),
            "label_10": [0, 1, -1],
        }
    )
    monkeypatch.setattr(
        "mlfx.training.data.load_labelled_dataset",
        lambda *a, **kw: df,
    )

    result = prepare_tabular_data("SYM", "1H", "label_10")

    assert result is not None
    X, y, _ = result
    assert X.shape[0] == 2, "Row with NaN must be dropped; only 2 valid rows remain"
    assert y.shape[0] == 2


def test_prepare_tabular_data_returns_none_for_missing_label_col(monkeypatch) -> None:
    """If the requested label column is absent the function must return None."""
    df = pl.DataFrame({"feat_a": [1.0, 2.0], "label_5": [0, 1]})
    monkeypatch.setattr(
        "mlfx.training.data.load_labelled_dataset",
        lambda *a, **kw: df,
    )

    result = prepare_tabular_data("SYM", "1H", "label_10")  # label_10 absent
    assert result is None
