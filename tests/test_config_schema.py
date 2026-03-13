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
# Workflow profile validation
# ---------------------------------------------------------------------------

class TestWorkflowProfiles:
    def test_profile_benchmark_requires_non_empty_backends(self):
        from mlfx.config.schema import ProfileBenchmarkConfig

        with pytest.raises(ValidationError, match="backends"):
            ProfileBenchmarkConfig(backends=[])

    def test_profile_evaluate_accepts_slippage_and_windows(self):
        from mlfx.config.schema import ProfileEvaluateConfig

        cfg = ProfileEvaluateConfig(
            symbol="XAUUSD",
            tf="1H",
            label="label_10",
            tp_r=1.5,
            sl_r=1.0,
            initial_capital=10_000.0,
            risk_pct=1.0,
            commission=0.1,
            eval_start="20250101",
            eval_end="20250331",
        )
        assert cfg.symbol == "XAUUSD"
        assert cfg.eval_start == "20250101"
        assert cfg.eval_end == "20250331"

    def test_app_config_accepts_profiles_mapping(self):
        from mlfx.config.schema import AppConfig

        cfg = AppConfig.model_validate(
            {
                "profiles": {
                    "research": {
                        "train": {
                            "symbol": "XAUUSD",
                            "tf": "1H",
                            "label": "label_10",
                            "backend": "mlf",
                            "train_start": "20240101",
                            "train_end": "20241231",
                            "n_trials": 5,
                            "n_splits": 3,
                        },
                        "evaluate": {
                            "symbol": "XAUUSD",
                            "tf": "1H",
                            "label": "label_10",
                            "eval_start": "20250101",
                            "eval_end": "20250331",
                            "tp_r": 1.5,
                            "sl_r": 1.0,
                            "initial_capital": 10_000.0,
                            "risk_pct": 1.0,
                            "commission": 0.1,
                        },
                        "benchmark": {
                            "symbol": "XAUUSD",
                            "tf": "1H",
                            "label": "label_10",
                            "backends": ["mlf", "sgd", "stats"],
                            "train_start": "20240101",
                            "train_end": "20241231",
                            "n_trials": 5,
                            "n_splits": 3,
                        },
                    }
                }
            }
        )

        assert "research" in cfg.profiles
        assert cfg.profiles["research"].train is not None
        assert cfg.profiles["research"].evaluate is not None
        assert cfg.profiles["research"].benchmark is not None
        assert cfg.profiles["research"].benchmark.backends == ["mlf", "sgd", "stats"]


# ---------------------------------------------------------------------------
# AppConfig round-trip
# ---------------------------------------------------------------------------

class TestAppConfig:
    def test_load_config_returns_app_config(self, tmp_path: Path):
        from mlfx.config.settings import load_config

        with pytest.raises(FileNotFoundError, match="config\\.toml not found"):
            load_config(tmp_path / "nonexistent.toml")

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

    def test_load_config_reflects_profile_overrides(self, tmp_path: Path):
        from mlfx.config.settings import load_config

        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
[profiles.research.train]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
backend = "mlf"
train_start = "20240101"
train_end = "20241231"
n_trials = 5
n_splits = 3

[profiles.research.evaluate]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
eval_start = "20250101"
eval_end = "20250331"
tp_r = 1.5
sl_r = 1.0
initial_capital = 10000.0
risk_pct = 1.0
commission = 0.1

[profiles.research.benchmark]
symbol = "XAUUSD"
tf = "1H"
label = "label_10"
backends = ["mlf", "sgd", "stats"]
train_start = "20240101"
train_end = "20241231"
n_trials = 5
n_splits = 3
"""
        )
        config = load_config(cfg_file)

        assert "research" in config.profiles
        assert config.profiles["research"].train is not None
        assert config.profiles["research"].train.backend == "mlf"
        assert config.profiles["research"].train.train_start == "20240101"
        assert config.profiles["research"].evaluate is not None
        assert config.profiles["research"].evaluate.eval_end == "20250331"
        assert config.profiles["research"].benchmark is not None
        assert config.profiles["research"].benchmark.backends == ["mlf", "sgd", "stats"]

    def test_model_validate_round_trip(self):
        from mlfx.config.schema import AppConfig

        cfg = AppConfig()
        dumped = cfg.model_dump()
        restored = AppConfig.model_validate(dumped)
        assert restored == cfg


# ---------------------------------------------------------------------------
# settings.py helpers
# ---------------------------------------------------------------------------

class TestSettingsHelpers:
    def test_load_config_includes_profiles_mapping(self, tmp_path: Path):
        from mlfx.config.settings import load_config

        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
[profiles.research.train]
backend = "mlf"

[profiles.research.benchmark]
backends = ["mlf", "sgd"]
"""
        )

        cfg = load_config(cfg_file)
        assert "research" in cfg.profiles
        assert cfg.profiles["research"].train is not None
        assert cfg.profiles["research"].train.backend == "mlf"
        assert cfg.profiles["research"].benchmark is not None
        assert cfg.profiles["research"].benchmark.backends == ["mlf", "sgd"]

    def test_resolve_profile_section_returns_single_section(self, tmp_path: Path):
        from mlfx.cli.resolve import resolve_profile_section
        from mlfx.config.settings import load_config

        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
[profiles.research.train]
backend = "mlf"

[profiles.oos.evaluate]
eval_start = "20250101"
"""
        )

        cfg = load_config(cfg_file)
        section = resolve_profile_section(cfg, "research", "train")
        assert section["backend"] == "mlf"

    def test_resolve_profile_section_raises_for_unknown_profile(self, tmp_path: Path):
        from mlfx.cli.resolve import resolve_profile_section
        from mlfx.config.settings import load_config

        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
[profiles.research.train]
backend = "mlf"
"""
        )

        cfg = load_config(cfg_file)
        with pytest.raises(ValueError, match="Unknown profile"):
            resolve_profile_section(cfg, "missing", "train")

    def test_resolve_profile_section_handles_missing_and_none(self, tmp_path: Path):
        from mlfx.cli.resolve import resolve_profile_section
        from mlfx.config.settings import load_config

        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
[profiles.research.train]
backend = "mlf"
"""
        )
        cfg = load_config(cfg_file)

        assert resolve_profile_section(cfg, None, "train") == {}

        with pytest.raises(ValueError, match="does not define a 'benchmark' section"):
            resolve_profile_section(cfg, "research", "benchmark")


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
