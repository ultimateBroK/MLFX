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
from mlfx.training.registry import get_backend_runner, get_runner_kwargs

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
    kwargs = get_runner_kwargs(config)

    _DL_BACKENDS = frozenset({"lstm", "bilstm", "transformer", "cnn_lstm"})
    if config.backend in _DL_BACKENDS:
        from mlfx.training.data import prepare_tabular_data
        prepared = prepare_tabular_data(config.symbol, config.tf, config.label_col)
        if prepared is not None:
            X, y, feature_cols = prepared
            kwargs.update({"X": X, "y": y, "feature_cols": feature_cols})

    run_id: str | None = None
    if enable_tracking:
        run_id = _start_tracking_run(config)

    try:
        metrics: dict[str, Any] = runner(**kwargs) or {}
    except Exception:
        logger.exception("Backend %s raised an exception.", config.backend)
        if run_id:
            _end_tracking_run(run_id, status="FAILED", metrics={}, config=config)
        raise

    elapsed = time.perf_counter() - t0
    metrics["elapsed_seconds"] = round(elapsed, 2)

    if run_id:
        # Filter metrics for tracking: only numeric types, exclude n_samples
        filtered_metrics = {
            k: v
            for k, v in metrics.items()
            if isinstance(v, (int, float)) and k not in ("n_samples",)
        }
        _end_tracking_run(run_id, status="FINISHED", metrics=filtered_metrics, config=config)

    if enable_registry and metrics:
        _register_artifact(config, metrics)

    summary = {
        k: v
        for k, v in metrics.items()
        if k not in ("best_params", "history", "history_tail", "selected_features")
        and isinstance(v, (int, float, str))
    }
    logger.info(
        "Training complete — backend=%s  elapsed=%.1fs  %s",
        config.backend,
        elapsed,
        summary,
    )
    return metrics


# ---------------------------------------------------------------------------
# Private helpers (gracefully degrade when optional packages are absent)
# ---------------------------------------------------------------------------


def _start_tracking_run(config: TrainingConfig) -> str | None:
    try:
        from mlfx.tracking.tracker import get_tracker
        from mlfx.config.paths import DEFAULT_PATHS

        tracker = get_tracker(runs_dir=DEFAULT_PATHS.runs_dir(config.symbol, config.tf))
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
    config: TrainingConfig,
) -> None:
    """End a tracking run with pre-filtered metrics.
    
    Parameters
    ----------
    run_id:
        The run ID returned by start_run.
    status:
        Run status: "FINISHED" or "FAILED".
    metrics:
        Pre-filtered metrics dict (already contains only loggable types).
    config:
        Training configuration for run context.
    """
    try:
        from mlfx.tracking.tracker import get_tracker
        from mlfx.config.paths import DEFAULT_PATHS

        tracker = get_tracker(runs_dir=DEFAULT_PATHS.runs_dir(config.symbol, config.tf))
        tracker.log_metrics(run_id, metrics)
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
