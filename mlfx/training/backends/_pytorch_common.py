"""Shared HPO scaffold for PyTorch sequence-based backends.

This module eliminates the bulk of near-identical boilerplate that was
previously duplicated across multiple sequence model implementations.

Each backend supplies two callables:

``train_once_fn``
    The backend-specific single-fold training function with signature::

        train_once_fn(
            X_tr, y_tr, X_val, y_val,
            seq_len, epochs, batch_size, patience,
            **model_params,
        ) -> tuple[model, val_f1, history]

``suggest_params_fn``
    An Optuna trial callback that returns a ``dict`` of model hyperparameters
    (the ``**model_params`` passed to *train_once_fn*) or ``None`` to flag an
    invalid combination (the trial objective returns ``0.0``)::

        suggest_params_fn(trial) -> dict[str, Any] | None

Usage example (lstm.py)::

    from mlfx.training.backends._pytorch_common import run_pytorch_hpo

    def _suggest_params(trial):
        return {
            "hidden_size": trial.suggest_categorical("hidden_size", [32, 64, 128]),
            "num_layers":  trial.suggest_int("num_layers", 1, 3),
            "dropout":     trial.suggest_float("dropout", 0.1, 0.5),
            "lr":          trial.suggest_float("lr", 1e-4, 5e-3, log=True),
        }

    def train_lstm(X, y, feature_cols, *, n_trials, ...):
        return run_pytorch_hpo(
            train_once_fn=train_lstm_once,
            suggest_params_fn=_suggest_params,
            X=X, y=y, feature_cols=feature_cols,
            model_type="LSTM",
            n_trials=n_trials, ...
        )
"""

from __future__ import annotations

import logging
from typing import Any, Callable

import numpy as np
import optuna
import torch
from sklearn.feature_selection import SelectKBest, f_classif, VarianceThreshold

from mlfx.training.backends._sequence_utils import create_sequences
from mlfx.training.cross_validation import get_cross_validator
from mlfx.training.evaluation import compute_classification_metrics

logger = logging.getLogger(__name__)


