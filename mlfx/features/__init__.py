"""Feature-engineering namespace and shared feature-column helpers."""

from .columns import FEATURE_BLACKLIST, NUMERIC_DTYPES, select_numeric_feature_columns
from .ta import add_atr, add_ema, add_macd, add_normalized_distances, add_rsi
from .technical import add_killzone_features, add_sr_pp_features
from .pipeline import build_feature_pipeline, run_feature_pipeline

__all__ = [
    # Column helpers
    "FEATURE_BLACKLIST",
    "NUMERIC_DTYPES",
    "select_numeric_feature_columns",
    # TA indicators
    "add_rsi",
    "add_macd",
    "add_atr",
    "add_ema",
    "add_normalized_distances",
    # Custom features
    "add_killzone_features",
    "add_sr_pp_features",
    # Pipeline orchestration
    "build_feature_pipeline",
    "run_feature_pipeline",
]
