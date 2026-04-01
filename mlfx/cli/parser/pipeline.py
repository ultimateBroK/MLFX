"""Pipeline subcommand parser for MLFX CLI."""

from __future__ import annotations

import argparse


def add_pipeline_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add pipeline subcommand parser."""
    pipeline = subparsers.add_parser(
        "pipeline",
        help="Run ETL pipeline: resample → features → labels",
        description="Execute the full data pipeline for one or more timeframes.",
    )
    pipeline.add_argument(
        "--symbol", default=None, help="Symbol (default: config.toml)"
    )
    pipeline.add_argument(
        "--tf",
        nargs="+",
        default=None,
        metavar="TF",
        help="Timeframe(s) to process: 1m, 5m, 15m, 30m, 1H, 2H, 4H, 1D (default: config.toml)",
    )
    pipeline.add_argument(
        "--pivot",
        default=None,
        help="Pivot type: traditional, fibonacci, woodie, classic, demark, camarilla (default: config.toml)",
    )
    pipeline.add_argument(
        "--anchor",
        default=None,
        help="Pivot anchor: daily, weekly, monthly (default: config.toml)",
    )
    pipeline.add_argument(
        "--atr-period",
        type=int,
        default=None,
        help="ATR period for label generation (default: config.toml)",
    )
    pipeline.add_argument(
        "--atr-mult",
        type=float,
        default=None,
        help="ATR multiplier for label thresholds (default: config.toml)",
    )
    pipeline.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Overwrite existing files (default: config.toml)",
    )
    pipeline.add_argument(
        "--skip-resample",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Skip tick → OHLCV resampling (default: config.toml)",
    )
    pipeline.add_argument(
        "--skip-features",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Skip feature engineering (default: config.toml)",
    )
    pipeline.add_argument(
        "--skip-labels",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Skip label generation (default: config.toml)",
    )
