"""Unit tests for training and feature configuration schemas.

Tests TrainConfig, BacktestConfig, and FeatureConfig validation.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestTrainConfig:
    """Tests for TrainConfig validation."""

    def test_valid_defaults(self):
        from mlfx.config.schema import TrainConfig

        cfg = TrainConfig()
        assert cfg.backend == "mlf"
        assert cfg.n_splits == 5
        assert cfg.n_trials == 30

    def test_invalid_backend_raises(self):
        from mlfx.config.schema import TrainConfig

        with pytest.raises(ValidationError, match="backend"):
            TrainConfig(backend="turbo_magic")

    def test_n_splits_minimum_is_2(self):
        from mlfx.config.schema import TrainConfig

        with pytest.raises(ValidationError):
            TrainConfig(n_splits=1)

    def test_n_splits_of_2_is_valid(self):
        from mlfx.config.schema import TrainConfig

        cfg = TrainConfig(n_splits=2)
        assert cfg.n_splits == 2

    def test_n_trials_minimum_is_1(self):
        from mlfx.config.schema import TrainConfig

        with pytest.raises(ValidationError):
            TrainConfig(n_trials=0)

    def test_cv_method_accepts_documented_values(self):
        from mlfx.config.schema import TrainConfig

        cfg = TrainConfig(cv_method="walk_forward")
        assert cfg.cv_method == "walk_forward"

    def test_embargo_pct_must_be_in_half_open_unit_interval(self):
        from mlfx.config.schema import TrainConfig

        with pytest.raises(ValidationError):
            TrainConfig(embargo_pct=1.0)


class TestBacktestConfig:
    """Tests for BacktestConfig validation."""

    def test_tp_r_must_be_positive(self):
        from mlfx.config.schema import BacktestConfig

        with pytest.raises(ValidationError):
            BacktestConfig(tp_r=0.0)

    def test_sl_r_must_be_positive(self):
        from mlfx.config.schema import BacktestConfig

        with pytest.raises(ValidationError):
            BacktestConfig(sl_r=-1.0)

    def test_risk_pct_must_be_positive(self):
        from mlfx.config.schema import BacktestConfig

        with pytest.raises(ValidationError):
            BacktestConfig(risk_pct=0.0)

    def test_valid_backtest_config(self):
        from mlfx.config.schema import BacktestConfig

        cfg = BacktestConfig(tp_r=1.5, sl_r=1.0, risk_pct=1.0, initial_capital=10_000.0)
        assert cfg.tp_r == 1.5


class TestFeatureConfig:
    """Tests for FeatureConfig validation."""

    def test_ema_periods_default(self):
        from mlfx.config.schema import FeatureConfig

        cfg = FeatureConfig()
        assert cfg.ema_periods == [20, 50, 200]

    def test_ema_periods_custom(self):
        from mlfx.config.schema import FeatureConfig

        cfg = FeatureConfig(ema_periods=[10, 21, 100])
        assert cfg.ema_periods == [10, 21, 100]
