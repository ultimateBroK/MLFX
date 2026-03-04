"""
models/lstm.py
==============
PyTorch LSTM classifier for XAUUSD direction prediction.

Architecture:
    nn.LSTM(input_size, hidden_size, num_layers)
    → nn.Dropout(dropout)
    → nn.Linear(hidden_size, num_classes=3)

Classes (remapped for cross-entropy):
    0 → SHORT (original -1)
    1 → NEUTRAL (original 0)
    2 → LONG (original +1)

Output: outputs/models/{symbol}/{tf}/lstm_{label_col}.pt
        outputs/models/{symbol}/{tf}/lstm_{label_col}_metrics.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

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


# ── Feature prep ───────────────────────────────────────────────────────────────


def get_feature_columns(df: pl.DataFrame) -> list[str]:
    return [
        c
        for c in df.columns
        if c not in FEATURE_BLACKLIST
        and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int8)
    ]


# ── Sequence windowing ─────────────────────────────────────────────────────────


def create_sequences(
    X: np.ndarray,
    y: np.ndarray,
    seq_len: int = 100,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert flat feature array to overlapping sliding windows.

    Args:
        X:       (N, features) float32 array.
        y:       (N,) int64 label array.
        seq_len: Number of bars per sequence.

    Returns:
        (X_seq, y_seq) where X_seq is (N-seq_len, seq_len, features)
        and y_seq is the label at the END of each window.
    """
    n = len(X)
    if n <= seq_len:
        raise ValueError(f"Need n > seq_len ({n} <= {seq_len})")

    n_seqs = n - seq_len
    X_seq = np.lib.stride_tricks.as_strided(
        X,
        shape=(n_seqs, seq_len, X.shape[1]),
        strides=(X.strides[0], X.strides[0], X.strides[1]),
        writeable=False,
    ).copy()
    y_seq = y[seq_len:]
    return X_seq.astype(np.float32), y_seq.astype(np.int64)


# ── Model definition ───────────────────────────────────────────────────────────


class FXLstm(nn.Module):
    """
    LSTM classifier for multi-class direction prediction.

    Args:
        input_size:  Number of features per timestep.
        hidden_size: LSTM hidden dimension (default 128).
        num_layers:  Stacked LSTM layers (default 2).
        dropout:     Dropout probability between LSTM layers (default 0.3).
        num_classes: Output classes (default 3: SHORT, NEUTRAL, LONG).
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
        num_classes: int = 3,
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
        # x: (batch, seq_len, input_size)
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])  # last timestep
        return self.fc(out)  # (batch, num_classes)


# ── Training loop ──────────────────────────────────────────────────────────────


def train_lstm(
    X: np.ndarray,
    y: np.ndarray,
    seq_len: int = 100,
    hidden_size: int = 128,
    num_layers: int = 2,
    dropout: float = 0.3,
    epochs: int = 30,
    batch_size: int = 64,
    lr: float = 1e-3,
    patience: int = 5,
    val_frac: float = 0.15,
) -> tuple[FXLstm, dict]:
    """
    Train FXLstm with early stopping.

    Args:
        X:           (N, features) float32 feature array (already clean, no NaN).
        y:           (N,) int64 label array, values in {0,1,2}.
        seq_len:     Sliding window length.
        hidden_size: LSTM hidden units.
        num_layers:  Stacked LSTM layers.
        dropout:     Dropout rate.
        epochs:      Max training epochs.
        batch_size:  Mini-batch size.
        lr:          Learning rate (Adam).
        patience:    Early stopping patience (epochs without val loss improvement).
        val_frac:    Fraction of data used as validation (chronological tail).

    Returns:
        (best_model, metrics_dict)
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("LSTM training on device: %s", device)

    X_seq, y_seq = create_sequences(X, y, seq_len=seq_len)
    n = len(X_seq)
    cut = int(n * (1 - val_frac))

    X_tr, X_val = X_seq[:cut], X_seq[cut:]
    y_tr, y_val = y_seq[:cut], y_seq[cut:]

    tr_ds = TensorDataset(torch.tensor(X_tr), torch.tensor(y_tr))
    val_ds = TensorDataset(torch.tensor(X_val), torch.tensor(y_val))
    tr_dl = DataLoader(tr_ds, batch_size=batch_size, shuffle=False)
    val_dl = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    input_size = X.shape[1]
    model = FXLstm(
        input_size=input_size,
        hidden_size=hidden_size,
        num_layers=num_layers,
        dropout=dropout,
        num_classes=3,
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, patience=2, factor=0.5
    )

    best_val_loss = float("inf")
    patience_counter = 0
    best_state: dict = {}
    history: list[dict] = []

    for epoch in range(1, epochs + 1):
        # Train
        model.train()
        train_loss = 0.0
        for xb, yb in tr_dl:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item() * len(xb)
        train_loss /= len(tr_ds)

        # Validate
        model.eval()
        val_loss = 0.0
        correct = 0
        with torch.no_grad():
            for xb, yb in val_dl:
                xb, yb = xb.to(device), yb.to(device)
                logits = model(xb)
                val_loss += criterion(logits, yb).item() * len(xb)
                correct += (logits.argmax(1) == yb).sum().item()
        val_loss /= len(val_ds)
        val_acc = correct / len(val_ds)

        scheduler.step(val_loss)
        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "val_acc": val_acc,
            }
        )
        logger.debug(
            "Epoch %03d/%03d  train_loss=%.4f  val_loss=%.4f  val_acc=%.4f",
            epoch,
            epochs,
            train_loss,
            val_loss,
            val_acc,
        )

        # Early stopping
        if val_loss < best_val_loss - 1e-4:
            best_val_loss = val_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info("Early stopping at epoch %d (patience=%d)", epoch, patience)
                break

    # Restore best
    if best_state:
        model.load_state_dict(best_state)
    model.to("cpu")

    best_rec = min(history, key=lambda r: r["val_loss"])
    metrics = {
        "best_epoch": best_rec["epoch"],
        "best_val_loss": best_rec["val_loss"],
        "best_val_acc": best_rec["val_acc"],
        "seq_len": seq_len,
        "hidden_size": hidden_size,
        "num_layers": num_layers,
        "dropout": dropout,
        "epochs_trained": len(history),
        "n_samples": len(X),
        "n_sequences": n,
        "history": history,
    }
    logger.info(
        "LSTM best_epoch=%d  val_loss=%.4f  val_acc=%.4f",
        best_rec["epoch"],
        best_rec["val_loss"],
        best_rec["val_acc"],
    )
    return model, metrics


