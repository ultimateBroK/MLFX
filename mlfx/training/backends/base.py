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
    label_col: str = "label_10"
    backend: str = "mlf"
    n_trials: int = 15
    n_splits: int = 5
    force: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def to_runner_kwargs(self) -> dict[str, Any]:
        """Return the kwargs dict accepted by backend ``run_*`` functions."""
        base: dict[str, Any] = {
            "symbol": self.symbol,
            "tf": self.tf,
            "label_col": self.label_col,
            "force": self.force,
        }
        base.update(self.extra)
        # Pass tuning params only to backends that accept them.
        if self.backend in ("mlf",):
            base["n_trials"] = self.n_trials
            base["n_splits"] = self.n_splits
        elif self.backend == "stats":
            base["n_splits"] = self.n_splits
        elif self.backend == "neuralforecast":
            base["n_windows"] = self.n_splits
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
        label_col: str,
        force: bool,
        **kwargs: Any,
    ) -> dict[str, Any]: ...
