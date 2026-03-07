"""
Package-native PyTorch CNN-LSTM backend for XAUUSD direction prediction.
"""

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
from sklearn.utils.class_weight import compute_sample_weight
from torch.utils.data import DataLoader, TensorDataset
from mlfx.training.data import build_model_output_path, load_labelled_dataset
from mlfx.training.feature_selection import select_numeric_feature_columns
from mlfx.training.artifacts import save_torch_artifact

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

class FXCnnLstm(nn.Module):
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
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    X_seq_tr, y_seq_tr = create_sequences(X_tr, y_tr, seq_len=seq_len)
    X_seq_va, y_seq_va = create_sequences(X_val, y_val, seq_len=seq_len)

    tr_ds = TensorDataset(torch.tensor(X_seq_tr), torch.tensor(y_seq_tr))
    val_ds = TensorDataset(torch.tensor(X_seq_va), torch.tensor(y_seq_va))
    tr_dl = DataLoader(tr_ds, batch_size=batch_size, shuffle=False)
    val_dl = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    model = FXCnnLstm(
        input_size=X_tr.shape[1],
        cnn_channels=cnn_channels,
        cnn_kernel=cnn_kernel,
        cnn_pool=cnn_pool,
        lstm_hidden=lstm_hidden,
        num_layers=num_layers,
        dropout=dropout,
        num_classes=5,
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
    cnn_channels = trial.suggest_categorical("cnn_channels", [32, 64])
    cnn_kernel = trial.suggest_categorical("cnn_kernel", [3, 5])
    cnn_pool = trial.suggest_categorical("cnn_pool", [2, 3])
    lstm_hidden = trial.suggest_categorical("lstm_hidden", [32, 64, 128])
    num_layers = trial.suggest_int("num_layers", 1, 2)
    dropout = trial.suggest_float("dropout", 0.1, 0.5)
    lr = trial.suggest_float("lr", 1e-4, 5e-3, log=True)

    tscv = TimeSeriesSplit(n_splits=n_splits)
    f1_scores = []

    for train_idx, val_idx in tscv.split(X):
        if len(train_idx) <= seq_len or len(val_idx) <= seq_len:
            continue
            
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]
        
        _, val_f1, _ = train_cnnlstm_once(
            X_tr, y_tr, X_val, y_val,
            seq_len=seq_len,
            cnn_channels=cnn_channels,
            cnn_kernel=cnn_kernel,
            cnn_pool=cnn_pool,
            lstm_hidden=lstm_hidden,
            num_layers=num_layers,
            dropout=dropout,
            lr=lr,
            epochs=epochs,
            batch_size=batch_size,
            patience=patience,
        )
        f1_scores.append(val_f1)

    return float(np.mean(f1_scores)) if f1_scores else 0.0

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
) -> tuple[FXCnnLstm, dict]:
    
    logger.info("Applying feature selection (top %d)", top_k_features)
    k = min(top_k_features, X.shape[1])
    selector = SelectKBest(score_func=f_classif, k=k)
    X_selected = selector.fit_transform(X, y)
    selected_mask = selector.get_support()
    selected_features = [f for i, f in enumerate(feature_cols) if selected_mask[i]]

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize")
    study.optimize(
        lambda t: _objective(t, X_selected, y, seq_len, epochs, batch_size, patience, n_splits),
        n_trials=n_trials,
        show_progress_bar=False,
    )
    
    best_params = study.best_params
    logger.info("Best CNN-LSTM params: %s | F1: %.4f", best_params, study.best_value)

    tscv = TimeSeriesSplit(n_splits=n_splits)
    oos_preds = np.full(len(y), -1, dtype=y.dtype)
    oos_labels = np.full(len(y), -1, dtype=y.dtype)
    
    for train_idx, val_idx in tscv.split(X_selected):
        if len(train_idx) <= seq_len or len(val_idx) <= seq_len:
            continue
            
        model_cv, _, _ = train_cnnlstm_once(
            X_selected[train_idx], y[train_idx], 
            X_selected[val_idx], y[val_idx],
            seq_len=seq_len,
            cnn_channels=best_params["cnn_channels"],
            cnn_kernel=best_params["cnn_kernel"],
            cnn_pool=best_params["cnn_pool"],
            lstm_hidden=best_params["lstm_hidden"],
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
    final_model, final_f1, history = train_cnnlstm_once(
        X_selected[:cut], y[:cut],
        X_selected[cut:], y[cut:],
        seq_len=seq_len,
        cnn_channels=best_params["cnn_channels"],
        cnn_kernel=best_params["cnn_kernel"],
        cnn_pool=best_params["cnn_pool"],
        lstm_hidden=best_params["lstm_hidden"],
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
    }
    
    logger.info("Final OOS F1: %.4f", f1_macro_oos)
    return final_model, metrics

def save_model(model: FXCnnLstm, metrics: dict, path: Path) -> None:
    save_torch_artifact({"state_dict": model.state_dict(), "metrics": metrics}, metrics, path)
    logger.info("✓ CNN-LSTM saved → %s", path)

def load_model(path: Path, input_size: int, **model_kwargs: Any) -> FXCnnLstm:
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
    force: bool = False,
) -> dict:
    out_path = build_model_output_path(f"cnn_lstm_{label_col}", symbol, tf, suffix=".pt")

    if out_path.exists() and not force:
        logger.info("CNN-LSTM model exists at %s", out_path)
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

    model, metrics = train_cnnlstm(
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

    run_cnn_lstm(symbol=args.symbol, tf=args.tf, label_col=args.label, force=args.force)
