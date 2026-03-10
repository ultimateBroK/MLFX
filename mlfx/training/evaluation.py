"""Shared evaluation metrics for all training backends.

Centralises the f1_score call so every backend uses the same averaging strategy
and zero_division handling.  Import :func:`compute_classification_metrics` instead
of calling ``sklearn.metrics.f1_score`` directly in backend code.
"""

from __future__ import annotations

from typing import TypedDict

import numpy as np
from sklearn.metrics import f1_score


class EvaluationMetrics(TypedDict):
    """Shape of the metrics dict returned by :func:`run_pytorch_hpo`."""

    best_cv_f1_macro: float
    f1_macro_oos: float
    best_params: dict
    selected_features: list[str]
    seq_len: int
    n_samples: int
    history: list[dict]
    model_type: str


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    average: str = "macro",
) -> float:
    """Return macro F1-score for multi-class classification predictions.

    Parameters
    ----------
    y_true:
        Ground-truth integer labels.
    y_pred:
        Predicted integer labels (same shape as *y_true*).
    average:
        Averaging strategy forwarded to :func:`sklearn.metrics.f1_score`.
        Defaults to ``"macro"`` (unweighted mean across classes).

    Returns
    -------
    float
        F1 score in *[0, 1]*.  Returns ``0.0`` for empty inputs or
        degenerate predictions (``zero_division=0``).
    """
    if len(y_true) == 0:
        return 0.0
    return float(f1_score(y_true, y_pred, average=average, zero_division=0))
