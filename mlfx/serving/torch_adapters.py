"""Adapters to rebuild PyTorch sequence models from persisted artifacts for serving."""

from __future__ import annotations

from typing import Any, Type

import numpy as np

NUM_CLASSES = 5

# Training-only hyperparameters that should NOT be passed to model constructors
_TRAINING_ONLY_PARAMS: frozenset[str] = frozenset({
    "lr",           # learning rate
    "learning_rate",
    "epochs",
    "batch_size",
    "patience",     # early stopping patience
    "optimizer",
    "weight_decay",
    "momentum",
    "n_trials",     # optuna trials
    "n_splits",     # cv splits
})


def _rebuild_torch_model(
    model_cls: Type[Any],
    payload: dict[str, Any],
    *,
    extra_from_metrics: list[str] | None = None,
) -> Any:
    """Rebuild a PyTorch model from payload. Uses best_params + optional metrics fields."""
    metrics = payload["metrics"]
    bp = metrics["best_params"]
    input_size = len(metrics.get("selected_features", []))
    
    # Filter out training-only hyperparameters, keep only architecture params
    arch_params = {k: v for k, v in bp.items() if k not in _TRAINING_ONLY_PARAMS}
    
    kwargs: dict[str, Any] = {"input_size": input_size, "num_classes": NUM_CLASSES, **arch_params}
    if extra_from_metrics:
        for key in extra_from_metrics:
            kwargs[key] = metrics.get(key)
    model = model_cls(**kwargs)
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model


def _rebuild_lstm(payload: dict[str, Any]) -> Any:
    from mlfx.training.backends.lstm import FXLstm

    return _rebuild_torch_model(FXLstm, payload)


_MODEL_REBUILDERS: dict[str, Any] = {
    "LSTM": _rebuild_lstm,
}


def rebuild_torch_model(payload: dict[str, Any]) -> Any:
    """Rebuild a PyTorch model from a state_dict + metrics payload."""
    metrics = payload.get("metrics", {})
    model_type = metrics.get("model_type", "")
    if model_type not in _MODEL_REBUILDERS:
        raise ValueError(
            f"Unknown torch model_type '{model_type}'. "
            f"Supported: {list(_MODEL_REBUILDERS)}"
        )
    return _MODEL_REBUILDERS[model_type](payload)


def predict_with_torch_model(
    model: Any,
    X: np.ndarray,
    seq_len: int,
) -> np.ndarray:
    """Run prediction for a sequence model, padding warmup rows with neutral (2)."""
    import torch

    from mlfx.training.backends._sequence_utils import create_sequences

    n = len(X)
    if n <= seq_len:
        return np.full(n, 2, dtype=np.int64)

    y_dummy = np.zeros(n, dtype=np.int64)
    X_seq, _ = create_sequences(X.astype(np.float32), y_dummy, seq_len=seq_len)

    with torch.no_grad():
        X_t = torch.tensor(X_seq)
        logits = model(X_t)
        preds = logits.argmax(dim=1).numpy().astype(np.int64)

    # Predictions correspond to rows [seq_len, seq_len+1, ..., n-1]; pad first seq_len rows.
    out = np.full(n, 2, dtype=np.int64)
    out[seq_len:] = preds
    return out
