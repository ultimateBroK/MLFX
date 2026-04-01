"""Argument parser definitions for MLFX CLI.

This package provides modular CLI argument parsers organized by subcommand
grouping. Each module contains parsers for related commands, making maintenance
easier and dependencies clearer.

Example:
    from mlfx.cli.parser import build_parser
    parser = build_parser()
    args = parser.parse_args()
"""

from __future__ import annotations

import argparse

from mlfx.cli.parser.download import add_download_parser
from mlfx.cli.parser.drift import add_drift_parser, add_drift_retrain_parser
from mlfx.cli.parser.mlflow import add_mlflow_parser
from mlfx.cli.parser.models import add_models_parser, add_profiles_parser
from mlfx.cli.parser.pipeline import add_pipeline_parser
from mlfx.cli.parser.qa import add_qa_parser
from mlfx.cli.parser.serve import add_batch_parser, add_serve_parser
from mlfx.cli.parser.train import add_evaluate_parser, add_train_parser
from mlfx.cli.parser.workflow import (
    add_benchmark_parser,
    add_run_all_parser,
    add_run_profile_parser,
)

__all__ = ["build_parser"]


def build_parser() -> argparse.ArgumentParser:
    """Build the consolidated argument parser for MLFX workflows."""
    parser = argparse.ArgumentParser(
        description="MLFX — Machine Learning for Forex. Terminal-first workflow.",
        epilog="Examples:\n"
        "  mlfx download --symbol XAUUSD --start-year 2020\n"
        "  mlfx pipeline --tf 1H\n"
        "  mlfx train --backend lstm --n-trials 20\n"
        "  mlfx train --profile research\n"
        "  mlfx benchmark --backends mlf lstm stats --n-trials 10\n"
        "  mlfx benchmark --profile benchmark_fast\n"
        "  mlfx evaluate --tp 2.0 --sl 1.0\n"
        "  mlfx evaluate --profile research\n"
        "  mlfx profiles\n"
        "  mlfx run-profile --profile research\n"
        "  mlfx run-profile --profile research --skip-benchmark\n"
        "  mlfx run-all --profile research\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--lang",
        choices=["en", "vi"],
        default="en",
        help="Display language for output (default: en)",
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # Data ingestion and quality
    add_download_parser(subparsers)
    add_qa_parser(subparsers)

    # Pipeline and processing
    add_pipeline_parser(subparsers)

    # Training and evaluation
    add_train_parser(subparsers)
    add_evaluate_parser(subparsers)
    add_benchmark_parser(subparsers)

    # Serving and inference
    add_serve_parser(subparsers)
    add_batch_parser(subparsers)

    # Drift detection
    add_drift_parser(subparsers)
    add_drift_retrain_parser(subparsers)

    # Model management
    add_models_parser(subparsers)
    add_profiles_parser(subparsers)

    # Workflow orchestration
    add_run_profile_parser(subparsers)
    add_run_all_parser(subparsers)

    # MLflow integration
    add_mlflow_parser(subparsers)

    return parser
