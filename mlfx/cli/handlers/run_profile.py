"""Run-profile command handler."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

from mlfx.workflow import StageResult
from mlfx.workflow.results import StageStatus
from mlfx.workflow.orchestration import run_profile_command

from ..render import console

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


def handle_run_profile(args: argparse.Namespace) -> None:
    """Handle the run-profile command."""
    try:
        run_profile_command(args)
        stage = StageResult(
            stage="run-profile",
            status="ok",
            params=vars(args),
        )
    except Exception as exc:  # noqa: BLE001
        stage = StageResult(
            stage="run-profile",
            status="error",
            params=vars(args),
            error=str(exc),
        )
    _persist_cli_workflow("run-profile", [stage], params=vars(args))
    _exit_on_stage_error(stage)
