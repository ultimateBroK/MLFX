"""Shared CLI workflow summary helpers."""

from __future__ import annotations

import logging
import sys
from typing import Any

from mlfx.workflow import StageResult, WorkflowResult, persist_workflow_result
from mlfx.workflow.results import StageStatus

from .render import console


def derive_workflow_status(stages: list[StageResult]) -> StageStatus:
    """Collapse stage statuses into one workflow status."""
    if any(stage.status == "error" for stage in stages):
        return "error"
    if stages and all(stage.status == "skipped" for stage in stages):
        return "skipped"
    return "ok"


def persist_cli_workflow(
    workflow: str,
    stages: list[StageResult],
    *,
    params: dict[str, Any] | None = None,
) -> None:
    """Persist one CLI workflow summary and print its path."""
    result = WorkflowResult(
        workflow=workflow,
        stages=stages,
        status=derive_workflow_status(stages),
        params=params or {},
    )
    summary_path = persist_workflow_result(result)
    console.print(f"Workflow summary: {summary_path}")


def exit_on_stage_error(stage: StageResult) -> None:
    """Exit the CLI process when a stage failed."""
    if stage.status == "error":
        if stage.error:
            logging.getLogger(__name__).error("%s failed: %s", stage.stage, stage.error)
        sys.exit(1)


def make_skipped_stage(
    stage: str,
    *,
    reason: str,
    params: dict[str, Any] | None = None,
) -> StageResult:
    """Create a canonical skipped stage result payload."""
    return StageResult(
        stage=stage,
        status="skipped",
        metrics={"reason": reason},
        params=params or {},
    )
