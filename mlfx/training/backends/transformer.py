"""
Package-native PyTorch Transformer backend for XAUUSD direction prediction.
"""

from __future__ import annotations

import argparse
import logging
import math
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


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for Transformer sequences."""

    def __init__(self, d_model: int, max_len: int = 5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        if d_model % 2 == 1:
            pe[:, 1::2] = torch.cos(position * div_term[:-1])
        else:
            pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x is (batch, seq_len, d_model)
        seq_len = x.size(1)
        return x + self.pe[:, :seq_len, :]

class FXTransformer(nn.Module):
    """Transformer encoder for 5-class direction prediction from sequence features."""

    def __init__(
        self,
        input_size: int,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        dropout: float = 0.3,
        num_classes: int = 5,
        seq_len: int = 60,
    ) -> None:
        super().__init__()
        self.input_linear = nn.Linear(input_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len=seq_len)

        encoder_layers = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(d_model, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, input_size)
        x = self.input_linear(x)
        x = self.pos_encoder(x)

        # passed into transformer
        out = self.transformer_encoder(x)

        # We can either pool or take the last item
        # Taking the last item in sequence
        out = self.dropout(out[:, -1, :])
        return self.fc(out)

def train_transformer_once(
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    seq_len: int,
    d_model: int,
    nhead: int,
    num_layers: int,
    dim_feedforward: int,
    dropout: float,
    lr: float,
    epochs: int,
    batch_size: int,
    patience: int,
) -> tuple[FXTransformer, float, list[dict]]:
    """Train Transformer for one train/val split. Returns (model, best_val_f1, history)."""
    return train_sequence_model_once(
        FXTransformer,
        X_tr, y_tr, X_val, y_val,
        seq_len=seq_len,
        model_kwargs={
            "d_model": d_model,
            "nhead": nhead,
            "num_layers": num_layers,
            "dim_feedforward": dim_feedforward,
            "dropout": dropout,
            "seq_len": seq_len,
            "num_classes": 5,
        },
        lr=lr,
        epochs=epochs,
        batch_size=batch_size,
        patience=patience,
    )

def _suggest_params(trial: optuna.Trial) -> dict[str, Any] | None:
    d_model = trial.suggest_categorical("d_model", [32, 64, 128])
    nhead = trial.suggest_categorical("nhead", [2, 4, 8])
    if d_model % nhead != 0:
        return None  # run_pytorch_hpo treats None as 0.0
    return {
        "d_model": d_model,
        "nhead": nhead,
        "num_layers": trial.suggest_int("num_layers", 1, 3),
        "dim_feedforward": trial.suggest_categorical("dim_feedforward", [64, 128, 256]),
        "dropout": trial.suggest_float("dropout", 0.1, 0.5),
        "lr": trial.suggest_float("lr", 1e-4, 5e-3, log=True),
    }

def train_transformer(
    X: np.ndarray,
    y: np.ndarray,
    feature_cols: list[str],
    n_trials: int = 10,
    n_splits: int = 5,
    seq_len: int = 60,
    epochs: int = 30,
    batch_size: int = 128,
    patience: int = 5,
    top_k_features: int = 20,
    seed: int = 42,
) -> tuple[FXTransformer, dict]:
    """Train Transformer with Optuna HPO, feature selection, and OOS evaluation. Returns (model, metrics)."""
    return run_pytorch_hpo(
        train_transformer_once, _suggest_params, X, y, feature_cols,
        model_type="Transformer",
        n_trials=n_trials,
        n_splits=n_splits,
        seq_len=seq_len,
        epochs=epochs,
        batch_size=batch_size,
        patience=patience,
        top_k_features=top_k_features,
        seed=seed,
    )

def save_model(model: FXTransformer, metrics: dict, path: Path) -> None:
    """Persist Transformer state_dict and metrics to .pt artifact for serving."""
    save_torch_artifact({"state_dict": model.state_dict(), "metrics": metrics}, metrics, path)
    logger.info("✓ Transformer saved → %s", path)

def load_model(path: Path, input_size: int, **model_kwargs: Any) -> FXTransformer:
    """Load Transformer from .pt artifact. Uses best_params and seq_len from metrics for architecture."""
    payload = torch.load(path, map_location="cpu", weights_only=True)
    metrics = payload["metrics"]
    bp = metrics["best_params"]
    model = FXTransformer(
        input_size=input_size,
        d_model=bp["d_model"],
        nhead=bp["nhead"],
        num_layers=bp["num_layers"],
        dim_feedforward=bp["dim_feedforward"],
        dropout=bp["dropout"],
        seq_len=metrics["seq_len"],
        num_classes=5,
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model

def run_transformer(
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
    """Train PyTorch Transformer with Optuna HPO. Returns metrics dict or {} if skipped."""
    set_seed(seed)
    out_path = build_model_output_path(
        f"transformer_{label_col}",
        symbol,
        tf,
        label_col,
        suffix=".pt",
    )

    if out_path.exists() and not force:
        logger.info("Transformer model exists at %s", out_path)
        return {}

    if X is None or y is None or feature_cols is None:
        prepared = prepare_tabular_data(symbol, tf, label_col)
        if prepared is None:
            return {}
        X, y, feature_cols = prepared
    model, metrics = train_transformer(
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
    """Build argparse for standalone Transformer training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--seq-len", type=int, default=60)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    """CLI entrypoint for standalone Transformer training."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args()
    run_transformer(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        seq_len=args.seq_len,
        epochs=args.epochs,
        force=args.force,
    )


if __name__ == "__main__":
    main()
