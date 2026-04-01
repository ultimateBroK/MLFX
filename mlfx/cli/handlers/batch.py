"""Batch prediction command handler."""

from __future__ import annotations

import argparse

from mlfx.workflow.stages import run_batch

from .._workflow_summary import (
    exit_on_stage_error as _exit_on_stage_error,
    persist_cli_workflow as _persist_cli_workflow,
)
from ..render import console
from ..resolve import resolve_batch_config


def handle_batch(args: argparse.Namespace) -> None:
    """Handle the batch-predict command."""
    batch_cfg = resolve_batch_config(args)
    with console.status("[bold green]Running batch inference..."):
        stage = run_batch(**batch_cfg)
    if stage.metrics:
        console.print(stage.metrics)
    _persist_cli_workflow("batch-predict", [stage], params=vars(args))
    _exit_on_stage_error(stage)
