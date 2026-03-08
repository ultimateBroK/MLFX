"""Registry for trainable model backends exposed by the TUI/CLI."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from mlfx.training.backends.base import BackendRunner

if TYPE_CHECKING:
    from mlfx.training.backends.base import TrainingConfig

# Backend key -> (module, symbol)
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

# Backend-specific extra kwargs (callable receives config, returns dict to merge)
def _extra_mlf(c: "TrainingConfig") -> dict[str, Any]:
    return {"n_trials": c.n_trials, "n_splits": c.n_splits}


def _extra_stats(c: "TrainingConfig") -> dict[str, Any]:
    return {"n_splits": c.n_splits}


def _extra_neuralforecast(c: "TrainingConfig") -> dict[str, Any]:
    return {"n_windows": c.n_splits}


BACKEND_EXTRA_KWARGS: dict[str, Any] = {
    "mlf": _extra_mlf,
    "stats": _extra_stats,
    "neuralforecast": _extra_neuralforecast,
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


def get_runner_kwargs(config: "TrainingConfig") -> dict[str, Any]:
    """Build kwargs for a backend from config, including backend-specific params."""
    kwargs = dict(config.to_runner_kwargs())
    extra_fn = BACKEND_EXTRA_KWARGS.get(config.backend)
    if extra_fn is not None:
        kwargs.update(extra_fn(config))
    return kwargs
