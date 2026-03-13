"""Shared interface types for all training backends.

Every backend must be callable with a signature compatible with
``BackendRunner`` and should return a ``TrainResult`` dict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, TypedDict


# ---------------------------------------------------------------------------
# Result contract
# ---------------------------------------------------------------------------


class TrainResult(TypedDict, total=False):
    """Standardised dict every backend ``run_*`` function returns."""

    model_type: str
    best_cv_f1_macro: float
    f1_macro_train: float
    f1_macro_oos: float
    best_params: dict[str, Any]
    n_samples: int
    selected_features: list[str]
    artifact_path: str
    run_id: str


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass
class TrainingConfig:
    """Canonical configuration for a single training run.

    All fields mirror the CLI arguments accepted by ``mlfx train``.
    """

    symbol: str = "XAUUSD"
    tf: str = "1H"
    label: str = "label_10"
    backend: str = "mlf"
    n_trials: int = 15
    n_splits: int = 5
    random_seed: int = 42
    force: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def to_runner_kwargs(self) -> dict[str, Any]:
        """Return base kwargs (symbol, tf, label, force, seed) plus extra.

        Backend-specific params (n_trials, n_splits, n_windows) are resolved
        by the registry via :func:`mlfx.training.registry.get_runner_kwargs`.
        """
        base: dict[str, Any] = {
            "symbol": self.symbol,
            "tf": self.tf,
            "label": self.label,
            "force": self.force,
            "seed": self.random_seed,
        }
        base.update(self.extra)
        return base


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class BackendRunner(Protocol):
    """Structural type every backend ``run_*`` entry-point satisfies."""

    def __call__(
        self,
        symbol: str,
        tf: str,
        label: str,
        force: bool,
        **kwargs: Any,
    ) -> dict[str, Any]: ...
