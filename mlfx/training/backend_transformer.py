"""
Package-native PyTorch Transformer backend for XAUUSD direction prediction.
"""

import logging
import math
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
from torch.utils.data import DataLoader, TensorDataset
from mlfx.training.dataset import build_model_output_path, load_labelled_dataset
from mlfx.training.features import select_numeric_feature_columns
from mlfx.training.persistence import save_torch_artifact

logger = logging.getLogger(__name__)

def get_feature_columns(df: pl.DataFrame) -> list[str]:
    return select_numeric_feature_columns(df)

def create_sequences(
    X: np.ndarray,
    y: np.ndarray,
    seq_len: int = 100,
) -> tuple[np.ndarray, np.ndarray]:
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

class PositionalEncoding(nn.Module):
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
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    X_seq_tr, y_seq_tr = create_sequences(X_tr, y_tr, seq_len=seq_len)
    X_seq_va, y_seq_va = create_sequences(X_val, y_val, seq_len=seq_len)

    tr_ds = TensorDataset(torch.tensor(X_seq_tr), torch.tensor(y_seq_tr))
    val_ds = TensorDataset(torch.tensor(X_seq_va), torch.tensor(y_seq_va))
    tr_dl = DataLoader(tr_ds, batch_size=batch_size, shuffle=False)
    val_dl = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    model = FXTransformer(
        input_size=X_tr.shape[1],
        d_model=d_model,
        nhead=nhead,
        num_layers=num_layers,
        dim_feedforward=dim_feedforward,
        dropout=dropout,
        num_classes=5,
        seq_len=seq_len,
    ).to(device)

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
        preds_list = []
        labels_list = []
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
    d_model = trial.suggest_categorical("d_model", [32, 64, 128])
    nhead = trial.suggest_categorical("nhead", [2, 4, 8])
    if d_model % nhead != 0:
        return 0.0 # prune invalid combos quickly

    num_layers = trial.suggest_int("num_layers", 1, 3)
    dim_feedforward = trial.suggest_categorical("dim_feedforward", [64, 128, 256])
    dropout = trial.suggest_float("dropout", 0.1, 0.5)
    lr = trial.suggest_float("lr", 1e-4, 5e-3, log=True)

    tscv = TimeSeriesSplit(n_splits=n_splits)
    f1_scores = []

    for train_idx, val_idx in tscv.split(X):
        if len(train_idx) <= seq_len or len(val_idx) <= seq_len:
            continue
            
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]
        
        _, val_f1, _ = train_transformer_once(
            X_tr, y_tr, X_val, y_val,
            seq_len=seq_len,
            d_model=d_model,
            nhead=nhead,
            num_layers=num_layers,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            lr=lr,
            epochs=epochs,
            batch_size=batch_size,
            patience=patience,
        )
        f1_scores.append(val_f1)

    return float(np.mean(f1_scores)) if f1_scores else 0.0

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
) -> tuple[FXTransformer, dict]:
    
    logger.info("Applying feature selection (top %d)", top_k_features)
    k = min(top_k_features, X.shape[1])
    selector = SelectKBest(score_func=f_classif, k=k)
    X_selected = selector.fit_transform(X, y)
    selected_mask = selector.get_support()
    selected_features = [f for i, f in enumerate(feature_cols) if selected_mask[i]]

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize")
    
    # We can pre-enqueue known good combos or let it figure it out
    study.optimize(
        lambda t: _objective(t, X_selected, y, seq_len, epochs, batch_size, patience, n_splits),
        n_trials=n_trials,
        show_progress_bar=False,
    )
    
    best_params = study.best_params
    logger.info("Best Transformer params: %s | F1: %.4f", best_params, study.best_value)

    tscv = TimeSeriesSplit(n_splits=n_splits)
    oos_preds = np.full(len(y), -1, dtype=y.dtype)
    oos_labels = np.full(len(y), -1, dtype=y.dtype)
    
    for train_idx, val_idx in tscv.split(X_selected):
        if len(train_idx) <= seq_len or len(val_idx) <= seq_len:
            continue
            
        model_cv, _, _ = train_transformer_once(
            X_selected[train_idx], y[train_idx], 
            X_selected[val_idx], y[val_idx],
            seq_len=seq_len,
            d_model=best_params["d_model"],
            nhead=best_params["nhead"],
            num_layers=best_params["num_layers"],
            dim_feedforward=best_params["dim_feedforward"],
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
    final_model, final_f1, history = train_transformer_once(
        X_selected[:cut], y[:cut],
        X_selected[cut:], y[cut:],
        seq_len=seq_len,
        d_model=best_params["d_model"],
        nhead=best_params["nhead"],
        num_layers=best_params["num_layers"],
        dim_feedforward=best_params["dim_feedforward"],
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
    }
    
    logger.info("Final OOS F1: %.4f", f1_macro_oos)
    return final_model, metrics

def save_model(model: FXTransformer, metrics: dict, path: Path) -> None:
    save_torch_artifact({"state_dict": model.state_dict(), "metrics": metrics}, metrics, path)
    logger.info("✓ Transformer saved → %s", path)

def load_model(path: Path, input_size: int, **model_kwargs: Any) -> FXTransformer:
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
    force: bool = False,
) -> dict:
    out_path = build_model_output_path(f"transformer_{label_col}", symbol, tf, suffix=".pt")

    if out_path.exists() and not force:
        logger.info("Transformer model exists at %s", out_path)
        return {}

    df = load_labelled_dataset(symbol, tf)
    if df is None:
        return {}
    if label_col not in df.columns:
        return {}

    feature_cols = get_feature_columns(df)
    subset = df.select(feature_cols + [label_col]).drop_nulls()
    X = subset.select(feature_cols).to_numpy().astype(np.float32)
    y = (subset[label_col].to_numpy() + 2).astype(np.int64)

    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    model, metrics = train_transformer(
        X, y, feature_cols,
        n_trials=10,
        seq_len=seq_len,
        epochs=epochs,
    )
    save_model(model, metrics, out_path)
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

    run_transformer(symbol=args.symbol, tf=args.tf, label_col=args.label, force=args.force)
