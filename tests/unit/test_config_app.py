"""Unit tests for AppConfig and workflow profile schemas.

Tests AppConfig round-trip serialization and workflow profile validation.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError


class TestWorkflowProfiles:
    """Tests for workflow profile validation."""

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
                            "cv_method": "purged_kfold",
                            "embargo_pct": 0.02,
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
        assert cfg.profiles["research"].train.cv_method == "purged_kfold"
        assert cfg.profiles["research"].train.embargo_pct == 0.02


class TestAppConfig:
    """Tests for AppConfig round-trip serialization."""

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
cv_method = "purged_kfold"
embargo_pct = 0.02
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
        assert config.profiles["research"].train.cv_method == "purged_kfold"
        assert config.profiles["research"].train.embargo_pct == 0.02
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
