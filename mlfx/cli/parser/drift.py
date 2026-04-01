"""Drift detection and retrain subcommand parsers for MLFX CLI."""

from __future__ import annotations

import argparse

from mlfx.cli.parser._common import ALL_BACKENDS


def add_drift_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add drift subcommand parser."""
    drift = subparsers.add_parser(
        "drift",
        help="Detect feature drift",
        description="Compare current features against training reference using KS/PSI tests.",
    )
    drift.add_argument("--symbol", default=None, help="Symbol (default: config.toml)")
    drift.add_argument("--tf", default=None, help="Timeframe (default: config.toml)")
    drift.add_argument(
        "--label", default=None, help="Label column (default: config.toml)"
    )
    drift.add_argument(
        "--threshold-ks",
        type=float,
        default=None,
        help="Kolmogorov-Smirnov threshold (default: config.toml)",
    )
    drift.add_argument(
        "--threshold-psi",
        type=float,
        default=None,
        help="Population Stability Index threshold (default: config.toml)",
    )
    drift.add_argument(
        "--min-samples",
        type=int,
        default=None,
        help="Minimum live samples per feature for drift tests (default: config.toml)",
    )


def add_drift_retrain_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add drift-retrain subcommand parser."""
    drift_retrain = subparsers.add_parser(
        "drift-retrain",
        help="Run drift detection and retrain if drift is found",
        description="Detect drift first; if drifted features exist, retrain the selected backend.",
    )
    drift_retrain.add_argument("--symbol", default=None, help="Symbol")
    drift_retrain.add_argument("--tf", default=None, help="Timeframe")
    drift_retrain.add_argument("--label", default=None, help="Label column")
    drift_retrain.add_argument(
        "--backend",
        default=None,
        choices=ALL_BACKENDS,
        metavar="BACKEND",
        help=f"Model backend. Options: {', '.join(ALL_BACKENDS)}",
    )
    drift_retrain.add_argument(
        "--n-trials", type=int, default=None, help="Optuna trials for HPO"
    )
    drift_retrain.add_argument(
        "--n-splits", type=int, default=None, help="TimeSeriesSplit folds"
    )
    drift_retrain.add_argument(
        "--cv-method",
        choices=["purged_kfold", "purged_timeseries", "walk_forward", "timeseries"],
        default=None,
        help="Cross-validation method (default: config.toml)",
    )
    drift_retrain.add_argument(
        "--embargo-pct",
        type=float,
        default=None,
        help="Embargo percentage for purged CV methods (default: config.toml)",
    )
    drift_retrain.add_argument(
        "--train-start",
        default=None,
        help="Inclusive training start date in compact format YYYYMMDD, e.g. 20240101",
    )
    drift_retrain.add_argument(
        "--train-end",
        default=None,
        help="Inclusive training end date in compact format YYYYMMDD, e.g. 20241231",
    )
    drift_retrain.add_argument(
        "--profile",
        default=None,
        help="Load train defaults from a named profile in config.toml",
    )
    drift_retrain.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Force retrain if drift is detected",
    )
    drift_retrain.add_argument(
        "--threshold-ks",
        type=float,
        default=None,
        help="Kolmogorov-Smirnov threshold (default: config.toml)",
    )
    drift_retrain.add_argument(
        "--threshold-psi",
        type=float,
        default=None,
        help="Population Stability Index threshold (default: config.toml)",
    )
    drift_retrain.add_argument(
        "--min-samples",
        type=int,
        default=None,
        help="Minimum live samples per feature for drift tests (default: config.toml)",
    )
