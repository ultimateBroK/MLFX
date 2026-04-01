"""Pipeline command handler."""

from __future__ import annotations

import argparse

from mlfx.workflow.stages import run_pipeline_stage

from .._workflow_summary import (
    exit_on_stage_error as _exit_on_stage_error,
    persist_cli_workflow as _persist_cli_workflow,
)
from ..resolve import resolve_pipeline_config


def handle_pipeline(args: argparse.Namespace) -> None:
    """Handle the pipeline command."""
    pipeline_cfg = resolve_pipeline_config(args)
    stage = run_pipeline_stage(**pipeline_cfg)
    _persist_cli_workflow("pipeline", [stage], params=vars(args))
    _exit_on_stage_error(stage)
