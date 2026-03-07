"""Experiment tracker implementations.

Two backends are provided:

* :class:`MlflowTracker` — wraps MLflow when it is installed.
* :class:`FileTracker`   — stores run metadata in ``outputs/runs/`` as JSON
  files; zero external dependencies.

:func:`get_tracker` auto-selects the best available backend.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from mlfx.config.paths import DEFAULT_PATHS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class BaseTracker(ABC):
    """Minimal interface every tracker implementation must satisfy."""

    @abstractmethod
    def start_run(self, run_name: str, params: dict[str, Any]) -> str:
        """Begin a new run; return an opaque run-ID string."""

    @abstractmethod
    def log_metrics(self, run_id: str, metrics: dict[str, float]) -> None:
        """Record numeric metrics for an existing run."""

    @abstractmethod
    def end_run(self, run_id: str, status: str = "FINISHED") -> None:
        """Mark the run as complete."""


# ---------------------------------------------------------------------------
# File-based tracker (no external dependencies)
# ---------------------------------------------------------------------------


class FileTracker(BaseTracker):
    """Stores run metadata as JSON files under ``<runs_dir>/<run_id>.json``.

    Parameters
    ----------
    runs_dir:
        Directory for run JSON files.  Defaults to ``outputs/runs/``.
    """

    def __init__(self, runs_dir: Path | None = None) -> None:
        self._runs_dir = runs_dir or (DEFAULT_PATHS.outputs_root / "runs")
        self._runs_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, run_id: str) -> Path:
        return self._runs_dir / f"{run_id}.json"

    def start_run(self, run_name: str, params: dict[str, Any]) -> str:
        run_id = uuid.uuid4().hex[:12]
        record = {
            "run_id": run_id,
            "run_name": run_name,
            "status": "RUNNING",
            "start_time": time.time(),
            "params": {k: str(v) for k, v in params.items()},
            "metrics": {},
        }
        self._path(run_id).write_text(json.dumps(record, indent=2))
        logger.debug("FileTracker: started run %s (%s)", run_id, run_name)
        return run_id

    def log_metrics(self, run_id: str, metrics: dict[str, float]) -> None:
        path = self._path(run_id)
        if not path.exists():
            logger.warning("FileTracker: unknown run_id %s", run_id)
            return
        record = json.loads(path.read_text())
        record["metrics"].update({k: round(float(v), 6) for k, v in metrics.items()})
        path.write_text(json.dumps(record, indent=2))

    def end_run(self, run_id: str, status: str = "FINISHED") -> None:
        path = self._path(run_id)
        if not path.exists():
            return
        record = json.loads(path.read_text())
        record["status"] = status
        record["end_time"] = time.time()
        path.write_text(json.dumps(record, indent=2))
        logger.debug("FileTracker: ended run %s  status=%s", run_id, status)


# ---------------------------------------------------------------------------
# MLflow tracker (optional dependency)
# ---------------------------------------------------------------------------


class MlflowTracker(BaseTracker):
    """Wraps MLflow when it is installed.

    Parameters
    ----------
    tracking_uri:
        MLflow tracking server URI.  Defaults to the local ``mlruns/``
        directory (MLflow's own default).
    experiment_name:
        MLflow experiment to log runs under.
    """

    def __init__(
        self,
        tracking_uri: str | None = None,
        experiment_name: str = "mlfx",
    ) -> None:
        import mlflow  # noqa: PLC0415

        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        self._mlflow = mlflow
        self._active: dict[str, Any] = {}

    def start_run(self, run_name: str, params: dict[str, Any]) -> str:
        active = self._mlflow.start_run(run_name=run_name)
        self._mlflow.log_params({k: str(v) for k, v in params.items()})
        run_id = active.info.run_id
        self._active[run_id] = active
        return run_id

    def log_metrics(self, run_id: str, metrics: dict[str, float]) -> None:
        with self._mlflow.start_run(run_id=run_id):
            self._mlflow.log_metrics(metrics)

    def end_run(self, run_id: str, status: str = "FINISHED") -> None:
        self._mlflow.end_run(status=status)
        self._active.pop(run_id, None)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_tracker(
    *,
    prefer_mlflow: bool = True,
    tracking_uri: str | None = None,
    experiment_name: str = "mlfx",
    runs_dir: Path | None = None,
) -> BaseTracker:
    """Return the best available tracker.

    Tries MLflow first (if *prefer_mlflow* is True and the package is
    installed); falls back to :class:`FileTracker` otherwise.
    """
    if prefer_mlflow:
        try:
            return MlflowTracker(
                tracking_uri=tracking_uri,
                experiment_name=experiment_name,
            )
        except ImportError:
            logger.debug("MLflow not installed; using FileTracker.")
    return FileTracker(runs_dir=runs_dir)