def run_pytorch_hpo(
    train_once_fn: Callable[..., tuple[Any, float, list[dict]]],
    suggest_params_fn: Callable[[optuna.Trial], dict[str, Any] | None],
    X: np.ndarray,
    y: np.ndarray,
    feature_cols: list[str],
    *,
    model_type: str,
    n_trials: int,
    n_splits: int,
    seq_len: int,
    epochs: int,
    batch_size: int,
    patience: int,
    top_k_features: int,
    seed: int,
    cv_method: str = "purged_timeseries",
    embargo_pct: float = 0.01,
    label_horizon: int = 10,
) -> tuple[Any, dict[str, Any]]:
    """Feature selection → Optuna HPO → OOS evaluation → final model.

    Parameters
    ----------
    train_once_fn:
        Backend-specific single-fold trainer.  Called as::

            train_once_fn(
                X_tr, y_tr, X_val, y_val,
                seq_len=seq_len, epochs=epochs, batch_size=batch_size,
                patience=patience, **params,
            )

    suggest_params_fn:
        ``(trial) → dict | None``.  Return *None* to mark an invalid trial
        (e.g. a hyperparameter constraint is violated); the objective returns
        ``0.0`` for that trial.
    X, y, feature_cols:
        Pre-loaded feature matrix, label array, and column names.
    model_type:
        Short string stored in the returned metrics dict (e.g. ``"LSTM"``).
    cv_method:
        Cross-validation method: "purged_kfold", "purged_timeseries",
        "walk_forward", or "timeseries" (default: "purged_timeseries").
    embargo_pct:
        Percentage of data to embargo after each test fold (default: 0.01).
    label_horizon:
        Number of bars ahead used in label generation (default: 10).

    Returns
    -------
    tuple[model, metrics_dict]
        *model* is the final trained model; *metrics_dict* contains
        ``best_cv_f1_macro``, ``f1_macro_oos``, ``best_params``,
        ``selected_features``, ``seq_len``, ``n_samples``, ``history``,
        ``model_type``, ``cv_method``, ``embargo_pct``, ``label_horizon``.
    """
    # ------------------------------------------------------------------
    # 1. Feature selection
    # ------------------------------------------------------------------
    # First, remove constant features (zero variance) to avoid sklearn warnings
    variance_selector = VarianceThreshold(threshold=0.0)
    X_var = variance_selector.fit_transform(X)
    non_constant_mask = variance_selector.get_support()
    feature_cols_non_constant = [f for i, f in enumerate(feature_cols) if non_constant_mask[i]]
    n_removed = len(feature_cols) - len(feature_cols_non_constant)
    if n_removed > 0:
        logger.debug("Removed %d constant features before selection", n_removed)

    # Then apply SelectKBest on non-constant features
    logger.info("Applying feature selection (top %d of %d)", top_k_features, X_var.shape[1])
    k = min(top_k_features, X_var.shape[1])
    selector = SelectKBest(score_func=f_classif, k=k)
    X_sel: np.ndarray = selector.fit_transform(X_var, y)
    selected_features = [f for i, f in enumerate(feature_cols_non_constant) if selector.get_support()[i]]

    # ------------------------------------------------------------------
    # 2. Optuna HPO
    # ------------------------------------------------------------------
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=seed),
    )

    def _objective(trial: optuna.Trial) -> float:
        params = suggest_params_fn(trial)
        if params is None:
            # Invalid hyperparameter combination (e.g. d_model % nhead != 0).
            return 0.0

        cv = get_cross_validator(
            method=cv_method,
            n_splits=n_splits,
            label_horizon=label_horizon,
            embargo_pct=embargo_pct,
        )
        f1_scores: list[float] = []
        for train_idx, val_idx in cv.split(X_sel):
            if len(train_idx) <= seq_len or len(val_idx) <= seq_len:
                continue
            _, val_f1, _ = train_once_fn(
                X_sel[train_idx], y[train_idx],
                X_sel[val_idx], y[val_idx],
                seq_len=seq_len,
                epochs=epochs,
                batch_size=batch_size,
                patience=patience,
                **params,
            )
            f1_scores.append(val_f1)
        return float(np.mean(f1_scores)) if f1_scores else 0.0

    study.optimize(_objective, n_trials=n_trials, show_progress_bar=False)
    best_params = study.best_params
    logger.info("Best %s params: %s | CV F1: %.4f", model_type, best_params, study.best_value)

    # ------------------------------------------------------------------
    # 3. Out-of-sample evaluation (walk-forward CV with best params)
    # ------------------------------------------------------------------
    cv = get_cross_validator(
        method=cv_method,
        n_splits=n_splits,
        label_horizon=label_horizon,
        embargo_pct=embargo_pct,
    )
    oos_preds = np.full(len(y), -1, dtype=y.dtype)
    oos_labels = np.full(len(y), -1, dtype=y.dtype)

    for train_idx, val_idx in cv.split(X_sel):
        if len(train_idx) <= seq_len or len(val_idx) <= seq_len:
            continue
        model_cv, _, _ = train_once_fn(
            X_sel[train_idx], y[train_idx],
            X_sel[val_idx], y[val_idx],
            seq_len=seq_len,
            epochs=epochs,
            batch_size=batch_size,
            patience=patience,
            **best_params,
        )
        model_cv.eval()
        X_val_seq, y_val_seq = create_sequences(X_sel[val_idx], y[val_idx], seq_len=seq_len)
        with torch.no_grad():
            preds = model_cv(torch.tensor(X_val_seq)).argmax(1).cpu().numpy()
        oos_preds[val_idx[seq_len:]] = preds
        oos_labels[val_idx[seq_len:]] = y_val_seq

    valid_mask = oos_preds != -1
    f1_macro_oos = compute_classification_metrics(oos_labels[valid_mask], oos_preds[valid_mask])

    # ------------------------------------------------------------------
    # 4. Final model — train on first 90 %, evaluate on last 10 %
    # ------------------------------------------------------------------
    cut = int(len(X_sel) * 0.9)
    final_model, _, history = train_once_fn(
        X_sel[:cut], y[:cut],
        X_sel[cut:], y[cut:],
        seq_len=seq_len,
        epochs=epochs,
        batch_size=batch_size,
        patience=patience,
        **best_params,
    )

    metrics: dict[str, Any] = {
        "best_cv_f1_macro": study.best_value,
        "f1_macro_oos": f1_macro_oos,
        "best_params": best_params,
        "selected_features": selected_features,
        "seq_len": seq_len,
        "n_samples": len(X),
        "history": history,
        "model_type": model_type,
        "cv_method": cv_method,
        "embargo_pct": embargo_pct,
        "label_horizon": label_horizon,
    }
    logger.info("Final OOS F1: %.4f", f1_macro_oos)
    return final_model, metrics
