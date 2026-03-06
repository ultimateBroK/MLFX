"""
models/online_sgd.py
====================
Online Learning model for XAUUSD using SGDClassifier.
Supports `partial_fit` to simulate continuous updates over time.

Output: outputs/models/{symbol}/{tf}/online_sgd_{label_col}.pkl
"""

import json
import logging
import pickle
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import f1_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

LABELS_DIR = Path("data/labels")
SAVED_DIR = Path("outputs/models")

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

def get_feature_columns(df: pl.DataFrame) -> list[str]:
    return [
        c for c in df.columns
        if c not in FEATURE_BLACKLIST
        and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int8)
    ]

def train_online_sgd(
    X: np.ndarray,
    y: np.ndarray,
    batch_size: int = 500,
) -> tuple[SGDClassifier, StandardScaler, dict]:
    """
    Simulates an online learning environment by chunking the dataset
    and partially fitting on each chunk, evaluating OOS predicting the next chunk.
    """
    scaler = StandardScaler()
    clf = SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, max_iter=1, tol=None, random_state=42)
    classes = np.array([0, 1, 2, 3, 4])
    
    n_samples = len(X)
    oos_preds = []
    oos_labels = []
    
    # Pre-warm with the first batch
    X_warm = X[:batch_size]
    y_warm = y[:batch_size]
    X_warm_sc = scaler.fit_transform(X_warm)
    clf.partial_fit(X_warm_sc, y_warm, classes=classes)
    
    for start_idx in range(batch_size, n_samples, batch_size):
        end_idx = min(start_idx + batch_size, n_samples)
        X_batch = X[start_idx:end_idx]
        y_batch = y[start_idx:end_idx]
        
        # Predict on new batch (out-of-sample)
        X_batch_sc = scaler.transform(X_batch)
        preds = clf.predict(X_batch_sc)
        oos_preds.extend(preds)
        oos_labels.extend(y_batch)
        
        # Now update the scaler and model with the new batch
        scaler.partial_fit(X_batch)
        X_batch_sc_updated = scaler.transform(X_batch)
        clf.partial_fit(X_batch_sc_updated, y_batch)
        
    f1_macro_oos = float(f1_score(oos_labels, oos_preds, average="macro", zero_division=0))
    
    metrics = {
        "f1_macro_oos": f1_macro_oos,
        "n_samples": n_samples,
        "batch_size": batch_size,
    }
    
    logger.info("Final Online SGD OOS F1: %.4f", f1_macro_oos)
    return clf, scaler, metrics

def save_model(clf: SGDClassifier, scaler: StandardScaler, metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump({"clf": clf, "scaler": scaler}, f)
    metrics_path = path.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2, default=str))
    logger.info("✓ Online SGD saved → %s", path)

def run_online_sgd(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label_col: str = "label_10",
    force: bool = False,
) -> dict:
    in_dir = LABELS_DIR / symbol / tf
    out_dir = SAVED_DIR / symbol / tf
    out_path = out_dir / f"online_sgd_{label_col}.pkl"

    if out_path.exists() and not force:
        logger.info("Online SGD model exists at %s", out_path)
        return {}

    parquet_files = sorted(in_dir.glob("*.parquet")) if in_dir.exists() else []
    if not parquet_files:
        return {}

    df = pl.concat([pl.read_parquet(f) for f in parquet_files]).sort("timestamp")
    if label_col not in df.columns:
        return {}

    feature_cols = get_feature_columns(df)
    subset = df.select(feature_cols + [label_col]).drop_nulls()
    X = subset.select(feature_cols).to_numpy().astype(np.float32)
    y = (subset[label_col].to_numpy() + 2).astype(np.int64)

    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    clf, scaler, metrics = train_online_sgd(X, y)
    save_model(clf, scaler, metrics, out_path)
    return metrics

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    run_online_sgd(symbol=args.symbol, tf=args.tf, label_col=args.label, force=args.force)
