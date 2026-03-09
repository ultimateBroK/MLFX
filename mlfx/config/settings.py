"""Shared application settings loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import tomllib

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


def load_config(config_file: Path | None = None) -> AppConfig:
    """Load and merge runtime config with built-in defaults, then validate.

    The TOML file is optional — if absent the schema defaults apply.  All
    unknown keys in the TOML are silently ignored (``extra='ignore'``).
    """
    target = config_file or DEFAULT_PATHS.config_file
    if not target.exists():
        raw: dict[str, dict[str, Any]] = {
            section: values.copy() for section, values in DEFAULT_CONFIG.items()
        }
        return AppConfig.model_validate(raw)

    with target.open("rb") as handle:
        data = tomllib.load(handle)

    merged: dict[str, dict[str, Any]] = {}
    for section, defaults in DEFAULT_CONFIG.items():
        merged[section] = {**defaults, **data.get(section, {})}
    return AppConfig.model_validate(merged)
