"""Shared sequence creation and training for PyTorch sequence-based backends (LSTM)."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader, TensorDataset

T = TypeVar("T", bound=nn.Module)


def train_sequence_model_once(
    model_factory: Callable[..., T],
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    seq_len: int,
    model_kwargs: dict[str, Any],
    lr: float,
    epochs: int,
    batch_size: int,
    patience: int,
) -> tuple[T, float, list[dict]]:
    """Train a sequence model with early stopping on validation loss.

    Parameters
    ----------
    model_factory : callable
        Factory that takes (input_size, **model_kwargs) and returns an nn.Module.
    X_tr, y_tr, X_val, y_val : np.ndarray
        Train/val feature matrices and label arrays.
    seq_len : int
        Sequence length for sliding windows.
    model_kwargs : dict
        Extra kwargs passed to model_factory (e.g. hidden_size, num_layers, dropout).
    lr, epochs, batch_size, patience : int/float
        Training hyperparameters.

    Returns
    -------
    tuple[model, best_f1_macro, history]
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    X_seq_tr, y_seq_tr = create_sequences(X_tr, y_tr, seq_len=seq_len)
    X_seq_va, y_seq_va = create_sequences(X_val, y_val, seq_len=seq_len)

    tr_ds = TensorDataset(torch.tensor(X_seq_tr), torch.tensor(y_seq_tr))
    val_ds = TensorDataset(torch.tensor(X_seq_va), torch.tensor(y_seq_va))
    tr_dl = DataLoader(tr_ds, batch_size=batch_size, shuffle=False)
    val_dl = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    input_size = int(X_tr.shape[1])
    model = model_factory(input_size=input_size, **model_kwargs).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    best_val_loss = float("inf")
    best_f1_macro = 0.0
    patience_counter = 0
    best_state: dict = {}
    history: list[dict] = []

    for epoch in range(1, epochs + 1):
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

        model.eval()
        val_loss = 0.0
        preds_list: list[np.ndarray] = []
        labels_list: list[np.ndarray] = []
        with torch.no_grad():
            for xb, yb in val_dl:
                xb, yb = xb.to(device), yb.to(device)
                logits = model(xb)
                val_loss += criterion(logits, yb).item() * len(xb)
                preds_list.append(logits.argmax(1).cpu().numpy())
                labels_list.append(yb.cpu().numpy())

        val_loss /= len(val_ds)
        preds_all = np.concatenate(preds_list)
        labels_all = np.concatenate(labels_list)
        val_f1 = f1_score(labels_all, preds_all, average="macro", zero_division=0)

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "val_f1": float(val_f1),
        })

        if val_loss < best_val_loss - 1e-4:
            best_val_loss = val_loss
            best_f1_macro = val_f1
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    if best_state:
        model.load_state_dict(best_state)
    model.to("cpu")

    return model, float(best_f1_macro), history


def create_sequences(
    X: np.ndarray,
    y: np.ndarray,
    seq_len: int = 100,
) -> tuple[np.ndarray, np.ndarray]:
    """Create sliding-window sequences from feature matrix and labels.

    Parameters
    ----------
    X : np.ndarray
        Feature matrix of shape (n_samples, n_features).
    y : np.ndarray
        Label array of shape (n_samples,).
    seq_len : int
        Length of each sequence (number of timesteps).

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        X_seq of shape (n_seqs, seq_len, n_features), y_seq of shape (n_seqs,).
    """
    n = len(X)
    if n <= seq_len:
        raise ValueError(
            f"Dataset too small: {len(X)} rows ≤ seq_len={seq_len}. "
            f"Need >{seq_len} rows after dropping nulls."
        )

    n_seqs = n - seq_len
    X_seq = np.lib.stride_tricks.as_strided(
        X,
        shape=(n_seqs, seq_len, X.shape[1]),
        strides=(X.strides[0], X.strides[0], X.strides[1]),
        writeable=False,
    ).copy()
    y_seq = y[seq_len:]
    return X_seq.astype(np.float32), y_seq.astype(np.int64)
