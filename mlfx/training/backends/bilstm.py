"""
Package-native PyTorch BiLSTM backend for XAUUSD direction prediction.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import numpy as np
import optuna
import torch
import torch.nn as nn

from mlfx.training._utils import set_seed
from mlfx.training.artifacts import save_torch_artifact
from mlfx.training.backends._pytorch_common import run_pytorch_hpo
from mlfx.training.backends._sequence_utils import train_sequence_model_once
from mlfx.training.data import build_model_output_path, prepare_tabular_data

logger = logging.getLogger(__name__)


class FXBiLstm(nn.Module):
    """Bidirectional LSTM for 5-class direction prediction from sequence features."""

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
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size * 2, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])
        return self.fc(out)

def train_bilstm_once(
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
) -> tuple[FXBiLstm, float, list[dict]]:
    """Train BiLSTM for one train/val split. Returns (model, best_val_f1, history)."""
    return train_sequence_model_once(
        FXBiLstm,
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

def _suggest_params(trial: optuna.Trial) -> dict[str, Any]:
    return {
        "hidden_size": trial.suggest_categorical("hidden_size", [32, 64, 128]),
        "num_layers": trial.suggest_int("num_layers", 1, 3),
        "dropout": trial.suggest_float("dropout", 0.1, 0.5),
        "lr": trial.suggest_float("lr", 1e-4, 5e-3, log=True),
    }

def train_bilstm(
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
) -> tuple[FXBiLstm, dict]:
    """Train BiLSTM with Optuna HPO, feature selection, and OOS evaluation. Returns (model, metrics)."""
    return run_pytorch_hpo(
        train_bilstm_once, _suggest_params, X, y, feature_cols,
        model_type="BiLSTM",
        n_trials=n_trials,
        n_splits=n_splits,
        seq_len=seq_len,
        epochs=epochs,
        batch_size=batch_size,
        patience=patience,
        top_k_features=top_k_features,
        seed=seed,
    )

def save_model(model: FXBiLstm, metrics: dict, path: Path) -> None:
    """Persist BiLSTM state_dict and metrics to .pt artifact for serving."""
    save_torch_artifact({"state_dict": model.state_dict(), "metrics": metrics}, metrics, path)
    logger.info("✓ BiLSTM saved → %s", path)

def load_model(path: Path, input_size: int, **model_kwargs: Any) -> FXBiLstm:
    """Load BiLSTM from .pt artifact. Uses best_params from metrics for architecture."""
    payload = torch.load(path, map_location="cpu")
    metrics = payload["metrics"]
    model = FXBiLstm(
        input_size=input_size,
        hidden_size=metrics["best_params"]["hidden_size"],
        num_layers=metrics["best_params"]["num_layers"],
        dropout=metrics["best_params"]["dropout"],
        num_classes=5,
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model

def run_bilstm(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label_col: str = "label_10",
    seq_len: int = 60,
    epochs: int = 30,
    n_trials: int = 10,
    n_splits: int = 5,
    batch_size: int = 128,
    patience: int = 5,
    top_k_features: int = 20,
    force: bool = False,
    seed: int = 42,
    train_start: str | None = None,
    train_end: str | None = None,
    X: np.ndarray | None = None,
    y: np.ndarray | None = None,
    feature_cols: list[str] | None = None,
) -> dict:
    """Train PyTorch BiLSTM with Optuna HPO. Returns metrics dict or {} if skipped."""
    set_seed(seed)
    out_path = build_model_output_path(
        f"bilstm_{label_col}",
        symbol,
        tf,
        label_col,
        suffix=".pt",
    )

    if out_path.exists() and not force:
        logger.info("BiLSTM model exists at %s", out_path)
        return {}

    if X is None or y is None or feature_cols is None:
        prepared = prepare_tabular_data(
            symbol,
            tf,
            label_col,
            train_start=train_start,
            train_end=train_end,
        )
        if prepared is None:
            return {}
        X, y, feature_cols = prepared
    model, metrics = train_bilstm(
        X, y, feature_cols,
        n_trials=n_trials,
        n_splits=n_splits,
        seq_len=seq_len,
        epochs=epochs,
        batch_size=batch_size,
        patience=patience,
        top_k_features=top_k_features,
        seed=seed,
    )
    save_model(model, metrics, out_path)
    metrics["artifact_path"] = str(out_path)
    return metrics


def build_parser() -> argparse.ArgumentParser:
    """Build argparse for standalone BiLSTM training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--seq-len", type=int, default=60)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    """CLI entrypoint for standalone BiLSTM training."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args()
    run_bilstm(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        seq_len=args.seq_len,
        epochs=args.epochs,
        force=args.force,
    )


if __name__ == "__main__":
    main()
