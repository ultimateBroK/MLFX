"""Backward compatibility module - re-exports from mlfx.features.

This module provides backward compatibility for code that imports from
`mlfx.pipeline.features`. New code should import directly from `mlfx.features`.

Example:
    # Old import (still works)
    from mlfx.pipeline.features import build_feature_pipeline, run_feature_pipeline

    # New import (preferred)
    from mlfx.features import build_feature_pipeline, run_feature_pipeline
"""

from __future__ import annotations

from mlfx.features.ta import (
    add_atr,
    add_ema,
    add_macd,
    add_normalized_distances,
    add_rsi,
)
from mlfx.features.pipeline import (
    build_feature_pipeline,
    run_feature_pipeline,
)

__all__ = [
    # TA indicators
    "add_rsi",
    "add_macd",
    "add_atr",
    "add_ema",
    "add_normalized_distances",
    # Pipeline orchestration
    "build_feature_pipeline",
    "run_feature_pipeline",
]
