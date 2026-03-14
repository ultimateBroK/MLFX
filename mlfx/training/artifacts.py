"""Shared persistence helpers for training backends.

Provides functions for saving model artifacts both locally and to MLflow.
Supports hybrid storage where metadata goes to MLflow and binaries stay on disk.
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Any

import torch

logger = logging.getLogger(__name__)


def ensure_parent_dir(path: Path) -> None:
    """Create the parent directory for an artifact path."""
    path.parent.mkdir(parents=True, exist_ok=True)


def write_metrics_json(metrics: dict[str, Any], metrics_path: Path) -> None:
    """Persist metrics as JSON, creating parent directories if needed."""
    ensure_parent_dir(metrics_path)
    metrics_path.write_text(json.dumps(metrics, indent=2, default=str))


def save_pickle_artifact(payload: Any, metrics: dict[str, Any], path: Path) -> None:
    """Save a pickle artifact and its sidecar metrics JSON."""
    ensure_parent_dir(path)
    with open(path, "wb") as file_handle:
        pickle.dump(payload, file_handle)
    write_metrics_json(metrics, path.with_suffix(".metrics.json"))


def save_torch_artifact(
    payload: dict[str, Any],
    metrics: dict[str, Any],
    path: Path,
    *,
    history_key: str = "history",
) -> None:
    """Save a torch payload and a condensed metrics sidecar."""
    ensure_parent_dir(path)
    torch.save(payload, path)
    safe_metrics = {key: value for key, value in metrics.items() if key != history_key}
    if history_key in metrics:
        safe_metrics[f"{history_key}_tail"] = metrics.get(history_key, [])[-5:]
    write_metrics_json(safe_metrics, path.with_suffix(".metrics.json"))


# ---------------------------------------------------------------------------
# MLflow-aware artifact helpers
# ---------------------------------------------------------------------------


def log_artifact_to_mlflow(
    local_path: Path | str,
    artifact_path: str | None = None,
    run_id: str | None = None,
) -> bool:
    """Log an artifact to MLflow if available.

    Parameters
    ----------
    local_path
        Path to the local artifact file.
    artifact_path
        Optional subdirectory within the artifact store.
    run_id
        MLflow run ID. If None, uses active run.

    Returns
    -------
    bool
        True if logged successfully, False otherwise.
    """
    local_path = Path(local_path)
    if not local_path.exists():
        logger.warning("Artifact does not exist: %s", local_path)
        return False

    try:
        import mlflow  # noqa: PLC0415

        if run_id:
            with mlflow.start_run(run_id=run_id):
                mlflow.log_artifact(str(local_path), artifact_path)
        else:
            mlflow.log_artifact(str(local_path), artifact_path)
        logger.debug("Logged artifact to MLflow: %s", local_path)
        return True
    except ImportError:
        logger.debug("MLflow not installed; skipping artifact logging.")
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to log artifact to MLflow: %s", exc)
        return False


def log_metrics_to_mlflow(
    metrics: dict[str, float],
    run_id: str | None = None,
) -> bool:
    """Log metrics to MLflow if available.

    Parameters
    ----------
    metrics
        Dictionary of metric names to values.
    run_id
        MLflow run ID. If None, uses active run.

    Returns
    -------
    bool
        True if logged successfully, False otherwise.
    """
    try:
        import mlflow  # noqa: PLC0415

        if run_id:
            with mlflow.start_run(run_id=run_id):
                mlflow.log_metrics(metrics)
        else:
            mlflow.log_metrics(metrics)
        logger.debug("Logged %d metrics to MLflow", len(metrics))
        return True
    except ImportError:
        logger.debug("MLflow not installed; skipping metrics logging.")
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to log metrics to MLflow: %s", exc)
        return False


def log_params_to_mlflow(
    params: dict[str, Any],
    run_id: str | None = None,
) -> bool:
    """Log parameters to MLflow if available.

    Parameters
    ----------
    params
        Dictionary of parameter names to values.
    run_id
        MLflow run ID. If None, uses active run.

    Returns
    -------
    bool
        True if logged successfully, False otherwise.
    """
    try:
        import mlflow  # noqa: PLC0415

        # Convert all values to strings for MLflow
        str_params = {k: str(v) for k, v in params.items()}

        if run_id:
            with mlflow.start_run(run_id=run_id):
                mlflow.log_params(str_params)
        else:
            mlflow.log_params(str_params)
        logger.debug("Logged %d params to MLflow", len(params))
        return True
    except ImportError:
        logger.debug("MLflow not installed; skipping params logging.")
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to log params to MLflow: %s", exc)
        return False


def save_and_log_artifact(
    payload: Any,
    metrics: dict[str, Any],
    path: Path,
    *,
    artifact_type: str = "pickle",
    run_id: str | None = None,
    mlflow_artifact_path: str | None = None,
) -> Path:
    """Save artifact locally and log to MLflow.

    This implements the hybrid storage strategy:
    - Binary artifact saved to local filesystem
    - Metrics logged to MLflow for querying
    - Artifact path logged to MLflow for lineage

    Parameters
    ----------
    payload
        The model artifact to save.
    metrics
        Metrics dictionary to save and log.
    path
        Local path to save the artifact.
    artifact_type
        Type of artifact: "pickle" or "torch".
    run_id
        MLflow run ID for logging.
    mlflow_artifact_path
        Subdirectory within MLflow artifact store.

    Returns
    -------
    Path
        Path to the saved artifact.
    """
    # Save locally
    if artifact_type == "torch":
        save_torch_artifact(payload, metrics, path)
    else:
        save_pickle_artifact(payload, metrics, path)

    # Log to MLflow
    log_artifact_to_mlflow(path, mlflow_artifact_path, run_id)

    # Log metrics
    numeric_metrics = {
        k: float(v) for k, v in metrics.items()
        if isinstance(v, (int, float))
    }
    if numeric_metrics:
        log_metrics_to_mlflow(numeric_metrics, run_id)

    return path


def register_model_with_mlflow(
    artifact_path: Path | str,
    model_name: str,
    run_id: str | None = None,
    tags: dict[str, str] | None = None,
) -> str | None:
    """Register a model with MLflow Model Registry.

    Parameters
    ----------
    artifact_path
        Path to the model artifact.
    model_name
        Name to register the model under.
    run_id
        MLflow run ID containing the model.
    tags
        Tags to attach to the registered model.

    Returns
    -------
    str | None
        The model version string, or None if registration failed.
    """
    try:
        import mlflow  # noqa: PLC0415

        artifact_path = Path(artifact_path)

        if run_id:
            model_uri = f"runs:/{run_id}/{artifact_path.name}"
        else:
            model_uri = f"file://{artifact_path.parent}"

        result = mlflow.register_model(
            model_uri,
            model_name,
            tags=tags,
        )
        logger.info("Registered model %s version %s", model_name, result.version)
        return result.version

    except ImportError:
        logger.debug("MLflow not installed; skipping model registration.")
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to register model: %s", exc)
        return None
