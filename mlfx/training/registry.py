"""Registry for trainable model backends exposed by the TUI/CLI."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any


BackendRunner = Callable[..., dict[str, Any]]


BACKEND_REGISTRY: dict[str, tuple[str, str]] = {
    "mlf":           ("mlfx.training.backends.mlforecast",    "run_ml_models"),
    "lstm":          ("mlfx.training.backends.lstm",          "run_lstm"),
    "bilstm":        ("mlfx.training.backends.bilstm",        "run_bilstm"),
    "transformer":   ("mlfx.training.backends.transformer",   "run_transformer"),
    "cnn_lstm":      ("mlfx.training.backends.cnn_lstm",      "run_cnn_lstm"),
    "sgd":           ("mlfx.training.backends.online_sgd",    "run_online_sgd"),
    "stats":         ("mlfx.training.backends.stats",         "run_stats"),
    "neuralforecast":("mlfx.training.backends.neuralforecast","run_neural_forecast"),
}


def get_backend_runner(backend: str) -> BackendRunner:
    """Resolve a backend key to its runner callable."""
    if backend not in BACKEND_REGISTRY:
        raise ValueError(
            f"Unknown backend '{backend}'. Choose from: {sorted(BACKEND_REGISTRY)}"
        )
    module_name, symbol_name = BACKEND_REGISTRY[backend]
    module = import_module(module_name)
    return getattr(module, symbol_name)
