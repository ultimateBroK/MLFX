"""Consolidated CLI entrypoint for core MLFX workflows.

This module provides a thin entrypoint that dispatches to individual
command handlers in the handlers/ subpackage.
"""

from __future__ import annotations

import logging

from .handlers import (
    handle_benchmark,
    handle_batch,
    handle_download,
    handle_drift,
    handle_drift_retrain,
    handle_evaluate,
    handle_mlflow,
    handle_models,
    handle_pipeline,
    handle_profiles,
    handle_qa,
    handle_run_all,
    handle_run_profile,
    handle_serve,
    handle_train,
)
from .parser import build_parser


def main() -> None:
    """Parse CLI args and dispatch to the appropriate workflow."""
    try:
        from mlfx.monitoring.logging_config import configure_logging

        configure_logging(level="INFO")
    except Exception:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = build_parser()
    args = parser.parse_args()

    # Set display language
    from mlfx.cli.render import set_language
    set_language(getattr(args, "lang", "en"))

    # Dispatch to appropriate handler
    command_handlers = {
        "download": handle_download,
        "pipeline": handle_pipeline,
        "qa": handle_qa,
        "train": handle_train,
        "evaluate": handle_evaluate,
        "serve": handle_serve,
        "batch-predict": handle_batch,
        "drift": handle_drift,
        "drift-retrain": handle_drift_retrain,
        "models": handle_models,
        "profiles": handle_profiles,
        "run-profile": handle_run_profile,
        "run-all": handle_run_all,
        "benchmark": handle_benchmark,
        "mlflow": handle_mlflow,
    }

    handler = command_handlers.get(args.command)
    if handler:
        handler(args)


# Backward compatibility aliases for external imports
# These are used by tests and external code that may import from main.py
from .resolve import (
    resolve_batch_config,
    resolve_download_config,
    resolve_drift_config,
    resolve_evaluate_config,
    resolve_pipeline_config,
    resolve_qa_config,
    resolve_serve_config,
    resolve_train_config,
)
from .render import (
    print_resolved_train_summary,
    print_resolved_evaluate_summary,
)
from mlfx.workflow.orchestration import (
    run_profile_command,
    run_benchmark,
    run_benchmark_stage,
)

# Aliases for backward compatibility
_resolve_train_command_config = resolve_train_config
_resolve_evaluate_command_config = resolve_evaluate_config
_resolve_download_command_config = resolve_download_config
_resolve_pipeline_command_config = resolve_pipeline_config
_resolve_qa_command_config = resolve_qa_config
_resolve_serve_command_config = resolve_serve_config
_resolve_batch_command_config = resolve_batch_config
_resolve_drift_command_config = resolve_drift_config
_print_resolved_train_summary = print_resolved_train_summary
_print_resolved_evaluate_summary = print_resolved_evaluate_summary
_run_profile_command = run_profile_command
_run_benchmark = run_benchmark
_run_benchmark_stage = run_benchmark_stage
