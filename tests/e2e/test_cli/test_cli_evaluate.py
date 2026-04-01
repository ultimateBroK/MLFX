"""Tests for CLI evaluate command configuration resolution."""

from __future__ import annotations

import argparse
import importlib
from types import SimpleNamespace

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
    return SimpleNamespace(
        train=SimpleNamespace(
            symbol="DEFAULT_SYMBOL",
            tf="4H",
            label="label_default",
            backend="sgd",
            n_trials=30,
            n_splits=5,
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


class TestResolveEvaluateCommandConfig:
    def test_profile_values_are_used_for_evaluate(
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
            capital=None,
            risk=None,
            commission=None,
            tp=None,
            sl=None,
            slippage=None,
            eval_start=None,
            eval_end=None,
            use_labels=None,
        )

        resolved = cli_module._resolve_evaluate_command_config(args)

        assert resolved == {
            "symbol": "XAUUSD",
            "tf": "1H",
            "label": "label_10",
            "capital": 10_000.0,
            "risk": 1.0,
            "commission": 0.1,
            "tp": 1.5,
            "sl": 1.0,
            "slippage": 0.0,
            "eval_start": "20250101",
            "eval_end": "20250331",
            "use_labels": False,
        }

    def test_cli_values_override_profile_for_evaluate(
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
            tf="1D",
            label="label_20",
            capital=50_000.0,
            risk=0.5,
            commission=0.05,
            tp=3.0,
            sl=0.8,
            slippage=0.2,
            eval_start="20260101",
            eval_end="20260131",
            use_labels=True,
        )

        resolved = cli_module._resolve_evaluate_command_config(args)

        assert resolved == {
            "symbol": "EURUSD",
            "tf": "1D",
            "label": "label_20",
            "capital": 50_000.0,
            "risk": 0.5,
            "commission": 0.05,
            "tp": 3.0,
            "sl": 0.8,
            "slippage": 0.2,
            "eval_start": "20260101",
            "eval_end": "20260131",
            "use_labels": True,
        }
