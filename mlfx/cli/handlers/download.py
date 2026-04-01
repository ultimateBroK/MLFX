"""Download command handler."""

from __future__ import annotations

import argparse

from mlfx.workflow.stages import run_download

from .._workflow_summary import (
    exit_on_stage_error as _exit_on_stage_error,
    persist_cli_workflow as _persist_cli_workflow,
)
from ..resolve import resolve_download_config


def handle_download(args: argparse.Namespace) -> None:
    """Handle the download command."""
    download_cfg = resolve_download_config(args)
    stage = run_download(**download_cfg)
    _persist_cli_workflow("download", [stage], params=vars(args))
    _exit_on_stage_error(stage)
