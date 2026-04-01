"""Common constants and utilities for CLI parsers.

This module centralizes shared imports to avoid import-time side effects
in parser modules. All backend registry access goes through this module.
"""

from __future__ import annotations

from mlfx.training.registry import BACKEND_REGISTRY

#: Sorted list of all available backend names for argument choices.
ALL_BACKENDS = sorted(BACKEND_REGISTRY)
