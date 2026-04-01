"""Shared application settings loader."""

from __future__ import annotations

from functools import lru_cache
import tomllib
from pathlib import Path
from typing import Any

from .paths import DEFAULT_PATHS
from .schema import AppConfig

def _load_raw_config_data(config_file: Path | None = None) -> dict[str, Any]:
    """Load raw TOML config data.

    The config file is mandatory. All unknown keys in the TOML are silently
    ignored by the Pydantic models (``extra='ignore'``).
    """
    target = config_file or DEFAULT_PATHS.config_file
    if not target.exists():
        raise FileNotFoundError(
            f"config.toml not found at {target}. Create one (see repo root config.toml)."
        )
    with target.open("rb") as handle:
        return tomllib.load(handle)


@lru_cache(maxsize=1)
def load_config(config_file: Path | None = None) -> AppConfig:
    """Load and validate config.toml into a single AppConfig object."""
    data = _load_raw_config_data(config_file)
    return AppConfig.model_validate(data)
