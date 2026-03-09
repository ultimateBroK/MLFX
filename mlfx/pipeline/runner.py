"""Multi-timeframe pipeline orchestrator.

Wraps ``resample_symbol_tf``, ``run_feature_pipeline``, and
``run_label_pipeline`` into a single ``run_pipeline`` call that iterates over
one or more timeframes for a given symbol.
"""

from __future__ import annotations

import logging
from typing import Any

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths
from mlfx.config.schema import FeatureConfig, PipelineConfig

logger = logging.getLogger(__name__)


def run_pipeline(
    symbol: str,
    timeframes: list[str],
    force: bool = False,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
    feature_cfg: FeatureConfig | None = None,
    pipeline_cfg: PipelineConfig | None = None,
) -> dict[str, dict[str, Any]]:
    """Run the full pipeline (resample → features → labels) for one or more timeframes.

    Args:
        symbol: Instrument symbol (e.g. ``"XAUUSD"``).
        timeframes: Non-empty list of timeframe strings (e.g. ``["1H", "4H"]``).
        force: Reprocess existing output files when ``True``.
        paths: ``ProjectPaths`` instance for data directory resolution.
        feature_cfg: Indicator hyper-parameters; defaults to ``FeatureConfig()``.
        pipeline_cfg: Labelling / pivot configuration; defaults to ``PipelineConfig()``.

    Returns:
        Mapping of *timeframe → stage stats dict* where each stage dict has the
        keys returned by the individual stage functions (``processed``,
        ``skipped``, ``total_bars``, …).

    Raises:
        ValueError: If *timeframes* is empty.
    """
    if not timeframes:
        raise ValueError("timeframes must be a non-empty list")

    # Lazily-imported here to avoid heavy TA-Lib import at module load time.
    from mlfx.pipeline.feature_engineering import run_feature_pipeline
    from mlfx.pipeline.labeling import run_label_pipeline
    from mlfx.pipeline.resampling import resample_symbol_tf

    _feat_cfg = feature_cfg if feature_cfg is not None else FeatureConfig()
    _pipe_cfg = pipeline_cfg if pipeline_cfg is not None else PipelineConfig()

    results: dict[str, dict[str, Any]] = {}
    for tf in timeframes:
        logger.info("Running pipeline for %s %s", symbol, tf)

        resample_stats = resample_symbol_tf(symbol=symbol, tf=tf, force=force, paths=paths)
        feature_stats = run_feature_pipeline(
            symbol=symbol,
            tf=tf,
            pivot_type=_pipe_cfg.pivot_type,
            pivot_anchor=_pipe_cfg.pivot_anchor,
            force=force,
            paths=paths,
            feature_cfg=_feat_cfg,
        )
        label_stats = run_label_pipeline(
            symbol=symbol,
            tf=tf,
            atr_period=_feat_cfg.atr_period,
            atr_mult=_pipe_cfg.atr_mult,
            force=force,
            paths=paths,
        )

        results[tf] = {
            "resample": resample_stats,
            "features": feature_stats,
            "labels": label_stats,
        }
        logger.info(
            "Completed %s %s — resample=%s features=%s labels=%s",
            symbol,
            tf,
            resample_stats.get("processed", 0),
            feature_stats.get("processed", 0),
            label_stats.get("processed", 0),
        )

    return results
