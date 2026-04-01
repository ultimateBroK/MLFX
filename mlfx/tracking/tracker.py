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

    def log_artifact(self, run_id: str, local_path: Path | str, artifact_path: str | None = None) -> None:
        """Log a local file as an artifact.

        Parameters
        ----------
        run_id
            The run ID to log the artifact under.
        local_path
            Path to the local file to log.
        artifact_path
            Optional subdirectory path within the artifact directory.
        """
        # Default: no-op for backward compatibility
        logger.debug("log_artifact not implemented for this tracker backend")

    def log_artifacts(self, run_id: str, local_dir: Path | str, artifact_path: str | None = None) -> None:
        """Log all files in a directory as artifacts.

        Parameters
        ----------
        run_id
            The run ID to log the artifacts under.
        local_dir
            Path to the local directory containing artifacts.
        artifact_path
            Optional subdirectory path within the artifact directory.
        """
        # Default: no-op for backward compatibility
        logger.debug("log_artifacts not implemented for this tracker backend")

    def log_figure(self, run_id: str, figure: Any, filename: str) -> None:
        """Log a matplotlib/plotly figure as an artifact.

        Parameters
        ----------
        run_id
            The run ID to log the figure under.
        figure
            A matplotlib Figure or plotly Figure object.
        filename
            The filename to save the figure as (e.g., "confusion_matrix.png").
        """
        # Default: no-op for backward compatibility
        logger.debug("log_figure not implemented for this tracker backend")

    def log_dict(self, run_id: str, dictionary: dict[str, Any], artifact_file: str) -> None:
        """Log a dictionary as a JSON artifact.

        Parameters
        ----------
        run_id
            The run ID to log the dictionary under.
        dictionary
            The dictionary to log.
        artifact_file
            The filename for the JSON artifact.
        """
        # Default: no-op for backward compatibility
        logger.debug("log_dict not implemented for this tracker backend")

    def register_model(
        self,
        run_id: str,
        model_path: str,
        model_name: str,
        tags: dict[str, str] | None = None,
    ) -> str | None:
        """Register a model in the model registry.

        Parameters
        ----------
        run_id
            The run ID containing the model artifact.
        model_path
            Path to the model artifact relative to the run's artifact directory.
        model_name
            Name to register the model under in the registry.
        tags
            Optional tags to attach to the registered model.

        Returns
        -------
        str | None
            The model version string, or None if registration failed.
        """
        # Default: no-op for backward compatibility
        logger.debug("register_model not implemented for this tracker backend")
        return None

    def search_runs(
        self,
        experiment_names: list[str] | None = None,
        filter_string: str = "",
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """Search for runs matching the given criteria.

        Parameters
        ----------
        experiment_names
            List of experiment names to search. If None, search all experiments.
        filter_string
            Filter string in MLflow search syntax (e.g., "metrics.f1 > 0.8").
        max_results
            Maximum number of runs to return.

        Returns
        -------
        list[dict[str, Any]]
            List of run dictionaries with metrics, params, and tags.
        """
        # Default: return empty list
        logger.debug("search_runs not implemented for this tracker backend")
        return []

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Get run metadata by run ID.

        Parameters
        ----------
        run_id
            The run ID to retrieve.

        Returns
        -------
        dict[str, Any] | None
            Dictionary containing run metadata, or None if not found.
        """
        # Default: return None
        logger.debug("get_run not implemented for this tracker backend")
        return None

    def get_artifact_uri(self, run_id: str) -> str | None:
        """Get the artifact URI for a run.

        Parameters
        ----------
        run_id
            The run ID to get the artifact URI for.

        Returns
        -------
        str | None
            The artifact URI, or None if not available.
        """
        # Default: return None
        logger.debug("get_artifact_uri not implemented for this tracker backend")
        return None


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
        self._runs_dir = runs_dir or DEFAULT_PATHS.runs_root
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

    def log_artifact(self, run_id: str, local_path: Path | str, artifact_path: str | None = None) -> None:
        """Copy artifact to run's artifact directory."""
        import shutil  # noqa: PLC0415

        local_path = Path(local_path)
        if not local_path.exists():
            logger.warning("FileTracker: artifact path does not exist: %s", local_path)
            return

        run_path = self._path(run_id)
        if not run_path.exists():
            logger.warning("FileTracker: unknown run_id %s", run_id)
            return

        # Create artifacts directory next to run JSON
        artifacts_dir = run_path.parent / f"{run_id}_artifacts"
        if artifact_path:
            artifacts_dir = artifacts_dir / artifact_path
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        dest = artifacts_dir / local_path.name
        shutil.copy2(local_path, dest)
        logger.debug("FileTracker: logged artifact %s -> %s", local_path, dest)

    def log_artifacts(self, run_id: str, local_dir: Path | str, artifact_path: str | None = None) -> None:
        """Copy all files in directory to run's artifact directory."""
        import shutil  # noqa: PLC0415

        local_dir = Path(local_dir)
        if not local_dir.is_dir():
            logger.warning("FileTracker: artifact directory does not exist: %s", local_dir)
            return

        run_path = self._path(run_id)
        if not run_path.exists():
            logger.warning("FileTracker: unknown run_id %s", run_id)
            return

        artifacts_dir = run_path.parent / f"{run_id}_artifacts"
        if artifact_path:
            artifacts_dir = artifacts_dir / artifact_path
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        for item in local_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, artifacts_dir / item.name)
        logger.debug("FileTracker: logged artifacts from %s to %s", local_dir, artifacts_dir)

    def log_dict(self, run_id: str, dictionary: dict[str, Any], artifact_file: str) -> None:
        """Save dictionary as JSON in run's artifact directory."""
        run_path = self._path(run_id)
        if not run_path.exists():
            logger.warning("FileTracker: unknown run_id %s", run_id)
            return

        artifacts_dir = run_path.parent / f"{run_id}_artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        dest = artifacts_dir / artifact_file
        dest.write_text(json.dumps(dictionary, indent=2, default=str))
        logger.debug("FileTracker: logged dict to %s", dest)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Get run metadata by run ID."""
        path = self._path(run_id)
        if not path.exists():
            return None
        return json.loads(path.read_text())  # type: ignore[no-any-return]

    def get_artifact_uri(self, run_id: str) -> str | None:
        """Get the artifact directory path for a run."""
        run_path = self._path(run_id)
        if not run_path.exists():
            return None
        artifacts_dir = run_path.parent / f"{run_id}_artifacts"
        return str(artifacts_dir) if artifacts_dir.exists() else None


# ---------------------------------------------------------------------------
# MLflow tracker (optional dependency)
# ---------------------------------------------------------------------------


class MlflowTracker(BaseTracker):
    """Wraps MLflow when it is installed.

    Parameters
    ----------
    tracking_uri:
        MLflow tracking server URI.  Defaults to SQLite database
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
        self._experiment_name = experiment_name

    def start_run(self, run_name: str, params: dict[str, Any]) -> str:
        active = self._mlflow.start_run(run_name=run_name)
        self._mlflow.log_params({k: str(v) for k, v in params.items()})
        run_id = active.info.run_id
        self._active[run_id] = active
        return run_id

    def log_metrics(self, run_id: str, metrics: dict[str, float]) -> None:
        # Check if there's an active run
        active = self._mlflow.active_run()
        if active and active.info.run_id == run_id:
            # Already in this run's context, log directly
            self._mlflow.log_metrics(metrics)
        elif active:
            # There's an active run but it's different, use nested
            with self._mlflow.start_run(run_id=run_id, nested=True):
                self._mlflow.log_metrics(metrics)
        else:
            # No active run, start normally
            with self._mlflow.start_run(run_id=run_id):
                self._mlflow.log_metrics(metrics)

    def end_run(self, run_id: str, status: str = "FINISHED") -> None:
        self._mlflow.end_run(status=status)
        self._active.pop(run_id, None)

    def log_artifact(self, run_id: str, local_path: Path | str, artifact_path: str | None = None) -> None:
        """Log a local file as an artifact using MLflow."""
        local_path = Path(local_path)
        if not local_path.exists():
            logger.warning("MlflowTracker: artifact path does not exist: %s", local_path)
            return
        # Check if there's an active run
        active = self._mlflow.active_run()
        if active and active.info.run_id == run_id:
            self._mlflow.log_artifact(str(local_path), artifact_path=artifact_path)
        elif active:
            with self._mlflow.start_run(run_id=run_id, nested=True):
                self._mlflow.log_artifact(str(local_path), artifact_path=artifact_path)
        else:
            with self._mlflow.start_run(run_id=run_id):
                self._mlflow.log_artifact(str(local_path), artifact_path=artifact_path)
        logger.debug("MlflowTracker: logged artifact %s", local_path)

    def log_artifacts(self, run_id: str, local_dir: Path | str, artifact_path: str | None = None) -> None:
        """Log all files in a directory as artifacts using MLflow."""
        local_dir = Path(local_dir)
        if not local_dir.is_dir():
            logger.warning("MlflowTracker: artifact directory does not exist: %s", local_dir)
            return
        # Check if there's an active run
        active = self._mlflow.active_run()
        if active and active.info.run_id == run_id:
            self._mlflow.log_artifacts(str(local_dir), artifact_path=artifact_path)
        elif active:
            with self._mlflow.start_run(run_id=run_id, nested=True):
                self._mlflow.log_artifacts(str(local_dir), artifact_path=artifact_path)
        else:
            with self._mlflow.start_run(run_id=run_id):
                self._mlflow.log_artifacts(str(local_dir), artifact_path=artifact_path)
        logger.debug("MlflowTracker: logged artifacts from %s", local_dir)

    def log_figure(self, run_id: str, figure: Any, filename: str) -> None:
        """Log a matplotlib/plotly figure as an artifact using MLflow."""
        # Check if there's an active run
        active = self._mlflow.active_run()
        if active and active.info.run_id == run_id:
            self._mlflow.log_figure(figure, filename)
        elif active:
            with self._mlflow.start_run(run_id=run_id, nested=True):
                self._mlflow.log_figure(figure, filename)
        else:
            with self._mlflow.start_run(run_id=run_id):
                self._mlflow.log_figure(figure, filename)
        logger.debug("MlflowTracker: logged figure %s", filename)

    def log_dict(self, run_id: str, dictionary: dict[str, Any], artifact_file: str) -> None:
        """Log a dictionary as a JSON artifact using MLflow."""
        # Check if there's an active run
        active = self._mlflow.active_run()
        if active and active.info.run_id == run_id:
            self._mlflow.log_dict(dictionary, artifact_file)
        elif active:
            with self._mlflow.start_run(run_id=run_id, nested=True):
                self._mlflow.log_dict(dictionary, artifact_file)
        else:
            with self._mlflow.start_run(run_id=run_id):
                self._mlflow.log_dict(dictionary, artifact_file)
        logger.debug("MlflowTracker: logged dict to %s", artifact_file)

    def register_model(
        self,
        run_id: str,
        model_path: str,
        model_name: str,
        tags: dict[str, str] | None = None,
    ) -> str | None:
        """Register a model in the MLflow Model Registry."""
        try:
            model_uri = f"runs:/{run_id}/{model_path}"
            result = self._mlflow.register_model(
                model_uri,
                model_name,
                tags=tags,
            )
            logger.info("MlflowTracker: registered model %s version %s", model_name, result.version)
            return result.version
        except Exception as exc:  # noqa: BLE001
            logger.warning("MlflowTracker: failed to register model %s: %s", model_name, exc)
            return None

    def search_runs(
        self,
        experiment_names: list[str] | None = None,
        filter_string: str = "",
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """Search for runs matching the given criteria using MLflow."""
        import pandas as pd  # noqa: PLC0415

        if experiment_names is None:
            experiment_names = [self._experiment_name]

        runs_df = self._mlflow.search_runs(
            experiment_names=experiment_names,
            filter_string=filter_string,
            max_results=max_results,
            output_format="pandas",
        )

        if isinstance(runs_df, pd.DataFrame) and not runs_df.empty:
            return runs_df.to_dict(orient="records")  # type: ignore[no-any-return]
        return []

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Get run metadata by run ID from MLflow."""
        try:
            run = self._mlflow.get_run(run_id)
            return {
                "run_id": run.info.run_id,
                "run_name": run.data.tags.get("mlflow.runName", ""),
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "params": run.data.params,
                "metrics": run.data.metrics,
                "tags": run.data.tags,
                "artifact_uri": run.info.artifact_uri,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("MlflowTracker: failed to get run %s: %s", run_id, exc)
            return None

    def get_artifact_uri(self, run_id: str) -> str | None:
        """Get the artifact URI for a run from MLflow."""
        try:
            run = self._mlflow.get_run(run_id)
            return run.info.artifact_uri
        except Exception:  # noqa: BLE001
            return None


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
