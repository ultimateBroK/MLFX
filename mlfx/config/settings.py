"""Shared application settings loader."""

from __future__ import annotations

import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any

from .paths import DEFAULT_PATHS
from .schema import AppConfig

DEFAULT_CONFIG: dict[str, dict[str, Any]] = {
    "download": {
        "symbol": "XAUUSD",
        "asset_class": "fx",
        "start_year": 2015,
        "start_month": 1,
        "concurrency": 20,
    },
    "pipeline": {
        "symbol": "XAUUSD",
        "timeframe": "1H",
        "pivot_type": "traditional",
        "pivot_anchor": "daily",
        "atr_period": 14,
        "atr_mult": 0.5,
    },
    "features": {
        "rsi_period": 14,
        "atr_period": 14,
        "ema_periods": [20, 50, 200],
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        "avg_range_n": 5,
    },
    "train": {
        "symbol": "XAUUSD",
        "timeframe": "1H",
        "label_col": "label_10",
        "backend": "mlf",
        "n_trials": 30,
        "n_splits": 5,
    },
    "backtest": {
        "symbol": "XAUUSD",
        "timeframe": "1H",
        "label_col": "label_10",
    },
}


def _load_raw_config_data(config_file: Path | None = None) -> dict[str, Any]:
    """Load raw TOML data or fall back to an empty mapping when config is absent."""
    target = config_file or DEFAULT_PATHS.config_file
    if not target.exists():
        return {}
    with target.open("rb") as handle:
        return tomllib.load(handle)


def _build_merged_config_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Merge built-in defaults with file overrides, preserving custom profile sections."""
    merged: dict[str, Any] = {}
    for section, defaults in DEFAULT_CONFIG.items():
        merged[section] = {**defaults, **data.get(section, {})}
    merged["profiles"] = deepcopy(data.get("profiles", {}))
    return merged


def load_config(config_file: Path | None = None) -> AppConfig:
    """Load and merge runtime config with built-in defaults, then validate.

    The TOML file is optional — if absent the schema defaults apply.  All
    unknown keys in the TOML are silently ignored (``extra='ignore'``).
    """
    data = _load_raw_config_data(config_file)
    merged = _build_merged_config_dict(data)
    return AppConfig.model_validate(merged)


def load_profiles(config_file: Path | None = None) -> dict[str, dict[str, Any]]:
    """Return the raw profile mapping from config.toml.

    Profiles are intentionally kept as flexible dictionaries so CLI commands
    can resolve only the sections they need (e.g. ``train``, ``evaluate``,
    ``benchmark``) without forcing a rigid schema up front.
    """
    data = _load_raw_config_data(config_file)
    profiles = data.get("profiles", {})
    if not isinstance(profiles, dict):
        return {}
    return deepcopy(profiles)


def get_profile(config_file: Path | None, profile_name: str) -> dict[str, Any]:
    """Fetch a single profile by name from the config file."""
    profiles = load_profiles(config_file)
    profile = profiles.get(profile_name)
    if not isinstance(profile, dict):
        raise KeyError(f"Unknown profile '{profile_name}'")
    return deepcopy(profile)


def resolve_profile_section(
    profile: dict[str, Any],
    section_name: str,
) -> dict[str, Any]:
    """Extract one section from a profile as a plain dictionary.

    Missing sections resolve to an empty mapping so callers can decide whether
    that is acceptable for the current command.
    """
    section = profile.get(section_name, {})
    if not isinstance(section, dict):
        return {}
    return deepcopy(section)
