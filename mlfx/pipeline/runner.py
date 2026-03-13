"""Multi-timeframe pipeline orchestrator.

Wraps ``resample_symbol_tf``, ``run_feature_pipeline``, and
``run_label_pipeline`` into a single ``run_pipeline`` call that iterates over
one or more timeframes for a given symbol. Supports skip flags so CLI/workflow
entrypoints can share one implementation.
"""

from __future__ import annotations

import logging
from typing import Any

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths
from mlfx.config.schema import FeatureConfig, PipelineConfig

logger = logging.getLogger(__name__)


_DEFAULT_LABEL_COLS = ["label_5", "label_10", "label_20"]


def _skipped_stage_stats(stage: str) -> dict[str, Any]:
    """Return a canonical skipped payload for one pipeline sub-stage."""
    base: dict[str, Any] = {"processed": 0, "skipped": 1, "total_bars": 0}
    if stage == "features":
        base["total_features"] = 0
    elif stage == "labels":
        base["label_cols"] = list(_DEFAULT_LABEL_COLS)
    return base


def run_pipeline(
    symbol: str,
    timeframes: list[str],
    force: bool = False,
    *,
    skip_resample: bool = False,
    skip_features: bool = False,
    skip_labels: bool = False,
    paths: ProjectPaths = DEFAULT_PATHS,
    feature_cfg: FeatureConfig | None = None,
    pipeline_cfg: PipelineConfig | None = None,
) -> dict[str, dict[str, Any]]:
    """Run the full pipeline (resample → features → labels) for one or more timeframes.

    Args:
        symbol: Instrument symbol (e.g. ``"XAUUSD"``).
        timeframes: Non-empty list of timeframe strings (e.g. ``["1H", "4H"]``).
        force: Reprocess existing output files when ``True``.
        skip_resample: Skip resample stage and emit canonical skipped stats.
        skip_features: Skip features stage and emit canonical skipped stats.
        skip_labels: Skip labels stage and emit canonical skipped stats.
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
    from mlfx.pipeline.features import run_feature_pipeline
    from mlfx.pipeline.labels import run_label_pipeline
    from mlfx.pipeline.resample import resample_symbol_tf

    _feat_cfg = feature_cfg if feature_cfg is not None else FeatureConfig()
    _pipe_cfg = pipeline_cfg if pipeline_cfg is not None else PipelineConfig()

    results: dict[str, dict[str, Any]] = {}
    for tf in timeframes:
        logger.info("Running pipeline for %s %s", symbol, tf)

        if skip_resample:
            resample_stats = _skipped_stage_stats("resample")
        else:
            resample_stats = resample_symbol_tf(symbol=symbol, tf=tf, force=force, paths=paths)

        if skip_features:
            feature_stats = _skipped_stage_stats("features")
        else:
            feature_stats = run_feature_pipeline(
                symbol=symbol,
                tf=tf,
                pivot_type=_pipe_cfg.pivot_type,
                pivot_anchor=_pipe_cfg.pivot_anchor,
                force=force,
                paths=paths,
                feature_cfg=_feat_cfg,
            )

        if skip_labels:
            label_stats = _skipped_stage_stats("labels")
        else:
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
