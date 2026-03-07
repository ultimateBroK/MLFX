"""Training backend package.

Each backend implementation lives in its own sub-module:

    mlfx.training.backends.mlforecast    – LightGBM via MLForecast
    mlfx.training.backends.lstm          – PyTorch LSTM
    mlfx.training.backends.bilstm        – PyTorch BiLSTM
    mlfx.training.backends.transformer   – PyTorch Transformer encoder
    mlfx.training.backends.cnn_lstm      – CNN + LSTM hybrid
    mlfx.training.backends.online_sgd    – sklearn SGDClassifier (online)
    mlfx.training.backends.stats         – StatsForecast baseline
    mlfx.training.backends.neuralforecast – NeuralForecast (NHiTS, NBEATS)

The ``base`` sub-module exposes the shared interfaces:
``BackendRunner`` protocol, ``TrainingConfig``, and ``TrainResult``.

Backends are NOT eagerly imported here to avoid pulling in heavy optional
dependencies (torch, optuna, neuralforecast, …) at import time.  Use the
registry (``mlfx.training.registry``) for dynamic resolution, or import a
specific backend directly:

    from mlfx.training.backends.mlforecast import run_ml_models
    from mlfx.training.backends.lstm import run_lstm
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

__all__ = [
    "run_bilstm",
    "run_cnn_lstm",
    "run_lstm",
    "run_ml_models",
    "run_neural_forecast",
    "run_online_sgd",
    "run_stats",
    "run_transformer",
]

_SYMBOL_MAP: dict[str, tuple[str, str]] = {
    "run_bilstm":        ("mlfx.training.backends.bilstm",        "run_bilstm"),
    "run_cnn_lstm":      ("mlfx.training.backends.cnn_lstm",      "run_cnn_lstm"),
    "run_lstm":          ("mlfx.training.backends.lstm",          "run_lstm"),
    "run_ml_models":     ("mlfx.training.backends.mlforecast",    "run_ml_models"),
    "run_neural_forecast":("mlfx.training.backends.neuralforecast","run_neural_forecast"),
    "run_online_sgd":    ("mlfx.training.backends.online_sgd",    "run_online_sgd"),
    "run_stats":         ("mlfx.training.backends.stats",         "run_stats"),
    "run_transformer":   ("mlfx.training.backends.transformer",   "run_transformer"),
}


def __getattr__(name: str) -> "Callable[..., Any]":
    if name in _SYMBOL_MAP:
        mod_name, attr = _SYMBOL_MAP[name]
        mod = import_module(mod_name)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
