"""Download command handler."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

from mlfx.workflow import StageResult, WorkflowResult, persist_workflow_result
from mlfx.workflow.stages import run_download

from ..render import console
from ..resolve import resolve_download_config

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


def handle_download(args: argparse.Namespace) -> None:
    """Handle the download command."""
    download_cfg = resolve_download_config(args)
    stage = run_download(**download_cfg)
    _persist_cli_workflow("download", [stage], params=vars(args))
    _exit_on_stage_error(stage)
