"""Short alias module for CLI workflow orchestration helpers.

This keeps concise import paths for personal-project ergonomics while preserving
all existing imports from mlfx.cli.workflows.
"""

from .workflows import run_benchmark, run_benchmark_stage, run_profile_command

__all__ = [
    "run_benchmark",
    "run_benchmark_stage",
    "run_profile_command",
]
