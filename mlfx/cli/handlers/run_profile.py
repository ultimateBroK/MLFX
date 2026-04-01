"""Run-profile command handler."""

from __future__ import annotations

import argparse

from mlfx.workflow import StageResult

from .._workflow_summary import (
    exit_on_stage_error as _exit_on_stage_error,
    persist_cli_workflow as _persist_cli_workflow,
)
from ..workflows import run_profile_command


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
