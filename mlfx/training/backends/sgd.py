"""
Package-native online SGD backend for XAUUSD direction prediction.
"""

from __future__ import annotations

import argparse
import logging

import numpy as np
import polars as pl
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import f1_score
from sklearn.preprocessing import StandardScaler

from mlfx.training._utils import set_seed
from mlfx.training.artifacts import save_pickle_artifact
from mlfx.training.data import build_model_output_path, prepare_tabular_data

logger = logging.getLogger(__name__)


def train_online_sgd(
    X: np.ndarray,
    y: np.ndarray,
    batch_size: int = 500,
    seed: int = 42,
) -> tuple[SGDClassifier, StandardScaler, dict]:
    """
    Simulate online learning by chunking the dataset and partially fitting
    on each chunk while scoring the next chunk out-of-sample.
    """
    scaler = StandardScaler()
    clf = SGDClassifier(
        loss="log_loss",
        penalty="l2",
        alpha=1e-4,
        max_iter=1,
        tol=None,
        random_state=seed,
    )
    classes = np.array([0, 1, 2, 3, 4])

    n_samples = len(X)
    oos_preds: list[int] = []
    oos_labels: list[int] = []

    X_warm = X[:batch_size]
    y_warm = y[:batch_size]
    X_warm_sc = scaler.fit_transform(X_warm)
    clf.partial_fit(X_warm_sc, y_warm, classes=classes)

    for start_idx in range(batch_size, n_samples, batch_size):
        end_idx = min(start_idx + batch_size, n_samples)
        X_batch = X[start_idx:end_idx]
        y_batch = y[start_idx:end_idx]

        X_batch_sc = scaler.transform(X_batch)
        preds = clf.predict(X_batch_sc)
        oos_preds.extend(preds)
        oos_labels.extend(y_batch)

        scaler.partial_fit(X_batch)
        X_batch_sc_updated = scaler.transform(X_batch)
        clf.partial_fit(X_batch_sc_updated, y_batch)

    f1_macro_oos = float(f1_score(oos_labels, oos_preds, average="macro", zero_division=0))

    metrics = {
        "best_cv_f1_macro": f1_macro_oos,
        "f1_macro_oos": f1_macro_oos,
        "n_samples": n_samples,
        "batch_size": batch_size,
        "model_type": "OnlineSGD",
    }

    logger.info("Final Online SGD OOS F1: %.4f", f1_macro_oos)
    return clf, scaler, metrics


def save_model(clf: SGDClassifier, scaler: StandardScaler, metrics: dict, path) -> None:
    """Persist SGDClassifier and StandardScaler to .pkl artifact for serving."""
    save_pickle_artifact({"clf": clf, "scaler": scaler}, metrics, path)
    logger.info("✓ Online SGD saved → %s", path)


def run_online_sgd(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label: str = "label_10",
    batch_size: int = 500,
    force: bool = False,
    seed: int = 42,
    train_start: str | None = None,
    train_end: str | None = None,
) -> dict:
    """Train online SGDClassifier with chunked partial_fit. Returns metrics dict or {} if skipped."""
    set_seed(seed)
    out_path = build_model_output_path(
        f"online_sgd_{label}",
        symbol,
        tf,
        label,
        suffix=".pkl",
    )

    if out_path.exists() and not force:
        logger.info("Online SGD model exists at %s", out_path)
        return {}

    prepared = prepare_tabular_data(
        symbol,
        tf,
        label,
        train_start=train_start,
        train_end=train_end,
    )
    if prepared is None:
        return {}

    X, y, feature_cols = prepared
    clf, scaler, metrics = train_online_sgd(X, y, batch_size=batch_size, seed=seed)
    metrics["selected_features"] = feature_cols
    save_model(clf, scaler, metrics, out_path)
    metrics["artifact_path"] = str(out_path)
    return metrics


def build_parser() -> argparse.ArgumentParser:
    """Build argparse for standalone online SGD training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    """CLI entrypoint for standalone online SGD training."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args()
    run_online_sgd(symbol=args.symbol, tf=args.tf, label=args.label, force=args.force)


if __name__ == "__main__":
    main()
