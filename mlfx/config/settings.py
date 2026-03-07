"""Shared application settings loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import tomllib

from .paths import DEFAULT_PATHS


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


def load_config(config_file: Path | None = None) -> dict[str, dict[str, Any]]:
    """Load and merge runtime config with built-in defaults."""
    target = config_file or DEFAULT_PATHS.config_file
    if not target.exists():
        return {section: values.copy() for section, values in DEFAULT_CONFIG.items()}

    with target.open("rb") as handle:
        data = tomllib.load(handle)

    merged: dict[str, dict[str, Any]] = {}
    for section, defaults in DEFAULT_CONFIG.items():
        merged[section] = {**defaults, **data.get(section, {})}
    return merged
