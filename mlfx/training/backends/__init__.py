"""Training backend package.

Each backend implementation lives in its own sub-module:

    mlfx.training.backends.mlf    – LightGBM via MLForecast
    mlfx.training.backends.lstm          – PyTorch LSTM
    mlfx.training.backends.sgd    – sklearn SGDClassifier (online)
    mlfx.training.backends.stats         – StatsForecast baseline

The ``base`` sub-module exposes the shared interfaces:
``BackendRunner`` protocol, ``TrainingConfig``, and ``TrainResult``.

Backends are NOT eagerly imported here to avoid pulling in heavy optional
dependencies (torch, optuna, …) at import time.  Use the
registry (``mlfx.training.registry``) for dynamic resolution, or import a
specific backend directly:

    from mlfx.training.backends.mlf import run_ml_models
    from mlfx.training.backends.lstm import run_lstm
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

__all__ = [
    "run_lstm",
    "run_ml_models",
    "run_online_sgd",
    "run_stats",
]

_SYMBOL_MAP: dict[str, tuple[str, str]] = {
    "run_lstm":          ("mlfx.training.backends.lstm",          "run_lstm"),
    "run_ml_models":     ("mlfx.training.backends.mlf",    "run_ml_models"),
    "run_online_sgd":    ("mlfx.training.backends.sgd",    "run_online_sgd"),
    "run_stats":         ("mlfx.training.backends.stats",         "run_stats"),
}


def __getattr__(name: str) -> "Callable[..., Any]":
    if name in _SYMBOL_MAP:
        mod_name, attr = _SYMBOL_MAP[name]
        mod = import_module(mod_name)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
