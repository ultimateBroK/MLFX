"""Registry for trainable model backends exposed by the TUI/CLI."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from mlfx.training.backends.base import BackendRunner

if TYPE_CHECKING:
    from mlfx.training.backends.base import TrainingConfig

# Backend key -> (module, symbol)
BACKEND_REGISTRY: dict[str, tuple[str, str]] = {
    "mlf":           ("mlfx.training.backends.mlf",    "run_ml_models"),
    "lstm":          ("mlfx.training.backends.lstm",          "run_lstm"),
    "sgd":           ("mlfx.training.backends.sgd",    "run_online_sgd"),
    "stats":         ("mlfx.training.backends.stats",         "run_stats"),
}

# Backend-specific extra kwargs (callable receives config, returns dict to merge)
def _extra_mlf(c: "TrainingConfig") -> dict[str, Any]:
    return {"n_trials": c.n_trials, "n_splits": c.n_splits}


def _extra_lstm(c: "TrainingConfig") -> dict[str, Any]:
    """Defaults for the PyTorch LSTM backend."""
    return {
        "n_trials": c.n_trials,
        "n_splits": c.n_splits,
        "seq_len": 60,
        "epochs": 30,
        "batch_size": 128,
        "patience": 5,
        "top_k_features": 20,
        "cv_method": c.extra.get("cv_method", "purged_timeseries"),
        "embargo_pct": c.extra.get("embargo_pct", 0.01),
    }


def _extra_sgd(c: "TrainingConfig") -> dict[str, Any]:
    return {"batch_size": 500}


def _extra_stats(c: "TrainingConfig") -> dict[str, Any]:
    return {"n_splits": c.n_splits, "season_length": 24}


BACKEND_EXTRA_KWARGS: dict[str, Any] = {
    "mlf":            _extra_mlf,
    "lstm":           _extra_lstm,
    "sgd":            _extra_sgd,
    "stats":          _extra_stats,
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


# Keys that are used for tracking/logging only and should not be passed to backend runners.
_TRACKING_ONLY_KEYS = frozenset({"profile", "use_mlflow"})


def get_runner_kwargs(config: "TrainingConfig") -> dict[str, Any]:
    """Build kwargs for a backend from config, including backend-specific params.

    Merge order (later wins): base params → backend defaults → user ``extra``.
    This ensures values in ``TrainingConfig.extra`` always override backend defaults.

    Tracking-only keys (e.g., ``profile``) are filtered out before passing to runners.
    """
    base: dict[str, Any] = {
        "symbol": config.symbol,
        "tf": config.tf,
        "label": config.label,
        "force": config.force,
        "seed": config.random_seed,
        "train_start": config.extra.get("train_start"),
        "train_end": config.extra.get("train_end"),
    }
    extra_fn = BACKEND_EXTRA_KWARGS.get(config.backend)
    if extra_fn is not None:
        base.update(extra_fn(config))
    # User-supplied extra always wins over backend defaults, but filter tracking-only keys.
    filtered_extra = {k: v for k, v in config.extra.items() if k not in _TRACKING_ONLY_KEYS}
    base.update(filtered_extra)
    return base
