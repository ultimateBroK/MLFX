"""Tests for CLI train command configuration resolution."""

from __future__ import annotations

import argparse
import importlib

import pytest


@pytest.fixture
def cli_module(monkeypatch):
    """Import the CLI module with logging setup neutralized."""
    monkeypatch.setattr(
        "mlfx.monitoring.logging_config.configure_logging",
        lambda level="INFO": None,
    )
    cli = importlib.import_module("mlfx.cli.main")
    return importlib.reload(cli)


@pytest.fixture
def sample_app_config():
    from types import SimpleNamespace

    return SimpleNamespace(
        train=SimpleNamespace(
            symbol="DEFAULT_SYMBOL",
            tf="4H",
            label="label_default",
            backend="sgd",
            n_trials=30,
            n_splits=5,
            cv_method="purged_timeseries",
            embargo_pct=0.01,
            force=False,
            train_start=None,
            train_end=None,
        ),
        backtest=SimpleNamespace(
            symbol="DEFAULT_SYMBOL",
            tf="4H",
            label="label_default",
            initial_capital=20_000.0,
            risk_pct=2.0,
            commission=0.2,
            tp_r=2.0,
            sl_r=1.2,
            slippage=0.0,
            eval_start=None,
            eval_end=None,
            use_labels=False,
        ),
    )


@pytest.fixture
def sample_profile():
    return {
        "train": {
            "symbol": "XAUUSD",
            "tf": "1H",
            "label": "label_10",
            "backend": "mlf",
            "train_start": "20240101",
            "train_end": "20241231",
            "n_trials": 5,
            "n_splits": 3,
            "cv_method": "walk_forward",
            "embargo_pct": 0.02,
            "force": True,
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
            "slippage": 0.0,
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


class TestResolveTrainCommandConfig:
    def test_profile_values_are_used_when_cli_values_are_missing(
        self, monkeypatch, cli_module, sample_app_config, sample_profile
    ) -> None:
        monkeypatch.setattr("mlfx.cli.resolve.load_config", lambda: sample_app_config)
        monkeypatch.setattr(
            "mlfx.cli.resolve.resolve_profile_section",
            lambda cfg, profile_name, section: sample_profile[section],
        )

        args = argparse.Namespace(
            profile="research",
            symbol=None,
            tf=None,
            label=None,
            backend=None,
            n_trials=None,
            n_splits=None,
            cv_method=None,
            embargo_pct=None,
            train_start=None,
            train_end=None,
            force=None,
        )

        resolved = cli_module._resolve_train_command_config(args)

        assert resolved == {
            "symbol": "XAUUSD",
            "tf": "1H",
            "label": "label_10",
            "backend": "mlf",
            "n_trials": 5,
            "n_splits": 3,
            "cv_method": "walk_forward",
            "embargo_pct": 0.02,
            "force": True,
            "train_start": "20240101",
            "train_end": "20241231",
        }

    def test_cli_values_override_profile_values(
        self, monkeypatch, cli_module, sample_app_config, sample_profile
    ) -> None:
        monkeypatch.setattr("mlfx.cli.resolve.load_config", lambda: sample_app_config)
        monkeypatch.setattr(
            "mlfx.cli.resolve.resolve_profile_section",
            lambda cfg, profile_name, section: sample_profile[section],
        )

        args = argparse.Namespace(
            profile="research",
            symbol="EURUSD",
            tf="15m",
            label="label_20",
            backend="stats",
            n_trials=9,
            n_splits=4,
            cv_method="purged_kfold",
            embargo_pct=0.05,
            train_start="20230101",
            train_end="20230630",
            force=False,
        )

        resolved = cli_module._resolve_train_command_config(args)

        assert resolved == {
            "symbol": "EURUSD",
            "tf": "15m",
            "label": "label_20",
            "backend": "stats",
            "n_trials": 9,
            "n_splits": 4,
            "cv_method": "purged_kfold",
            "embargo_pct": 0.05,
            "force": False,
            "train_start": "20230101",
            "train_end": "20230630",
        }
