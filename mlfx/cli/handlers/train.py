"""Train command handler."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

from mlfx.training.backends.base import TrainingConfig
from mlfx.workflow import StageResult
from mlfx.workflow.results import StageStatus
from mlfx.workflow.stages import run_train

from ..render import console, print_resolved_train_summary
from ..resolve import resolve_train_config

logger = logging.getLogger(__name__)


def _derive_workflow_status(stages: list[StageResult]) -> StageStatus:
    if any(stage.status == "error" for stage in stages):
        return "error"
    if stages and all(stage.status == "skipped" for stage in stages):
        return "skipped"
    return "ok"


def _persist_cli_workflow(
    workflow: str,
    stages: list[StageResult],
    *,
    params: dict[str, Any] | None = None,
) -> None:
    from mlfx.workflow import WorkflowResult, persist_workflow_result
    result = WorkflowResult(
        workflow=workflow,
        stages=stages,
        status=_derive_workflow_status(stages),
        params=params or {},
    )
    summary_path = persist_workflow_result(result)
    console.print(f"Workflow summary: {summary_path}")


def _exit_on_stage_error(stage: StageResult) -> None:
    if stage.status == "error":
        if stage.error:
            logging.getLogger(__name__).error("%s failed: %s", stage.stage, stage.error)
        sys.exit(1)


def handle_train(args: argparse.Namespace) -> None:
    """Handle the train command."""
    train_cfg = resolve_train_config(args)

    print_resolved_train_summary(
        profile=args.profile,
        symbol=train_cfg["symbol"],
        tf=train_cfg["tf"],
        label=train_cfg["label"],
        backend=train_cfg["backend"],
        n_trials=train_cfg["n_trials"],
        n_splits=train_cfg["n_splits"],
        train_start=train_cfg["train_start"],
        train_end=train_cfg["train_end"],
        force=train_cfg["force"],
    )

    # Enable MLflow if flag is set
    use_mlflow = getattr(args, "mlflow", False)
    if use_mlflow:
        from mlfx.config.mlflow import MLflowConfig
        config = MLflowConfig()
        config.setup_mlflow()
        console.print(f"MLflow tracking enabled: {config.tracking_uri}")

    cfg = TrainingConfig(
        symbol=train_cfg["symbol"],
        tf=train_cfg["tf"],
        label=train_cfg["label"],
        backend=train_cfg["backend"],
        n_trials=train_cfg["n_trials"],
        n_splits=train_cfg["n_splits"],
        force=train_cfg["force"],
        extra={
            "cv_method": train_cfg["cv_method"],
            "embargo_pct": train_cfg["embargo_pct"],
            "train_start": train_cfg["train_start"],
            "train_end": train_cfg["train_end"],
            "profile": args.profile,
            "use_mlflow": use_mlflow,
        },
    )
    stage = run_train(cfg)
    _persist_cli_workflow("train", [stage], params=vars(args))
    _exit_on_stage_error(stage)
