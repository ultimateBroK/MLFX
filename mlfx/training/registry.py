"""Registry for trainable model backends exposed by the TUI/CLI."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any


BackendRunner = Callable[..., dict[str, Any]]


BACKEND_REGISTRY: dict[str, tuple[str, str]] = {
    "mlf": ("mlfx.training.backends", "run_ml_models"),
    "lstm": ("mlfx.training.backends", "run_lstm"),
    "transformer": ("mlfx.training.backends", "run_transformer"),
    "cnn_lstm": ("mlfx.training.backends", "run_cnn_lstm"),
    "sgd": ("mlfx.training.backends", "run_online_sgd"),
    "stats": ("mlfx.training.backends", "run_stats"),
    "neuralforecast": ("mlfx.training.backends", "run_neural_forecast"),
}


def get_backend_runner(backend: str) -> BackendRunner:
    """Resolve a backend key into its legacy-compatible runner."""
    if backend not in BACKEND_REGISTRY:
        raise ValueError(
            f"Unknown backend '{backend}'. Choose from: {sorted(BACKEND_REGISTRY)}"
        )

    module_name, symbol_name = BACKEND_REGISTRY[backend]
    module = import_module(module_name)
    runner = getattr(module, symbol_name)
    return runner
