"""MLflow subcommand parser for MLFX CLI."""

from __future__ import annotations

import argparse

from mlfx.cli.parser._common import ALL_BACKENDS


def add_mlflow_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add mlflow subcommand parser."""
    mlflow = subparsers.add_parser(
        "mlflow",
        help="MLflow integration commands",
        description="Manage MLflow tracking server and migrate artifacts.",
    )
    mlflow_subparsers = mlflow.add_subparsers(
        dest="mlflow_command",
        required=True,
        help="MLflow subcommands",
    )

    mlflow_ui = mlflow_subparsers.add_parser(
        "ui",
        help="Launch MLflow tracking UI",
        description="Start the MLflow tracking server with web UI.",
    )
    mlflow_ui.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the UI server (default: 127.0.0.1)",
    )
    mlflow_ui.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for the UI server (default: 5000)",
    )
    mlflow_ui.add_argument(
        "--backend-store-uri",
        default=None,
        help="URI for MLflow backend store (default: from config)",
    )
    mlflow_ui.add_argument(
        "--default-artifact-root",
        default=None,
        help="Default artifact root path (default: from config)",
    )

    mlflow_migrate = mlflow_subparsers.add_parser(
        "migrate",
        help="Migrate existing artifacts to MLflow",
        description="Migrate existing model artifacts and run metadata to MLflow.",
    )
    mlflow_migrate.add_argument(
        "--symbol",
        default=None,
        help="Migrate only models for this symbol (default: all)",
    )
    mlflow_migrate.add_argument(
        "--tf",
        default=None,
        help="Migrate only models for this timeframe (default: all)",
    )
    mlflow_migrate.add_argument(
        "--backend",
        default=None,
        choices=ALL_BACKENDS,
        metavar="BACKEND",
        help=f"Migrate only models for this backend. Options: {', '.join(ALL_BACKENDS)} (default: all)",
    )
    mlflow_migrate.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview migration without making changes",
    )
    mlflow_migrate.add_argument(
        "--register-models",
        action="store_true",
        default=True,
        help="Register migrated models in MLflow Model Registry (default: True)",
    )
