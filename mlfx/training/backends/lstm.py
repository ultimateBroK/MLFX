"""
Package-native PyTorch LSTM backend for XAUUSD direction prediction.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import optuna
import polars as pl
import torch
import torch.nn as nn
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import f1_score
from sklearn.model_selection import TimeSeriesSplit
from mlfx.training.artifacts import save_torch_artifact
from mlfx.training.backends._sequence_utils import create_sequences, train_sequence_model_once
from mlfx.training.data import build_model_output_path, prepare_tabular_data
from mlfx.training._utils import set_seed

logger = logging.getLogger(__name__)


class FXLstm(nn.Module):
    """LSTM for 5-class direction prediction from sequence features."""

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
        num_classes: int = 5,
    ) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])
        return self.fc(out)

def train_lstm_once(
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    seq_len: int,
    hidden_size: int,
    num_layers: int,
    dropout: float,
    lr: float,
    epochs: int,
    batch_size: int,
    patience: int,
) -> tuple[FXLstm, float, list[dict]]:
    """Train LSTM for one train/val split. Returns (model, best_val_f1, history)."""
    return train_sequence_model_once(
        FXLstm,
        X_tr, y_tr, X_val, y_val,
        seq_len=seq_len,
        model_kwargs={
            "hidden_size": hidden_size,
            "num_layers": num_layers,
            "dropout": dropout,
            "num_classes": 5,
        },
        lr=lr,
        epochs=epochs,
        batch_size=batch_size,
        patience=patience,
    )

def _objective(
    trial: optuna.Trial,
    X: np.ndarray,
    y: np.ndarray,
    seq_len: int,
    epochs: int,
    batch_size: int,
    patience: int,
    n_splits: int,
) -> float:
    hidden_size = trial.suggest_categorical("hidden_size", [32, 64, 128])
    num_layers = trial.suggest_int("num_layers", 1, 3)
    dropout = trial.suggest_float("dropout", 0.1, 0.5)
    lr = trial.suggest_float("lr", 1e-4, 5e-3, log=True)

    tscv = TimeSeriesSplit(n_splits=n_splits)
    f1_scores = []

    for train_idx, val_idx in tscv.split(X):
        if len(train_idx) <= seq_len or len(val_idx) <= seq_len:
            continue
            
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]
        
        _, val_f1, _ = train_lstm_once(
            X_tr, y_tr, X_val, y_val,
            seq_len=seq_len,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            lr=lr,
            epochs=epochs,
            batch_size=batch_size,
            patience=patience,
        )
        f1_scores.append(val_f1)

    return float(np.mean(f1_scores)) if f1_scores else 0.0

def train_lstm(
    X: np.ndarray,
    y: np.ndarray,
    feature_cols: list[str],
    n_trials: int = 15,
    n_splits: int = 5,
    seq_len: int = 60,
    epochs: int = 30,
    batch_size: int = 128,
    patience: int = 5,
    top_k_features: int = 20,
    seed: int = 42,
) -> tuple[FXLstm, dict]:
    """Train LSTM with Optuna HPO, feature selection, and OOS evaluation. Returns (model, metrics)."""
    logger.info("Applying feature selection (top %d)", top_k_features)
    k = min(top_k_features, X.shape[1])
    selector = SelectKBest(score_func=f_classif, k=k)
    X_selected = selector.fit_transform(X, y)
    selected_mask = selector.get_support()
    selected_features = [f for i, f in enumerate(feature_cols) if selected_mask[i]]

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(
        lambda t: _objective(t, X_selected, y, seq_len, epochs, batch_size, patience, n_splits),
        n_trials=n_trials,
        show_progress_bar=False,
    )
    
    best_params = study.best_params
    logger.info("Best LSTM params: %s | F1: %.4f", best_params, study.best_value)

    tscv = TimeSeriesSplit(n_splits=n_splits)
    oos_preds = np.full(len(y), -1, dtype=y.dtype)
    oos_labels = np.full(len(y), -1, dtype=y.dtype)
    
    for train_idx, val_idx in tscv.split(X_selected):
        if len(train_idx) <= seq_len or len(val_idx) <= seq_len:
            continue
            
        model_cv, _, _ = train_lstm_once(
            X_selected[train_idx], y[train_idx], 
            X_selected[val_idx], y[val_idx],
            seq_len=seq_len,
            hidden_size=best_params["hidden_size"],
            num_layers=best_params["num_layers"],
            dropout=best_params["dropout"],
            lr=best_params["lr"],
            epochs=epochs,
            batch_size=batch_size,
            patience=patience,
        )
        model_cv.eval()
        X_val_seq, y_val_seq = create_sequences(X_selected[val_idx], y[val_idx], seq_len=seq_len)
        with torch.no_grad():
            preds = model_cv(torch.tensor(X_val_seq)).argmax(1).cpu().numpy()
        val_seq_idx = val_idx[seq_len:]
        oos_preds[val_seq_idx] = preds
        oos_labels[val_seq_idx] = y_val_seq

    valid_mask = oos_preds != -1
    f1_macro_oos = float(f1_score(oos_labels[valid_mask], oos_preds[valid_mask], average="macro", zero_division=0))

    cut = int(len(X_selected) * 0.9)
    final_model, final_f1, history = train_lstm_once(
        X_selected[:cut], y[:cut],
        X_selected[cut:], y[cut:],
        seq_len=seq_len,
        hidden_size=best_params["hidden_size"],
        num_layers=best_params["num_layers"],
        dropout=best_params["dropout"],
        lr=best_params["lr"],
        epochs=epochs,
        batch_size=batch_size,
        patience=patience,
    )
    
    metrics = {
        "best_cv_f1_macro": study.best_value,
        "f1_macro_oos": f1_macro_oos,
        "best_params": best_params,
        "selected_features": selected_features,
        "seq_len": seq_len,
        "n_samples": len(X),
        "history": history,
        "model_type": "LSTM",
    }
    
    logger.info("Final OOS F1: %.4f", f1_macro_oos)
    return final_model, metrics

def save_model(model: FXLstm, metrics: dict, path: Path) -> None:
    """Persist LSTM state_dict and metrics to .pt artifact for serving."""
    save_torch_artifact({"state_dict": model.state_dict(), "metrics": metrics}, metrics, path)
    logger.info("✓ LSTM saved → %s", path)

def load_model(path: Path, input_size: int, **model_kwargs: Any) -> FXLstm:
    """Load LSTM from .pt artifact. Uses best_params from metrics for architecture."""
    payload = torch.load(path, map_location="cpu", weights_only=True)
    metrics = payload["metrics"]
    model = FXLstm(
        input_size=input_size,
        hidden_size=metrics["best_params"]["hidden_size"],
        num_layers=metrics["best_params"]["num_layers"],
        dropout=metrics["best_params"]["dropout"],
        num_classes=5,
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model

def run_lstm(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label_col: str = "label_10",
    seq_len: int = 60,
    epochs: int = 30,
    force: bool = False,
    seed: int = 42,
) -> dict:
    """Train PyTorch LSTM with Optuna HPO. Returns metrics dict or {} if skipped."""
    set_seed(seed)
    out_path = build_model_output_path(f"lstm_{label_col}", symbol, tf, suffix=".pt")

    if out_path.exists() and not force:
        logger.info("LSTM model exists at %s", out_path)
        return {}

    prepared = prepare_tabular_data(symbol, tf, label_col)
    if prepared is None:
        return {}

    X, y, feature_cols = prepared
    model, metrics = train_lstm(
        X, y, feature_cols,
        n_trials=10,
        seq_len=seq_len,
        epochs=epochs,
        seed=seed,
    )
    save_model(model, metrics, out_path)
    metrics["artifact_path"] = str(out_path)
    return metrics


def build_parser() -> argparse.ArgumentParser:
    """Build argparse for standalone LSTM training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--seq-len", type=int, default=60)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    """CLI entrypoint for standalone LSTM training."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args()
    run_lstm(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        seq_len=args.seq_len,
        epochs=args.epochs,
        force=args.force,
    )


if __name__ == "__main__":
    main()
