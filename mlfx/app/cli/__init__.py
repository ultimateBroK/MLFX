"""Legacy compatibility package for old CLI import paths.

Prefer using mlfx.cli instead.
"""

from __future__ import annotations

from mlfx.app.cli.main import main

__all__ = ["main"]
