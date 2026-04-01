"""Workflow orchestration subcommand parsers for MLFX CLI.

Includes: run-profile, run-all, and benchmark commands.
"""

from __future__ import annotations

import argparse

from mlfx.cli.parser._common import ALL_BACKENDS


def add_run_profile_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add run-profile subcommand parser."""
    run_profile = subparsers.add_parser(
        "run-profile",
        help="Run train then evaluate from one workflow profile",
        description="Resolve one profile and orchestrate train followed by evaluate using that profile's sections.",
    )
    run_profile.add_argument(
        "--profile",
        required=True,
        help="Workflow profile name to execute",
    )
    run_profile.add_argument(
        "--skip-train",
        action="store_true",
        help="Skip the training step and run only evaluation from the profile",
    )
    run_profile.add_argument(
        "--skip-evaluate",
        action="store_true",
        help="Skip the evaluation step and run only training from the profile",
    )
    run_profile.add_argument(
        "--skip-benchmark",
        action="store_true",
        help="Skip the benchmark step even if the profile defines one",
    )
    run_profile.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary of the run-profile orchestration result",
    )
    run_profile.add_argument(
        "--force",
        action="store_true",
        help="Force retraining even if a model already exists",
    )


def add_run_all_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add run-all subcommand parser."""
    run_all = subparsers.add_parser(
        "run-all",
        help="Run the full end-to-end workflow",
        description=(
            "Run workflow sequence: download -> qa -> pipeline -> train -> evaluate -> "
            "benchmark -> serve placeholder -> batch-predict -> drift + retrain"
        ),
    )
    run_all.add_argument(
        "--profile",
        default=None,
        help="Use one workflow profile for train/evaluate/benchmark defaults",
    )
    run_all.add_argument(
        "--symbol", default=None, help="Symbol override (e.g., XAUUSD)"
    )
    run_all.add_argument("--tf", default=None, help="Timeframe override (e.g., 1H, 4H)")
    run_all.add_argument("--label", default=None, help="Label column override")
    run_all.add_argument(
        "--skip-download", action="store_true", help="Skip download stage"
    )
    run_all.add_argument("--skip-qa", action="store_true", help="Skip QA stage")
    run_all.add_argument(
        "--skip-pipeline", action="store_true", help="Skip pipeline stage"
    )
    run_all.add_argument("--skip-train", action="store_true", help="Skip train stage")
    run_all.add_argument(
        "--skip-evaluate", action="store_true", help="Skip evaluate stage"
    )
    run_all.add_argument(
        "--skip-benchmark", action="store_true", help="Skip benchmark stage"
    )
    run_all.add_argument(
        "--skip-serve", action="store_true", help="Skip serve placeholder stage"
    )
    run_all.add_argument(
        "--skip-batch", action="store_true", help="Skip batch prediction stage"
    )
    run_all.add_argument(
        "--skip-drift-retrain",
        action="store_true",
        help="Skip drift detection and retraining stages",
    )
    run_all.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue remaining stages after an error",
    )
    run_all.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary of run-all stage outputs",
    )


def add_benchmark_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add benchmark subcommand parser."""
    benchmark = subparsers.add_parser(
        "benchmark",
        help="Compare multiple backends on same data",
        description="Run multiple backends sequentially and compare metrics in a table.",
    )
    benchmark.add_argument(
        "--symbol", default=None, help="Symbol (default: config.toml)"
    )
    benchmark.add_argument(
        "--tf", default=None, help="Timeframe (default: config.toml)"
    )
    benchmark.add_argument(
        "--label", default=None, help="Label column (default: config.toml)"
    )
    benchmark.add_argument(
        "--backends",
        nargs="+",
        default=None,
        metavar="BACKEND",
        help=f"Backends to run. Default: config.toml. Available: {', '.join(ALL_BACKENDS)}",
    )
    benchmark.add_argument(
        "--n-trials", type=int, default=None, help="Optuna trials per backend"
    )
    benchmark.add_argument("--n-splits", type=int, default=None, help="CV folds")
    benchmark.add_argument(
        "--train-start",
        default=None,
        help="Inclusive training start date in compact format YYYYMMDD, e.g. 20240101",
    )
    benchmark.add_argument(
        "--train-end",
        default=None,
        help="Inclusive training end date in compact format YYYYMMDD, e.g. 20241231",
    )
    benchmark.add_argument(
        "--profile",
        default=None,
        help="Load benchmark defaults from a named profile in config.toml",
    )
    benchmark.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Force retrain all backends",
    )
    benchmark.add_argument(
        "--mlflow",
        action="store_true",
        default=False,
        help="Enable MLflow experiment tracking for benchmark runs",
    )
