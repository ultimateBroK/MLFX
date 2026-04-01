"""Benchmark command handler."""

from __future__ import annotations

import argparse

from .._workflow_summary import (
    exit_on_stage_error as _exit_on_stage_error,
    persist_cli_workflow as _persist_cli_workflow,
)
from ..workflows import run_benchmark_stage


def handle_benchmark(args: argparse.Namespace) -> None:
    """Handle the benchmark command."""
    stage = run_benchmark_stage(args)
    _persist_cli_workflow("benchmark", [stage], params=vars(args))
    _exit_on_stage_error(stage)
