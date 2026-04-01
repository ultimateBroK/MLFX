"""
tests/test_mlfx_pipeline.py
===========================
Contract tests for the migrated `mlfx.pipeline` and `mlfx.features` modules.
"""

from __future__ import annotations

import polars as pl


class TestMlfxResampling:
    def test_resampling_module_exposes_timeframes(self, sample_ticks):
        from mlfx.pipeline.resample import TIMEFRAMES, resample_to_ohlcv

        assert "1H" in TIMEFRAMES
        result = resample_to_ohlcv(sample_ticks, period=TIMEFRAMES["1H"])
        assert set(result.columns) >= {
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "tick_count",
        }


class TestMlfxIndicators:
    def test_killzone_module_builds_session_features(self, sample_ohlcv):
        from mlfx.features.technical.killzone import add_killzone_features

        result = add_killzone_features(sample_ohlcv)
        assert "in_london" in result.columns
        assert "d_open" in result.columns

    def test_sr_pp_module_builds_support_resistance_features(self, sample_ohlcv):
        from mlfx.features.technical.sr_pp import add_sr_pp_features

        result = add_sr_pp_features(sample_ohlcv)
        assert "sr_resist_1bar" in result.columns
        assert "pp_p" in result.columns


class TestMlfxFeatureEngineering:
    def test_feature_engineering_module_builds_full_feature_matrix(self, sample_ohlcv):
        from mlfx.pipeline.features import build_feature_pipeline

        result = build_feature_pipeline(sample_ohlcv)
        assert "rsi_14" in result.columns
        assert "pp_p" in result.columns
        assert "ema_20" in result.columns


class TestMlfxLabeling:
    def test_labeling_module_generates_labels(self, sample_ohlcv):
        from mlfx.pipeline.labels import add_labels

        with_atr = sample_ohlcv.with_columns(pl.lit(2.5).alias("atr_14"))
        result = add_labels(with_atr, horizons=[5])
        assert "close_ahead_5" in result.columns
        assert "label_5" in result.columns
