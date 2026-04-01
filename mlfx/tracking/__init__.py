"""Experiment tracking adapter.

Thin wrapper around MLflow (optional) that falls back to a lightweight
file-based tracker when MLflow is not installed.

Typical usage::

    from mlfx.tracking import get_tracker

    tracker = get_tracker()
    run_id = tracker.start_run("my_run", params={"lr": 0.01})
    tracker.log_metrics(run_id, {"f1": 0.72})
    tracker.end_run(run_id)
"""

from .context import ExperimentContext, experiment_context, workflow_context
from .tracker import BaseTracker, FileTracker, MlflowTracker, get_tracker

__all__ = [
    "BaseTracker",
    "ExperimentContext",
    "FileTracker",
    "MlflowTracker",
    "experiment_context",
    "get_tracker",
    "workflow_context",
]
