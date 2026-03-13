"""Legacy compatibility entrypoint for CLI imports.

Prefer using mlfx.cli.main directly.
"""

from __future__ import annotations

from mlfx.cli.main import main

__all__ = ["main"]
