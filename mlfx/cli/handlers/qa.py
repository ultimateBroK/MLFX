"""QA command handler."""

from __future__ import annotations

import argparse

from mlfx.workflow.stages import run_qa

from .._workflow_summary import (
    exit_on_stage_error as _exit_on_stage_error,
    persist_cli_workflow as _persist_cli_workflow,
)
from ..resolve import resolve_qa_config


def handle_qa(args: argparse.Namespace) -> None:
    """Handle the QA command."""
    qa_cfg = resolve_qa_config(args)
    stage = run_qa(**qa_cfg)
    _persist_cli_workflow("qa", [stage], params=vars(args))
    _exit_on_stage_error(stage)
