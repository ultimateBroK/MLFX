"""Profiles command handler."""

from __future__ import annotations

import argparse
import logging

from ..render import console, print_profiles_summary

logger = logging.getLogger(__name__)


def handle_profiles(args: argparse.Namespace) -> None:
    """Handle the profiles command."""
    from mlfx.config.settings import load_config

    try:
        config = load_config()
    except FileNotFoundError:
        console.print("[yellow]config.toml not found — no workflow profiles available.[/yellow]")
        return

    profiles = {
        name: profile.model_dump(exclude_none=True)
        for name, profile in config.profiles.items()
    }
    print_profiles_summary(args.profile, profiles)
