"""High-level training orchestrator.

Usage::

    from mlfx.training.runner import run_training
    from mlfx.training.config import TrainingConfig

    cfg = TrainingConfig(symbol="XAUUSD", tf="1H", backend="mlf")
    metrics = run_training(cfg)

The runner:
- Resolves the backend via the registry.
- Logs timing and run metadata.
- Optionally records the run in the experiment tracker (if available).
- Registers the produced artifact in the model registry (if available).
"""

from __future__ import annotations

import logging
import time
from typing import Any

from mlfx.training.backends.base import TrainingConfig
from mlfx.training.registry import get_backend_runner

logger = logging.getLogger(__name__)


def run_training(
    config: TrainingConfig,
    *,
    enable_tracking: bool = True,
    enable_registry: bool = True,
) -> dict[str, Any]:
    """Resolve backend, run training, and optionally track + register results.

    Parameters
    ----------
    config:
        Fully-populated :class:`TrainingConfig` instance.
    enable_tracking:
        When *True* (default), attempt to log the run to the experiment
        tracker.  Silently skipped if the tracker is unavailable.
    enable_registry:
        When *True* (default), register the produced artifact in the model
        registry after a successful run.

    Returns
    -------
    dict
        Raw metrics dict returned by the backend ``run_*`` function.
    """
    logger.info(
        "Starting training run — backend=%s  symbol=%s  tf=%s  label=%s",
        config.backend,
        config.symbol,
        config.tf,
        config.label_col,
    )
    t0 = time.perf_counter()

    runner = get_backend_runner(config.backend)
    kwargs = config.to_runner_kwargs()

    run_id: str | None = None
    if enable_tracking:
        run_id = _start_tracking_run(config)

    try:
        metrics: dict[str, Any] = runner(**kwargs) or {}
    except Exception:
        logger.exception("Backend %s raised an exception.", config.backend)
        if run_id:
            _end_tracking_run(run_id, status="FAILED", metrics={})
        raise

    elapsed = time.perf_counter() - t0
    metrics["elapsed_seconds"] = round(elapsed, 2)

    if run_id:
        _end_tracking_run(run_id, status="FINISHED", metrics=metrics)

    if enable_registry and metrics:
        _register_artifact(config, metrics)

    logger.info(
        "Training complete — backend=%s  elapsed=%.1fs  metrics=%s",
        config.backend,
        elapsed,
        {k: v for k, v in metrics.items() if k not in ("best_params", "history", "history_tail")},
    )
    return metrics


# ---------------------------------------------------------------------------
# Private helpers (gracefully degrade when optional packages are absent)
# ---------------------------------------------------------------------------


def _start_tracking_run(config: TrainingConfig) -> str | None:
    try:
        from mlfx.tracking.tracker import get_tracker

        tracker = get_tracker()
        return tracker.start_run(
            run_name=f"{config.backend}_{config.symbol}_{config.tf}_{config.label_col}",
            params={
                "backend": config.backend,
                "symbol": config.symbol,
                "tf": config.tf,
                "label_col": config.label_col,
                "n_trials": config.n_trials,
                "n_splits": config.n_splits,
                **config.extra,
            },
        )
    except Exception as exc:
        logger.debug("Tracking unavailable: %s", exc)
        return None


def _end_tracking_run(
    run_id: str,
    status: str,
    metrics: dict[str, Any],
) -> None:
    try:
        from mlfx.tracking.tracker import get_tracker

        tracker = get_tracker()
        loggable = {
            k: v
            for k, v in metrics.items()
            if isinstance(v, (int, float)) and k not in ("n_samples",)
        }
        tracker.log_metrics(run_id, loggable)
        tracker.end_run(run_id, status=status)
    except Exception as exc:
        logger.debug("Tracking end-run failed: %s", exc)


def _register_artifact(config: TrainingConfig, metrics: dict[str, Any]) -> None:
    try:
        from mlfx.registry.models import get_registry

        registry = get_registry()
        artifact_path = metrics.get("artifact_path")
        if not artifact_path:
            logger.warning(
                "Backend %s did not return artifact_path; registry entry may be unusable for serving.",
                config.backend,
            )
        registry.register(
            backend=config.backend,
            symbol=config.symbol,
            tf=config.tf,
            label_col=config.label_col,
            metrics=metrics,
            artifact_path=artifact_path,
        )
    except Exception as exc:
        logger.debug("Model registry update failed: %s", exc)
