"""
models/knn.py
=============
KNN baseline classifier for XAUUSD direction prediction.

Uses TimeSeriesSplit cross-validation (no data leakage).
Saves model as joblib and metrics as JSON.

Output: outputs/models/{symbol}/{tf}/knn_{label_col}.joblib
        outputs/models/{symbol}/{tf}/knn_{label_col}_metrics.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import polars as pl
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

LABELS_DIR = Path("data/labels")
SAVED_DIR = Path("outputs/models")

# Default feature columns — all numeric, no OHLCV raw prices
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


# ── Utilities ──────────────────────────────────────────────────────────────────


def get_feature_columns(df: pl.DataFrame) -> list[str]:
    """Return numeric columns not in FEATURE_BLACKLIST."""
    return [
        c
        for c in df.columns
        if c not in FEATURE_BLACKLIST
        and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int8)
    ]


def prepare_xy(
    df: pl.DataFrame, label_col: str
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Drop rows where label or any feature is null, return X, y arrays.

    Args:
        df:        DataFrame with features + label column.
        label_col: Target label column name.

    Returns:
        (X, y, feature_names)  — X is float64, y is int64
    """
    feature_cols = get_feature_columns(df)
    subset = df.select(feature_cols + [label_col]).drop_nulls()

    X = subset.select(feature_cols).to_numpy().astype(np.float64)
    y = subset[label_col].to_numpy().astype(np.int64)
    return X, y, feature_cols


# ── Training ───────────────────────────────────────────────────────────────────


def train_knn(
    X: np.ndarray,
    y: np.ndarray,
    n_neighbors: int = 10,
    n_splits: int = 5,
) -> dict[str, Any]:
    """
    Train KNN with TimeSeriesSplit cross-validation.

    Returns:
        Metrics dict: {accuracy, f1_macro, f1_weighted, cv_scores, report}
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scaler = StandardScaler()

    cv_accs: list[float] = []
    cv_f1s: list[float] = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]

        if len(np.unique(y_tr)) < 2:
            logger.debug("Fold %d: only one class in train — skipping", fold)
            continue

        X_tr_sc = scaler.fit_transform(X_tr)
        X_val_sc = scaler.transform(X_val)

        knn = KNeighborsClassifier(
            n_neighbors=n_neighbors,
            weights="distance",
            metric="euclidean",
        )
        knn.fit(X_tr_sc, y_tr)
        preds = knn.predict(X_val_sc)

        acc = float(np.mean(preds == y_val))
        f1 = float(f1_score(y_val, preds, average="macro", zero_division=0))
        cv_accs.append(acc)
        cv_f1s.append(f1)
        logger.debug("Fold %d: acc=%.4f  f1_macro=%.4f", fold, acc, f1)

    # Final model on all data
    X_sc = scaler.fit_transform(X)
    final_model = KNeighborsClassifier(
        n_neighbors=n_neighbors, weights="distance", metric="euclidean"
    )
    final_model.fit(X_sc, y)
    final_preds = final_model.predict(X_sc)
    report = classification_report(y, final_preds, zero_division=0, output_dict=True)

    metrics = {
        "accuracy_cv_mean": float(np.mean(cv_accs)) if cv_accs else 0.0,
        "accuracy_cv_std": float(np.std(cv_accs)) if cv_accs else 0.0,
        "f1_macro_cv_mean": float(np.mean(cv_f1s)) if cv_f1s else 0.0,
        "f1_macro_cv_std": float(np.std(cv_f1s)) if cv_f1s else 0.0,
        "f1_weighted_train": float(
            f1_score(y, final_preds, average="weighted", zero_division=0)
        ),
        "n_neighbors": n_neighbors,
        "n_samples": len(X),
        "report": report,
    }

    logger.info(
        "KNN cv_acc=%.4f±%.4f  cv_f1=%.4f±%.4f  k=%d",
        metrics["accuracy_cv_mean"],
        metrics["accuracy_cv_std"],
        metrics["f1_macro_cv_mean"],
        metrics["f1_macro_cv_std"],
        n_neighbors,
    )

    return metrics, final_model, scaler


# ── Save / Load ────────────────────────────────────────────────────────────────


def save_model(
    model: Any,
    scaler: Any,
    metrics: dict,
    path: Path,
) -> None:
    """Save KNN model (joblib) and metrics (JSON)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "scaler": scaler}, path)
    metrics_path = path.with_suffix(".metrics.json")
    safe_metrics = {k: v for k, v in metrics.items() if k != "report"}
    safe_metrics["report"] = metrics.get("report", {})
    metrics_path.write_text(json.dumps(safe_metrics, indent=2))
    logger.info("✓ Saved model → %s", path)
    logger.info("✓ Saved metrics → %s", metrics_path)


def load_model(path: Path) -> tuple[Any, Any]:
    """Load KNN model and scaler from joblib."""
    payload = joblib.load(path)
    return payload["model"], payload["scaler"]


# ── File-level runner ──────────────────────────────────────────────────────────


def run_knn(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label_col: str = "label_10",
    n_neighbors: int = 10,
    n_splits: int = 5,
    force: bool = False,
) -> dict:
    """
    Load labeled feature Parquet files, train KNN, save model + metrics.

    Returns:
        Metrics dict from train_knn.
    """
    in_dir = LABELS_DIR / symbol / tf
    out_dir = SAVED_DIR / symbol / tf
    out_path = out_dir / f"knn_{label_col}.joblib"

    if out_path.exists() and not force:
        logger.info(
            "KNN model already exists at %s (use force=True to retrain)", out_path
        )
        return {}

    parquet_files = sorted(in_dir.glob("*.parquet")) if in_dir.exists() else []
    if not parquet_files:
        logger.error("No labeled files found for %s %s in %s", symbol, tf, in_dir)
        return {}

    frames = [pl.read_parquet(f) for f in parquet_files]
    df = pl.concat(frames).sort("timestamp")

    if label_col not in df.columns:
        logger.error("Label column '%s' not found in dataset", label_col)
        return {}

    X, y, feature_cols = prepare_xy(df, label_col)
    logger.info("Dataset: %d samples × %d features", len(X), len(feature_cols))

    metrics, model, scaler = train_knn(X, y, n_neighbors=n_neighbors, n_splits=n_splits)
    metrics["feature_cols"] = feature_cols

    save_model(model, scaler, metrics, out_path)
    return metrics


# ── CLI ────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    parser = argparse.ArgumentParser(description="Train KNN baseline for ML_FX")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--splits", type=int, default=5)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    result = run_knn(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        n_neighbors=args.k,
        n_splits=args.splits,
        force=args.force,
    )
    if result:
        print(
            f"CV Accuracy: {result['accuracy_cv_mean']:.4f} ± {result['accuracy_cv_std']:.4f}"
        )
        print(
            f"CV F1 Macro: {result['f1_macro_cv_mean']:.4f} ± {result['f1_macro_cv_std']:.4f}"
        )
