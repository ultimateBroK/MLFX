"""Shared stage/workflow result contracts and persistence helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths

StageStatus = Literal["ok", "error", "skipped"]


@dataclass(slots=True)
class StageResult:
    """Canonical result payload returned by stage entrypoints."""

    stage: str
    status: StageStatus
    metrics: dict[str, Any] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    symbol: str | None = None
    tf: str | None = None
    label: str | None = None
    error: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    ended_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema"] = "mlfx.stage_result.v1"
        return payload


@dataclass(slots=True)
class WorkflowResult:
    """Canonical result payload for multi-stage workflows."""

    workflow: str
    stages: list[StageResult]
    invocation_id: str = field(default_factory=lambda: uuid4().hex[:12])
    status: StageStatus = "ok"
    params: dict[str, Any] = field(default_factory=dict)
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    ended_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "mlfx.workflow_result.v1",
            "workflow": self.workflow,
            "invocation_id": self.invocation_id,
            "status": self.status,
            "params": self.params,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "elapsed_seconds": self.elapsed_seconds,
            "stages": [stage.to_dict() for stage in self.stages],
        }


def persist_workflow_result(
    result: WorkflowResult,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
    log_to_mlflow: bool = True,
) -> Path:
    """Persist one workflow invocation summary under outputs/runs/workflows/.

    Also logs the result to MLflow if available for experiment tracking.

    Parameters
    ----------
    result
        The workflow result to persist.
    paths
        Project paths configuration.
    log_to_mlflow
        Whether to log to MLflow if available.

    Returns
    -------
    Path
        Path to the saved JSON file.
    """

    out_dir = paths.runs_root / "workflows"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{stamp}_{result.workflow}_{result.invocation_id}.json"
    out_path.write_text(json.dumps(result.to_dict(), indent=2, default=str))

    # Log to MLflow if available
    if log_to_mlflow:
        _log_workflow_to_mlflow(result, out_path)

    return out_path


def _log_workflow_run_content(
    mlflow: Any, result: WorkflowResult, json_path: Path
) -> None:
    """Log workflow content to MLflow run."""
    # Log workflow-level params
    mlflow.log_params({
        "workflow": result.workflow,
        "invocation_id": result.invocation_id,
        "status": result.status,
    })

    # Log workflow-level metrics
    mlflow.log_metrics({
        "elapsed_seconds": result.elapsed_seconds,
        "n_stages": len(result.stages),
        "n_successful": sum(1 for s in result.stages if s.status == "ok"),
        "n_failed": sum(1 for s in result.stages if s.status == "error"),
        "n_skipped": sum(1 for s in result.stages if s.status == "skipped"),
    })

    # Log the JSON artifact
    mlflow.log_artifact(str(json_path))

    # Log stage-level metrics
    for stage in result.stages:
        stage_prefix = f"stage.{stage.stage}"

        # Log stage params as tags
        for key, value in stage.params.items():
            mlflow.set_tag(f"{stage_prefix}.{key}", str(value))

        # Log stage metrics
        for key, value in stage.metrics.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(f"{stage_prefix}.{key}", float(value))

        # Log stage artifacts as tags (paths)
        for key, path in stage.artifacts.items():
            mlflow.set_tag(f"{stage_prefix}.artifact.{key}", path)


def _log_workflow_to_mlflow(result: WorkflowResult, json_path: Path) -> None:
    """Log workflow result to MLflow."""
    import logging  # noqa: PLC0415

    logger = logging.getLogger(__name__)

    try:
        import mlflow  # noqa: PLC0415

        from mlfx.config.mlflow import get_mlflow_config

        config = get_mlflow_config()
        if not config.is_mlflow_available():
            return

        config.setup_mlflow()

        # Create experiment for this workflow
        experiment_name = f"{config.experiment_prefix}/workflows/{result.workflow}"
        mlflow.set_experiment(experiment_name)

        # Check if there's already an active run
        active_run = mlflow.active_run()
        if active_run:
            # Use nested run if there's already an active run
            with mlflow.start_run(
                run_name=f"{result.workflow}_{result.invocation_id}",
                tags={"workflow": result.workflow, "invocation_id": result.invocation_id},
                nested=True,
            ):
                _log_workflow_run_content(mlflow, result, json_path)
        else:
            # Start a new run
            with mlflow.start_run(
                run_name=f"{result.workflow}_{result.invocation_id}",
                tags={"workflow": result.workflow, "invocation_id": result.invocation_id},
            ):
                _log_workflow_run_content(mlflow, result, json_path)

        logger.debug("Logged workflow %s to MLflow", result.invocation_id)

    except ImportError:
        logger.debug("MLflow not installed; skipping workflow logging.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to log workflow to MLflow: %s", exc)


def log_stage_result_to_mlflow(stage: StageResult, run_id: str | None = None) -> None:
    """Log a single stage result to MLflow.

    Useful for logging stages as they complete rather than waiting for
    the full workflow to finish.

    Parameters
    ----------
    stage
        The stage result to log.
    run_id
        MLflow run ID to log to. If None, uses active run.
    """
    import logging  # noqa: PLC0415

    logger = logging.getLogger(__name__)

    try:
        import mlflow  # noqa: PLC0415

        stage_prefix = f"stage.{stage.stage}"

        def _log():
            # Log stage status
            mlflow.set_tag(f"{stage_prefix}.status", stage.status)

            # Log stage params as tags
            for key, value in stage.params.items():
                mlflow.set_tag(f"{stage_prefix}.{key}", str(value))

            # Log stage metrics
            for key, value in stage.metrics.items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(f"{stage_prefix}.{key}", float(value))

            # Log timing
            mlflow.log_metric(f"{stage_prefix}.elapsed_seconds", stage.elapsed_seconds)

            # Log artifact paths as tags
            for key, path in stage.artifacts.items():
                mlflow.set_tag(f"{stage_prefix}.artifact.{key}", path)

            # Log error if present
            if stage.error:
                mlflow.set_tag(f"{stage_prefix}.error", stage.error)

        if run_id:
            with mlflow.start_run(run_id=run_id):
                _log()
        else:
            _log()

        logger.debug("Logged stage %s to MLflow", stage.stage)

    except ImportError:
        logger.debug("MLflow not installed; skipping stage logging.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to log stage to MLflow: %s", exc)
