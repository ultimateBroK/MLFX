"""
models/gradient_boost.py
========================
XGBoost and LightGBM classifiers for XAUUSD direction prediction.

Features:
  - Optuna hyperparameter tuning (TimeSeriesSplit CV)
  - Feature importance plotting + SHAP value analysis
  - Unified interface for XGB / LGB backend

Output: models/saved/{symbol}/{tf}/{backend}_{label_col}.model
        models/saved/{symbol}/{tf}/{backend}_{label_col}_metrics.json
        models/saved/{symbol}/{tf}/{backend}_{label_col}_importance.png
        models/saved/{symbol}/{tf}/{backend}_{label_col}_shap.png
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal

import joblib
import numpy as np
import polars as pl
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import TimeSeriesSplit

logger = logging.getLogger(__name__)

LABELS_DIR = Path("data/labels")
SAVED_DIR = Path("models/saved")

FEATURE_BLACKLIST = {
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "tick_count",
    "close_ahead_5",
    "close_ahead_10",
    "close_ahead_20",
    "label_5",
    "label_10",
    "label_20",
}

Backend = Literal["xgb", "lgb"]


# ── Feature prep (shared with knn.py) ──────────────────────────────────────────


def get_feature_columns(df: pl.DataFrame) -> list[str]:
    return [
        c
        for c in df.columns
        if c not in FEATURE_BLACKLIST
        and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int8)
    ]


def prepare_xy(
    df: pl.DataFrame, label_col: str
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    feature_cols = get_feature_columns(df)
    subset = df.select(feature_cols + [label_col]).drop_nulls()
    X = subset.select(feature_cols).to_numpy().astype(np.float32)
    y = subset[label_col].to_numpy().astype(np.int64)
    # Remap {-1, 0, 1} → {0, 1, 2} for multi-class classifiers
    y = y + 1  # SHORT→0, NEUTRAL→1, LONG→2
    return X, y, feature_cols


# ── Optuna objective ───────────────────────────────────────────────────────────


def _xgb_objective(trial, X: np.ndarray, y: np.ndarray, n_splits: int) -> float:
    import xgboost as xgb

    params = {
        "max_depth": trial.suggest_int("max_depth", 3, 8),
        "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.3, log=True),
        "n_estimators": trial.suggest_int("n_estimators", 100, 500),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "use_label_encoder": False,
        "eval_metric": "mlogloss",
        "objective": "multi:softmax",
        "num_class": 3,
        "verbosity": 0,
        "random_state": 42,
    }

    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores: list[float] = []
    for train_idx, val_idx in tscv.split(X):
        model = xgb.XGBClassifier(**params)
        model.fit(X[train_idx], y[train_idx], verbose=False)
        preds = model.predict(X[val_idx])
        scores.append(f1_score(y[val_idx], preds, average="macro", zero_division=0))
    return float(np.mean(scores))


def _lgb_objective(trial, X: np.ndarray, y: np.ndarray, n_splits: int) -> float:
    import lightgbm as lgb

    params = {
        "num_leaves": trial.suggest_int("num_leaves", 15, 127),
        "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.3, log=True),
        "n_estimators": trial.suggest_int("n_estimators", 100, 500),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
        "objective": "multiclass",
        "num_class": 3,
        "verbose": -1,
        "random_state": 42,
    }

    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores: list[float] = []
    for train_idx, val_idx in tscv.split(X):
        model = lgb.LGBMClassifier(**params)
        model.fit(X[train_idx], y[train_idx])
        preds = model.predict(X[val_idx])
        scores.append(f1_score(y[val_idx], preds, average="macro", zero_division=0))
    return float(np.mean(scores))


# ── Training ───────────────────────────────────────────────────────────────────


def train_xgboost(
    X: np.ndarray,
    y: np.ndarray,
    n_trials: int = 30,
    n_splits: int = 5,
) -> tuple[Any, dict]:
    """Train XGBClassifier with Optuna tuning. Returns (model, metrics)."""
    import optuna
    import xgboost as xgb

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize")
    study.optimize(
        lambda t: _xgb_objective(t, X, y, n_splits),
        n_trials=n_trials,
        show_progress_bar=False,
    )

    best_params = study.best_params | {
        "use_label_encoder": False,
        "eval_metric": "mlogloss",
        "objective": "multi:softmax",
        "num_class": 3,
        "verbosity": 0,
        "random_state": 42,
    }
    model = xgb.XGBClassifier(**best_params)
    model.fit(X, y, verbose=False)
    preds = model.predict(X)

    metrics = {
        "backend": "xgb",
        "best_params": study.best_params,
        "best_cv_f1_macro": study.best_value,
        "f1_macro_train": float(f1_score(y, preds, average="macro", zero_division=0)),
        "f1_weighted_train": float(
            f1_score(y, preds, average="weighted", zero_division=0)
        ),
        "n_samples": len(X),
        "n_trials": n_trials,
        "report": classification_report(y, preds, zero_division=0, output_dict=True),
    }
    logger.info(
        "XGB  best_cv_f1=%.4f  best_params=%s", study.best_value, study.best_params
    )
    return model, metrics


def train_lightgbm(
    X: np.ndarray,
    y: np.ndarray,
    n_trials: int = 30,
    n_splits: int = 5,
) -> tuple[Any, dict]:
    """Train LGBMClassifier with Optuna tuning. Returns (model, metrics)."""
    import lightgbm as lgb
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize")
    study.optimize(
        lambda t: _lgb_objective(t, X, y, n_splits),
        n_trials=n_trials,
        show_progress_bar=False,
    )

    best_params = study.best_params | {
        "objective": "multiclass",
        "num_class": 3,
        "verbose": -1,
        "random_state": 42,
    }
    model = lgb.LGBMClassifier(**best_params)
    model.fit(X, y)
    preds = model.predict(X)

    metrics = {
        "backend": "lgb",
        "best_params": study.best_params,
        "best_cv_f1_macro": study.best_value,
        "f1_macro_train": float(f1_score(y, preds, average="macro", zero_division=0)),
        "f1_weighted_train": float(
            f1_score(y, preds, average="weighted", zero_division=0)
        ),
        "n_samples": len(X),
        "n_trials": n_trials,
        "report": classification_report(y, preds, zero_division=0, output_dict=True),
    }
    logger.info(
        "LGB  best_cv_f1=%.4f  best_params=%s", study.best_value, study.best_params
    )
    return model, metrics


# ── Plots ──────────────────────────────────────────────────────────────────────


def plot_feature_importance(
    model: Any,
    feature_names: list[str],
    out_path: Path,
    backend: Backend = "xgb",
    top_n: int = 30,
) -> None:
    """Save a bar chart of top-N feature importances."""
    import matplotlib.pyplot as plt

    if backend == "xgb":
        importances = model.feature_importances_
    else:  # lgb
        importances = model.feature_importances_

    idx = np.argsort(importances)[-top_n:]
    names = [feature_names[i] for i in idx]
    vals = importances[idx]

    fig, ax = plt.subplots(figsize=(10, max(6, top_n * 0.3)))
    ax.barh(names, vals, color="#4e91d0")
    ax.set_xlabel("Feature Importance")
    ax.set_title(f"{backend.upper()} Feature Importance (top {top_n})")
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("✓ Feature importance plot → %s", out_path)


def compute_shap(
    model: Any,
    X: np.ndarray,
    feature_names: list[str],
    out_path: Path,
    max_display: int = 20,
) -> None:
    """Compute SHAP values and save summary plot."""
    import matplotlib.pyplot as plt
    import shap

    explainer = shap.TreeExplainer(model)
    # Use a sample for speed if dataset is large
    sample = X[:2000] if len(X) > 2000 else X
    shap_values = explainer.shap_values(sample)

    # For multi-class: shap_values is list of arrays (one per class)
    # Use class 2 (LONG) for illustration
    sv = shap_values[2] if isinstance(shap_values, list) else shap_values

    fig, ax = plt.subplots(figsize=(10, 8))
    shap.summary_plot(
        sv,
        sample,
        feature_names=feature_names,
        max_display=max_display,
        show=False,
        plot_type="bar",
    )
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("✓ SHAP summary plot → %s", out_path)


# ── Save / Load ────────────────────────────────────────────────────────────────


def save_model(model: Any, metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    metrics_path = path.with_suffix(".metrics.json")
    safe = {k: v for k, v in metrics.items() if k != "report"}
    safe["report"] = metrics.get("report", {})
    metrics_path.write_text(json.dumps(safe, indent=2, default=str))
    logger.info("✓ Saved %s model → %s", metrics.get("backend", ""), path)


def load_model(path: Path) -> Any:
    return joblib.load(path)


# ── File-level runner ──────────────────────────────────────────────────────────


def run_gradient_boost(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label_col: str = "label_10",
    backend: Backend = "xgb",
    n_trials: int = 30,
    n_splits: int = 5,
    force: bool = False,
    plot_shap: bool = True,
) -> dict:
    """
    Load labeled features, run Optuna-tuned XGB or LGB, save model + plots.
    """
    in_dir = LABELS_DIR / symbol / tf
    out_dir = SAVED_DIR / symbol / tf
    out_path = out_dir / f"{backend}_{label_col}.joblib"

    if out_path.exists() and not force:
        logger.info("%s model exists at %s", backend.upper(), out_path)
        return {}

    parquet_files = sorted(in_dir.glob("*.parquet")) if in_dir.exists() else []
    if not parquet_files:
        logger.error("No labeled files for %s %s", symbol, tf)
        return {}

    df = pl.concat([pl.read_parquet(f) for f in parquet_files]).sort("timestamp")
    if label_col not in df.columns:
        logger.error("Label column '%s' not found", label_col)
        return {}

    X, y, feature_cols = prepare_xy(df, label_col)
    logger.info(
        "Dataset: %d samples × %d features  backend=%s",
        len(X),
        len(feature_cols),
        backend,
    )

    if backend == "xgb":
        model, metrics = train_xgboost(X, y, n_trials=n_trials, n_splits=n_splits)
    else:
        model, metrics = train_lightgbm(X, y, n_trials=n_trials, n_splits=n_splits)

    metrics["feature_cols"] = feature_cols
    save_model(model, metrics, out_path)

    # Feature importance plot
    importance_path = out_dir / f"{backend}_{label_col}_importance.png"
    plot_feature_importance(model, feature_cols, importance_path, backend=backend)

    # SHAP plot
    if plot_shap:
        shap_path = out_dir / f"{backend}_{label_col}_shap.png"
        try:
            compute_shap(model, X, feature_cols, shap_path)
        except Exception as e:
            logger.warning("SHAP computation failed: %s", e)

    return metrics


# ── CLI ────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    parser = argparse.ArgumentParser(description="Train XGB/LGB for ML_FX")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--backend", choices=["xgb", "lgb"], default="xgb")
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--splits", type=int, default=5)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-shap", action="store_true")
    args = parser.parse_args()

    result = run_gradient_boost(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        backend=args.backend,
        n_trials=args.trials,
        n_splits=args.splits,
        force=args.force,
        plot_shap=not args.no_shap,
    )
    if result:
        print(f"Best CV F1: {result['best_cv_f1_macro']:.4f}")
        print(f"Train F1 macro: {result['f1_macro_train']:.4f}")
