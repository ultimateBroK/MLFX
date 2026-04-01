"""Serve and batch-predict subcommand parsers for MLFX CLI."""

from __future__ import annotations

import argparse


def add_serve_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add serve subcommand parser."""
    serve = subparsers.add_parser(
        "serve",
        help="Start FastAPI inference server",
        description="Launch the real-time prediction API.",
    )
    serve.add_argument(
        "--host", default=None, help="Bind address (default: config.toml)"
    )
    serve.add_argument(
        "--port", type=int, default=None, help="Port (default: config.toml)"
    )
    serve.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable auto-reload (default: config.toml)",
    )


def add_batch_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add batch-predict subcommand parser."""
    batch = subparsers.add_parser(
        "batch-predict",
        help="Run batch inference",
        description="Generate predictions for all bars and save to disk.",
    )
    batch.add_argument("--symbol", default=None, help="Symbol (default: config.toml)")
    batch.add_argument("--tf", default=None, help="Timeframe (default: config.toml)")
    batch.add_argument(
        "--label", default=None, help="Label column (default: config.toml)"
    )
