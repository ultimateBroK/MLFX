"""Tests for mlfx.training.evaluation helpers.

Covers:
  - ``compute_classification_metrics`` — perfect, known, all-wrong, and empty inputs
  - ``EvaluationMetrics`` TypedDict — all required keys are declared
"""

from __future__ import annotations

import numpy as np
import pytest

from mlfx.training.evaluation import EvaluationMetrics, compute_classification_metrics


# ── compute_classification_metrics ───────────────────────────────────────────


def test_compute_metrics_perfect_predictions() -> None:
    """Identical true and predicted labels must yield F1 = 1.0."""
    y = np.array([0, 1, 2, 3, 4], dtype=np.int64)
    score = compute_classification_metrics(y, y)
    assert score == pytest.approx(1.0)


def test_compute_metrics_known_value() -> None:
    """Verify a manually computed macro-F1 value.

    y_true = [0, 1, 2], y_pred = [0, 2, 1]
    Class 0: TP=1, FP=0, FN=0 → precision=1,  recall=1   → F1=1.0
    Class 1: TP=0, FP=1, FN=1 → precision=0,  recall=0   → F1=0.0 (zero_division=0)
    Class 2: TP=0, FP=1, FN=1 → precision=0,  recall=0   → F1=0.0 (zero_division=0)
    Macro F1 = (1.0 + 0.0 + 0.0) / 3 ≈ 0.333...
    """
    y_true = np.array([0, 1, 2], dtype=np.int64)
    y_pred = np.array([0, 2, 1], dtype=np.int64)
    score = compute_classification_metrics(y_true, y_pred)
    assert score == pytest.approx(1.0 / 3.0, abs=1e-6)


def test_compute_metrics_all_wrong_is_non_negative() -> None:
    """Worst-case predictions must still give a valid (non-negative) score."""
    y_true = np.array([0, 0, 0, 0], dtype=np.int64)
    y_pred = np.array([1, 2, 3, 4], dtype=np.int64)
    score = compute_classification_metrics(y_true, y_pred)
    assert 0.0 <= score < 1.0


def test_compute_metrics_empty_arrays_returns_zero() -> None:
    """Empty arrays must return 0.0 without raising."""
    score = compute_classification_metrics(
        np.array([], dtype=np.int64), np.array([], dtype=np.int64)
    )
    assert score == pytest.approx(0.0)


def test_compute_metrics_accepts_binary_labels() -> None:
    """Binary (two-class) case must work without errors."""
    y = np.array([0, 1, 0, 1], dtype=np.int64)
    y_pred = np.array([0, 1, 1, 0], dtype=np.int64)
    score = compute_classification_metrics(y, y_pred)
    assert 0.0 <= score <= 1.0


# ── EvaluationMetrics TypedDict ───────────────────────────────────────────────


def test_evaluation_metrics_has_all_required_keys() -> None:
    """Constructing a compliant EvaluationMetrics dict must satisfy all keys."""
    required_keys = {
        "best_cv_f1_macro",
        "f1_macro_oos",
        "best_params",
        "selected_features",
        "seq_len",
        "n_samples",
        "history",
        "model_type",
    }
    metrics: EvaluationMetrics = {
        "best_cv_f1_macro": 0.75,
        "f1_macro_oos": 0.70,
        "best_params": {"lr": 1e-3},
        "selected_features": ["feat_00", "feat_01"],
        "seq_len": 60,
        "n_samples": 1000,
        "history": [{"epoch": 1, "val_f1": 0.65}],
        "model_type": "lstm",
    }
    assert set(metrics.keys()) == required_keys
