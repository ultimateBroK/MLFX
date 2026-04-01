"""Models and profiles subcommand parsers for MLFX CLI."""

from __future__ import annotations

import argparse


def add_models_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add models subcommand parser."""
    models = subparsers.add_parser(
        "models",
        help="List registered model versions",
        description="Show all models in the registry with optional filtering.",
    )
    models.add_argument("--symbol", default=None, help="Filter by symbol")
    models.add_argument("--tf", default=None, help="Filter by timeframe")
    models.add_argument("--backend", default=None, help="Filter by backend")


def add_profiles_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add profiles subcommand parser."""
    profiles = subparsers.add_parser(
        "profiles",
        help="List available workflow profiles",
        description="Show workflow profiles from config.toml and which commands they support.",
    )
    profiles.add_argument(
        "--profile",
        default=None,
        help="Show only one profile in detailed form",
    )
