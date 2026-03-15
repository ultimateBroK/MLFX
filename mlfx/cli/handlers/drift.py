"""Drift detection command handlers."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

from mlfx.training.backends.base import TrainingConfig
from mlfx.workflow import StageResult
from mlfx.workflow.stages import run_drift, run_drift_then_retrain

from ..render import console
from ..resolve import resolve_drift_config, resolve_train_config

logger = logging.getLogger(__name__)


def _derive_workflow_status(stages: list[StageResult]) -> str:
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
        status=_derive_workflow_status(stages),  # type: ignore[arg-type]
        params=params or {},
    )
    summary_path = persist_workflow_result(result)
    console.print(f"Workflow summary: {summary_path}")


def _exit_on_stage_error(stage: StageResult) -> None:
    if stage.status == "error":
        if stage.error:
            logging.getLogger(__name__).error("%s failed: %s", stage.stage, stage.error)
        sys.exit(1)


def handle_drift(args: argparse.Namespace) -> None:
    """Handle the drift command."""
    drift_cfg = resolve_drift_config(args)
    with console.status("[bold green]Detecting feature drift..."):
        stage = run_drift(**drift_cfg)
    if stage.metrics:
        console.print(stage.metrics)
    _persist_cli_workflow("drift", [stage], params=vars(args))
    _exit_on_stage_error(stage)


def handle_drift_retrain(args: argparse.Namespace) -> None:
    """Handle the drift-retrain command."""
    drift_cfg = resolve_drift_config(args)
    train_cfg = resolve_train_config(args)
    cfg = TrainingConfig(
        symbol=train_cfg["symbol"],
        tf=train_cfg["tf"],
        label=train_cfg["label"],
        backend=train_cfg["backend"],
        n_trials=train_cfg["n_trials"],
        n_splits=train_cfg["n_splits"],
        force=train_cfg["force"],
        extra={
            "train_start": train_cfg["train_start"],
            "train_end": train_cfg["train_end"],
            "profile": args.profile,
        },
    )
    stages = list(run_drift_then_retrain(
        drift_params={
            "symbol": cfg.symbol,
            "tf": cfg.tf,
            "label": cfg.label,
            "threshold_ks": drift_cfg["threshold_ks"],
            "threshold_psi": drift_cfg["threshold_psi"],
            "min_samples": drift_cfg["min_samples"],
        },
        train_config=cfg,
    ))
    if stages:
        console.print({stage.stage: stage.status for stage in stages})
    _persist_cli_workflow("drift-retrain", stages, params=vars(args))
    if any(stage.status == "error" for stage in stages):
        sys.exit(1)
