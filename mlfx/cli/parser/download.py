"""Download subcommand parser for MLFX CLI."""

from __future__ import annotations

import argparse


def add_download_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add download subcommand parser."""
    download = subparsers.add_parser(
        "download",
        help="Download raw tick data from Dukascopy",
        description="Download historical tick data for a symbol.",
    )
    download.add_argument(
        "--symbol", default=None, help="Symbol to download (default: config.toml)"
    )
    download.add_argument(
        "--asset-class",
        choices=["fx", "crypto"],
        default=None,
        help="Asset class (default: config.toml)",
    )
    download.add_argument(
        "--start-year", type=int, default=None, help="Start year (default: config.toml)"
    )
    download.add_argument(
        "--start-month",
        type=int,
        default=None,
        help="Start month 1-12 (default: config.toml)",
    )
    download.add_argument(
        "--end-year", type=int, default=None, help="End year (default: current year)"
    )
    download.add_argument(
        "--end-month", type=int, default=None, help="End month (default: current month)"
    )
    download.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Parallel downloads (default: config.toml)",
    )
    download.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Force re-verify existing months (default: config.toml)",
    )
    download.add_argument(
        "--skip-current-month",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Skip checking/repairing current month (default: config.toml)",
    )