# ── Save / Load ────────────────────────────────────────────────────────────────


def save_model(model: FXLstm, metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "metrics": metrics}, path)
    metrics_path = path.with_suffix(".metrics.json")
    # history can be large — keep only last 10 epochs for brevity
    safe = {k: v for k, v in metrics.items() if k != "history"}
    safe["history_tail"] = metrics.get("history", [])[-10:]
    metrics_path.write_text(json.dumps(safe, indent=2, default=str))
    logger.info("✓ LSTM saved → %s", path)


def load_model(path: Path, input_size: int, **model_kwargs: Any) -> FXLstm:
    payload = torch.load(path, map_location="cpu", weights_only=True)
    metrics = payload["metrics"]
    model = FXLstm(
        input_size=input_size,
        hidden_size=metrics.get("hidden_size", 128),
        num_layers=metrics.get("num_layers", 2),
        dropout=metrics.get("dropout", 0.3),
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model


# ── File-level runner ──────────────────────────────────────────────────────────


def run_lstm(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label_col: str = "label_10",
    seq_len: int = 100,
    hidden_size: int = 128,
    num_layers: int = 2,
    epochs: int = 30,
    force: bool = False,
) -> dict:
    """Load labeled features, train LSTM, save model + metrics."""
    in_dir = LABELS_DIR / symbol / tf
    out_dir = SAVED_DIR / symbol / tf
    out_path = out_dir / f"lstm_{label_col}.pt"

    if out_path.exists() and not force:
        logger.info("LSTM model exists at %s", out_path)
        return {}

    parquet_files = sorted(in_dir.glob("*.parquet")) if in_dir.exists() else []
    if not parquet_files:
        logger.error("No labeled files for %s %s", symbol, tf)
        return {}

    df = pl.concat([pl.read_parquet(f) for f in parquet_files]).sort("timestamp")
    if label_col not in df.columns:
        logger.error("Label column '%s' not found", label_col)
        return {}

    feature_cols = [
        c
        for c in df.columns
        if c not in FEATURE_BLACKLIST
        and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int8)
    ]
    # Remap labels: -1 → 0, 0 → 1, 1 → 2
    subset = df.select(feature_cols + [label_col]).drop_nulls()
    X = subset.select(feature_cols).to_numpy().astype(np.float32)
    y = (subset[label_col].to_numpy() + 1).astype(np.int64)

    # Replace NaN/Inf with 0
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    logger.info(
        "Dataset: %d samples × %d features  seq_len=%d",
        len(X),
        len(feature_cols),
        seq_len,
    )

    model, metrics = train_lstm(
        X,
        y,
        seq_len=seq_len,
        hidden_size=hidden_size,
        num_layers=num_layers,
        epochs=epochs,
    )
    metrics["feature_cols"] = feature_cols
    save_model(model, metrics, out_path)
    return metrics


# ── CLI ────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    parser = argparse.ArgumentParser(description="Train LSTM for ML_FX")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--seq-len", type=int, default=100)
    parser.add_argument("--hidden", type=int, default=128)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    result = run_lstm(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        seq_len=args.seq_len,
        hidden_size=args.hidden,
        num_layers=args.layers,
        epochs=args.epochs,
        force=args.force,
    )
    if result:
        print(f"Best epoch: {result['best_epoch']}")
        print(f"Val accuracy: {result['best_val_acc']:.4f}")
