"""Configuration constants for MLFX Streamlit UI."""

from __future__ import annotations

from pathlib import Path

from mlfx.config.paths import DEFAULT_PATHS

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
CONFIG_FILE = DEFAULT_PATHS.config_file

TF_OPTIONS = ["1m", "5m", "15m", "30m", "1H", "2H", "4H", "1D"]
ASSET_CLASS_OPTIONS = ["fx", "crypto"]
BACKEND_OPTIONS = [
    "mlf",
    "lstm",
    "transformer",
    "cnn_lstm",
    "sgd",
    "stats",
    "neuralforecast",
]
LABEL_OPTIONS = ["label_5", "label_10", "label_20"]
PIVOT_TYPE_OPTIONS = ["traditional", "fibonacci", "woodie", "classic", "demark", "camarilla"]
PIVOT_ANCHOR_OPTIONS = ["daily", "weekly", "monthly"]
