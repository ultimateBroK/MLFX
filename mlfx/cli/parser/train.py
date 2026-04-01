"""Train and evaluate subcommand parsers for MLFX CLI."""

from __future__ import annotations

import argparse

from mlfx.cli.parser._common import ALL_BACKENDS


def add_train_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add train subcommand parser."""
    train = subparsers.add_parser(
        "train",
        help="Train a single model backend",
        description="Train one backend with Optuna HPO and CV.",
    )
    train.add_argument("--symbol", default=None, help="Symbol (default: config.toml)")
    train.add_argument("--tf", default=None, help="Timeframe (default: config.toml)")
    train.add_argument(
        "--label",
        default=None,
        help="Label column: label_5, label_10, label_20 (default: config.toml)",
    )
    train.add_argument(
        "--backend",
        default=None,
        choices=ALL_BACKENDS,
        metavar="BACKEND",
        help=f"Model backend. Options: {', '.join(ALL_BACKENDS)} (default: config.toml)",
    )
    train.add_argument(
        "--n-trials", type=int, default=None, help="Optuna trials for HPO"
    )
    train.add_argument(
        "--n-splits", type=int, default=None, help="TimeSeriesSplit folds"
    )
    train.add_argument(
        "--cv-method",
        choices=["purged_kfold", "purged_timeseries", "walk_forward", "timeseries"],
        default=None,
        help="Cross-validation method (default: config.toml)",
    )
    train.add_argument(
        "--embargo-pct",
        type=float,
        default=None,
        help="Embargo percentage for purged CV methods (default: config.toml)",
    )
    train.add_argument(
        "--train-start",
        default=None,
        help="Inclusive training start date in compact format YYYYMMDD, e.g. 20240101",
    )
    train.add_argument(
        "--train-end",
        default=None,
        help="Inclusive training end date in compact format YYYYMMDD, e.g. 20241231",
    )
    train.add_argument(
        "--profile",
        default=None,
        help="Load train defaults from a named profile in config.toml",
    )
    train.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Force retrain (overwrite saved model)",
    )
    train.add_argument(
        "--mlflow",
        action="store_true",
        default=False,
        help="Enable MLflow experiment tracking and model registry",
    )


def add_evaluate_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add evaluate subcommand parser."""
    evaluate = subparsers.add_parser(
        "evaluate",
        help="Run walk-forward backtest",
        description="Backtest a trained model or baseline labels.",
    )
    evaluate.add_argument("--symbol", default=None, help="Symbol")
    evaluate.add_argument("--tf", default=None, help="Timeframe")
    evaluate.add_argument("--label", default=None, help="Label column")
    evaluate.add_argument(
        "--capital", type=float, default=None, help="Initial capital in USD"
    )
    evaluate.add_argument("--risk", type=float, default=None, help="Risk per trade %%")
    evaluate.add_argument(
        "--commission", type=float, default=None, help="Commission in pips"
    )
    evaluate.add_argument(
        "--tp", type=float, default=None, help="Take-profit in R multiples"
    )
    evaluate.add_argument(
        "--sl", type=float, default=None, help="Stop-loss in R multiples"
    )
    evaluate.add_argument(
        "--slippage", type=float, default=None, help="Slippage in pips"
    )
    evaluate.add_argument(
        "--eval-start",
        default=None,
        help="Inclusive evaluation start date in compact format YYYYMMDD, e.g. 20240101",
    )
    evaluate.add_argument(
        "--eval-end",
        default=None,
        help="Inclusive evaluation end date in compact format YYYYMMDD, e.g. 20241231",
    )
    evaluate.add_argument(
        "--profile",
        default=None,
        help="Load evaluation defaults from a named profile in config.toml",
    )
    evaluate.add_argument(
        "--use-labels",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Backtest labels only (baseline). Default: backtest model if trained, else labels.",
    )
