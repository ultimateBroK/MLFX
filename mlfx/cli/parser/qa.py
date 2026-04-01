"""QA subcommand parser for MLFX CLI."""

from __future__ import annotations

import argparse


def add_qa_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add QA subcommand parser."""
    qa = subparsers.add_parser(
        "qa",
        help="Audit raw downloaded tick data",
        description="Run quality checks on downloaded raw tick data.",
    )
    qa.add_argument(
        "--symbol", default=None, help="Symbol to audit (default: config.toml)"
    )
    qa.add_argument(
        "--asset-class",
        choices=["fx", "crypto"],
        default=None,
        help="Asset class (default: config.toml)",
    )
