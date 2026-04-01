"""Core namespace for the MLFX application package."""

from .config.paths import DEFAULT_PATHS, ProjectPaths
from .config.settings import load_config

__all__ = [
    "DEFAULT_PATHS",
    "ProjectPaths",
    "load_config",
]
