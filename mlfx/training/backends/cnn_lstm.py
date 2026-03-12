"""
Package-native PyTorch CNN-LSTM backend for XAUUSD direction prediction.
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


class FXCnnLstm(nn.Module):
    """CNN + LSTM hybrid for 5-class direction prediction from sequence features."""

    def __init__(
        self,
        input_size: int,
        cnn_channels: int = 64,
        cnn_kernel: int = 3,
        cnn_pool: int = 2,
        lstm_hidden: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
        num_classes: int = 5,
    ) -> None:
        super().__init__()

        self.conv1d = nn.Conv1d(
            in_channels=input_size,
            out_channels=cnn_channels,
            kernel_size=cnn_kernel,
            padding=cnn_kernel // 2,
        )
        self.relu = nn.ReLU()
        self.maxpool = nn.MaxPool1d(kernel_size=cnn_pool)

        self.lstm = nn.LSTM(
            input_size=cnn_channels,
            hidden_size=lstm_hidden,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(lstm_hidden, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, features)
        x = x.permute(0, 2, 1) # (batch, features, seq_len)

        # CNN
        x = self.conv1d(x)
        x = self.relu(x)
        x = self.maxpool(x)

        # Back to (batch, new_seq_len, channels)
        x = x.permute(0, 2, 1)

        # LSTM
        out, _ = self.lstm(x)

        # Take the last valid step
        out = self.dropout(out[:, -1, :])
        return self.fc(out)

def train_cnnlstm_once(
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    seq_len: int,
    cnn_channels: int,
    cnn_kernel: int,
    cnn_pool: int,
    lstm_hidden: int,
    num_layers: int,
    dropout: float,
    lr: float,
    epochs: int,
    batch_size: int,
    patience: int,
) -> tuple[FXCnnLstm, float, list[dict]]:
    """Train CNN-LSTM for one train/val split. Returns (model, best_val_f1, history)."""
    return train_sequence_model_once(
        FXCnnLstm,
        X_tr, y_tr, X_val, y_val,
        seq_len=seq_len,
        model_kwargs={
            "cnn_channels": cnn_channels,
            "cnn_kernel": cnn_kernel,
            "cnn_pool": cnn_pool,
            "lstm_hidden": lstm_hidden,
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
        "cnn_channels": trial.suggest_categorical("cnn_channels", [32, 64]),
        "cnn_kernel": trial.suggest_categorical("cnn_kernel", [3, 5]),
        "cnn_pool": trial.suggest_categorical("cnn_pool", [2, 3]),
        "lstm_hidden": trial.suggest_categorical("lstm_hidden", [32, 64, 128]),
        "num_layers": trial.suggest_int("num_layers", 1, 2),
        "dropout": trial.suggest_float("dropout", 0.1, 0.5),
        "lr": trial.suggest_float("lr", 1e-4, 5e-3, log=True),
    }

def train_cnnlstm(
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
) -> tuple[FXCnnLstm, dict]:
    """Train CNN-LSTM with Optuna HPO, feature selection, and OOS evaluation. Returns (model, metrics)."""
    return run_pytorch_hpo(
        train_cnnlstm_once, _suggest_params, X, y, feature_cols,
        model_type="CNN_LSTM",
        n_trials=n_trials,
        n_splits=n_splits,
        seq_len=seq_len,
        epochs=epochs,
        batch_size=batch_size,
        patience=patience,
        top_k_features=top_k_features,
        seed=seed,
    )

def save_model(model: FXCnnLstm, metrics: dict, path: Path) -> None:
    """Persist CNN-LSTM state_dict and metrics to .pt artifact for serving."""
    save_torch_artifact({"state_dict": model.state_dict(), "metrics": metrics}, metrics, path)
    logger.info("✓ CNN-LSTM saved → %s", path)

def load_model(path: Path, input_size: int, **model_kwargs: Any) -> FXCnnLstm:
    """Load CNN-LSTM from .pt artifact. Uses best_params from metrics for architecture."""
    payload = torch.load(path, map_location="cpu", weights_only=True)
    metrics = payload["metrics"]
    bp = metrics["best_params"]
    model = FXCnnLstm(
        input_size=input_size,
        cnn_channels=bp["cnn_channels"],
        cnn_kernel=bp["cnn_kernel"],
        cnn_pool=bp["cnn_pool"],
        lstm_hidden=bp["lstm_hidden"],
        num_layers=bp["num_layers"],
        dropout=bp["dropout"],
        num_classes=5,
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model

def run_cnn_lstm(
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
    X: np.ndarray | None = None,
    y: np.ndarray | None = None,
    feature_cols: list[str] | None = None,
) -> dict:
    """Train PyTorch CNN-LSTM with Optuna HPO. Returns metrics dict or {} if skipped."""
    set_seed(seed)
    out_path = build_model_output_path(
        f"cnn_lstm_{label_col}",
        symbol,
        tf,
        label_col,
        suffix=".pt",
    )

    if out_path.exists() and not force:
        logger.info("CNN-LSTM model exists at %s", out_path)
        return {}

    if X is None or y is None or feature_cols is None:
        prepared = prepare_tabular_data(symbol, tf, label_col)
        if prepared is None:
            return {}
        X, y, feature_cols = prepared
    model, metrics = train_cnnlstm(
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
    """Build argparse for standalone CNN-LSTM training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--seq-len", type=int, default=60)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    """CLI entrypoint for standalone CNN-LSTM training."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args()
    run_cnn_lstm(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        seq_len=args.seq_len,
        epochs=args.epochs,
        force=args.force,
    )


if __name__ == "__main__":
    main()
