"""Experiment context manager for MLFX training and evaluation workflows.

Provides a convenient context manager for managing MLflow experiments with
automatic setup, logging, and cleanup. Handles experiment naming, parameter
logging, metric tracking, and artifact management.

Usage
-----
>>> from mlfx.tracking.context import experiment_context
>>> with experiment_context(symbol="XAUUSD", tf="1H", label="label_10", backend="mlf") as ctx:
...     # Training code here
...     ctx.log_metrics({"f1": 0.85, "accuracy": 0.92})
...     ctx.log_artifact("model.pkl")
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator

from mlfx.config.mlflow import get_mlflow_config
from mlfx.tracking.tracker import BaseTracker, get_tracker

logger = logging.getLogger(__name__)


@dataclass
class ExperimentContext:
    """Context object for managing experiment state within a context manager.

    Attributes
    ----------
    run_id
        The MLflow run ID for this experiment.
    run_name
        The human-readable run name.
    tracker
        The tracker instance for logging.
    experiment_name
        The full experiment name.
    """

    run_id: str
    run_name: str
    tracker: BaseTracker
    experiment_name: str

    def log_metrics(self, metrics: dict[str, float]) -> None:
        """Log metrics to the current run."""
        self.tracker.log_metrics(self.run_id, metrics)

    def log_params(self, params: dict[str, Any]) -> None:
        """Log additional parameters to the current run."""
        # Note: params are typically logged at run start, so this updates the run
        self.tracker.log_dict(self.run_id, params, "params.json")

    def log_artifact(self, local_path: Path | str, artifact_path: str | None = None) -> None:
        """Log a local file as an artifact."""
        self.tracker.log_artifact(self.run_id, local_path, artifact_path)

    def log_artifacts(self, local_dir: Path | str, artifact_path: str | None = None) -> None:
        """Log all files in a directory as artifacts."""
        self.tracker.log_artifacts(self.run_id, local_dir, artifact_path)

    def log_figure(self, figure: Any, filename: str) -> None:
        """Log a matplotlib/plotly figure as an artifact."""
        self.tracker.log_figure(self.run_id, figure, filename)

    def log_dict(self, dictionary: dict[str, Any], artifact_file: str) -> None:
        """Log a dictionary as a JSON artifact."""
        self.tracker.log_dict(self.run_id, dictionary, artifact_file)

    def register_model(self, model_path: str, model_name: str, tags: dict[str, str] | None = None) -> str | None:
        """Register the model in the model registry."""
        return self.tracker.register_model(self.run_id, model_path, model_name, tags)

    def get_artifact_uri(self) -> str | None:
        """Get the artifact URI for this run."""
        return self.tracker.get_artifact_uri(self.run_id)


@contextmanager
def experiment_context(
    symbol: str,
    tf: str,
    label: str,
    backend: str | None = None,
    *,
    run_name: str | None = None,
    params: dict[str, Any] | None = None,
    tags: dict[str, str] | None = None,
    use_mlflow: bool = True,
    experiment_prefix: str = "mlfx",
) -> Generator[ExperimentContext, None, None]:
    """Context manager for MLFX experiments with automatic logging.

    Sets up the experiment, starts a run, logs parameters, and handles cleanup.
    On exit, the run is automatically ended with appropriate status.

    Parameters
    ----------
    symbol
        Trading symbol (e.g., ``XAUUSD``).
    tf
        Timeframe (e.g., ``1H``).
    label
        Label column name (e.g., ``label_10``).
    backend
        Training backend name (e.g., ``mlf``, ``lstm``).
    run_name
        Optional custom run name. Auto-generated if not provided.
    params
        Parameters to log at run start.
    tags
        Tags to attach to the run.
    use_mlflow
        Whether to use MLflow if available. Falls back to FileTracker if False.
    experiment_prefix
        Prefix for experiment names.

    Yields
    ------
    ExperimentContext
        Context object with run_id and logging methods.

    Examples
    --------
    >>> with experiment_context("XAUUSD", "1H", "label_10", "mlf") as ctx:
    ...     # Training code
    ...     ctx.log_metrics({"train_f1": 0.85, "val_f1": 0.82})
    ...     ctx.log_artifact("model.pkl", "models")
    """
    config = get_mlflow_config()
    experiment_name = config.experiment_name(symbol=symbol, tf=tf, label=label, backend=backend)

    # Generate run name if not provided
    if run_name is None:
        parts = [symbol, tf]
        if backend:
            parts.append(backend)
        parts.append(label)
        run_name = "_".join(parts)

    # Build params dict
    full_params: dict[str, Any] = {
        "symbol": symbol,
        "tf": tf,
        "label": label,
    }
    if backend:
        full_params["backend"] = backend
    if params:
        full_params.update(params)

    # Get tracker
    tracker = get_tracker(
        prefer_mlflow=use_mlflow,
        experiment_name=experiment_name,
    )

    run_id: str | None = None
    status = "FINISHED"

    try:
        # Setup MLflow if using it
        if use_mlflow and config.is_mlflow_available():
            config.setup_mlflow()

        # Start the run
        run_id = tracker.start_run(run_name, full_params)

        # Log tags if provided
        if tags and hasattr(tracker, "log_dict"):
            tracker.log_dict(run_id, tags, "tags.json")

        context = ExperimentContext(
            run_id=run_id,
            run_name=run_name,
            tracker=tracker,
            experiment_name=experiment_name,
        )

        logger.info("Started experiment: %s (run_id=%s)", experiment_name, run_id)
        yield context

    except Exception as exc:
        status = "FAILED"
        logger.error("Experiment %s failed: %s", experiment_name, exc)
        raise

    finally:
        if run_id is not None:
            tracker.end_run(run_id, status=status)
            logger.info("Ended experiment: %s (status=%s)", experiment_name, status)


@contextmanager
def workflow_context(
    workflow_name: str,
    symbol: str | None = None,
    tf: str | None = None,
    label: str | None = None,
    *,
    params: dict[str, Any] | None = None,
    use_mlflow: bool = True,
) -> Generator[ExperimentContext, None, None]:
    """Context manager for workflow-level experiments.

    Similar to :func:`experiment_context` but for orchestrating multi-stage
    workflows (train, evaluate, benchmark).

    Parameters
    ----------
    workflow_name
        Name of the workflow (e.g., ``run_profile``, ``drift_retrain``).
    symbol
        Optional trading symbol.
    tf
        Optional timeframe.
    label
        Optional label column name.
    params
        Parameters to log at run start.
    use_mlflow
        Whether to use MLflow if available.

    Yields
    ------
    ExperimentContext
        Context object with run_id and logging methods.
    """
    config = get_mlflow_config()
    experiment_name = f"{config.experiment_prefix}/workflows/{workflow_name}"

    # Build run name
    run_name_parts = [workflow_name]
    if symbol:
        run_name_parts.append(symbol)
    if tf:
        run_name_parts.append(tf)
    if label:
        run_name_parts.append(label)
    run_name = "_".join(run_name_parts)

    # Build params dict
    full_params: dict[str, Any] = {"workflow": workflow_name}
    if symbol:
        full_params["symbol"] = symbol
    if tf:
        full_params["tf"] = tf
    if label:
        full_params["label"] = label
    if params:
        full_params.update(params)

    tracker = get_tracker(
        prefer_mlflow=use_mlflow,
        experiment_name=experiment_name,
    )

    run_id: str | None = None
    status = "FINISHED"

    try:
        if use_mlflow and config.is_mlflow_available():
            config.setup_mlflow()

        run_id = tracker.start_run(run_name, full_params)

        context = ExperimentContext(
            run_id=run_id,
            run_name=run_name,
            tracker=tracker,
            experiment_name=experiment_name,
        )

        logger.info("Started workflow: %s (run_id=%s)", workflow_name, run_id)
        yield context

    except Exception as exc:
        status = "FAILED"
        logger.error("Workflow %s failed: %s", workflow_name, exc)
        raise

    finally:
        if run_id is not None:
            tracker.end_run(run_id, status=status)
            logger.info("Ended workflow: %s (status=%s)", workflow_name, status)
