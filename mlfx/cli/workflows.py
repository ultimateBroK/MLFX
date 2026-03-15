"""Workflow orchestration helpers for the MLFX CLI.

This module re-exports orchestration functions from mlfx.workflow.orchestration
for backward compatibility. New code should import directly from mlfx.workflow.
"""

from __future__ import annotations

# Re-export from the new location for backward compatibility
from mlfx.workflow.orchestration import (
    run_benchmark,
    run_benchmark_stage,
    run_profile_command,
)

__all__ = [
    "run_benchmark",
    "run_benchmark_stage",
    "run_profile_command",
]
