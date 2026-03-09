"""tests/test_config_schema.py
================================
Unit tests for the Pydantic configuration schemas in mlfx.config.schema.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# TrainConfig validation
# ---------------------------------------------------------------------------

class TestTrainConfig:
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


# ---------------------------------------------------------------------------
# BacktestConfig validation
# ---------------------------------------------------------------------------

class TestBacktestConfig:
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


# ---------------------------------------------------------------------------
# FeatureConfig validation
# ---------------------------------------------------------------------------

class TestFeatureConfig:
    def test_ema_periods_default(self):
        from mlfx.config.schema import FeatureConfig

        cfg = FeatureConfig()
        assert cfg.ema_periods == [20, 50, 200]

    def test_ema_periods_custom(self):
        from mlfx.config.schema import FeatureConfig

        cfg = FeatureConfig(ema_periods=[10, 21, 100])
        assert cfg.ema_periods == [10, 21, 100]


# ---------------------------------------------------------------------------
# AppConfig round-trip
# ---------------------------------------------------------------------------

class TestAppConfig:
    def test_load_config_returns_app_config(self, tmp_path: Path):
        from mlfx.config.schema import AppConfig
        from mlfx.config.settings import load_config

        config = load_config(tmp_path / "nonexistent.toml")
        assert isinstance(config, AppConfig)

    def test_load_config_reflects_toml_overrides(self, tmp_path: Path):
        from mlfx.config.schema import AppConfig
        from mlfx.config.settings import load_config

        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            "[train]\nn_splits = 10\nbackend = \"stats\"\n"
        )
        config = load_config(cfg_file)
        assert isinstance(config, AppConfig)
        assert config.train.n_splits == 10
        assert config.train.backend == "stats"

    def test_model_validate_round_trip(self):
        from mlfx.config.schema import AppConfig

        cfg = AppConfig()
        dumped = cfg.model_dump()
        restored = AppConfig.model_validate(dumped)
        assert restored == cfg


# ---------------------------------------------------------------------------
# ServingSettings env-var overrides
# ---------------------------------------------------------------------------

class TestServingSettings:
    def test_default_log_level(self):
        from mlfx.config.schema import ServingSettings

        s = ServingSettings()
        assert s.log_level == "INFO"

    def test_env_override_log_level(self, monkeypatch):
        monkeypatch.setenv("MLFX_LOG_LEVEL", "DEBUG")
        # Re-instantiate to pick up the env var.
        from mlfx.config.schema import ServingSettings  # noqa: PLC0415

        s = ServingSettings()
        assert s.log_level == "DEBUG"

    def test_env_override_data_root(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MLFX_DATA_ROOT", str(tmp_path / "data"))
        from mlfx.config.schema import ServingSettings  # noqa: PLC0415

        s = ServingSettings()
        assert str(s.data_root) == str(tmp_path / "data")

    def test_env_override_propagates_to_get_project_paths(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MLFX_DATA_ROOT", str(tmp_path / "override_data"))
        from mlfx.config.paths import get_project_paths  # noqa: PLC0415
        from mlfx.config.schema import ServingSettings  # noqa: PLC0415

        paths = get_project_paths(ServingSettings())
        assert paths.data_root == (tmp_path / "override_data").resolve()
