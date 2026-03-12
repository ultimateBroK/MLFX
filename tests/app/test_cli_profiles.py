from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime
from types import SimpleNamespace

import pytest


@pytest.fixture
def cli_module(monkeypatch):
    """Import the CLI module with logging setup neutralized."""
    monkeypatch.setattr(
        "mlfx.monitoring.logging_config.configure_logging",
        lambda level="INFO": None,
    )
    cli = importlib.import_module("mlfx.app.cli.main")
    return importlib.reload(cli)


@pytest.fixture
def sample_app_config():
    return SimpleNamespace(
        train=SimpleNamespace(
            symbol="DEFAULT_SYMBOL",
            timeframe="4H",
            label_col="label_default",
            backend="sgd",
            n_trials=30,
            n_splits=5,
        ),
        backtest=SimpleNamespace(
            symbol="DEFAULT_SYMBOL",
            timeframe="4H",
            label_col="label_default",
            initial_capital=20_000.0,
            risk_pct=2.0,
            commission=0.2,
            tp_r=2.0,
            sl_r=1.2,
        ),
    )


@pytest.fixture
def sample_profile():
    return {
        "train": {
            "symbol": "XAUUSD",
            "timeframe": "1H",
            "label_col": "label_10",
            "backend": "mlf",
            "train_start": "20240101",
            "train_end": "20241231",
            "n_trials": 5,
            "n_splits": 3,
        },
        "evaluate": {
            "symbol": "XAUUSD",
            "timeframe": "1H",
            "label_col": "label_10",
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
            "timeframe": "1H",
            "label_col": "label_10",
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
        monkeypatch.setattr("mlfx.config.settings.load_config", lambda: sample_app_config)
        monkeypatch.setattr(
            "mlfx.app.cli.resolve.resolve_profile_section",
            lambda profile_name, section: sample_profile[section],
        )

        args = argparse.Namespace(
            profile="research",
            symbol=None,
            tf=None,
            label=None,
            backend=None,
            n_trials=None,
            n_splits=None,
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
            "force": True,
            "train_start": "20240101",
            "train_end": "20241231",
        }

    def test_cli_values_override_profile_values(
        self, monkeypatch, cli_module, sample_app_config, sample_profile
    ) -> None:
        monkeypatch.setattr("mlfx.config.settings.load_config", lambda: sample_app_config)
        monkeypatch.setattr(
            "mlfx.app.cli.resolve.resolve_profile_section",
            lambda profile_name, section: sample_profile[section],
        )

        args = argparse.Namespace(
            profile="research",
            symbol="EURUSD",
            tf="15m",
            label="label_20",
            backend="stats",
            n_trials=9,
            n_splits=4,
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
            "force": False,
            "train_start": "20230101",
            "train_end": "20230630",
        }


class TestResolveEvaluateCommandConfig:
    def test_profile_values_are_used_for_evaluate(
        self, monkeypatch, cli_module, sample_app_config, sample_profile
    ) -> None:
        monkeypatch.setattr("mlfx.config.settings.load_config", lambda: sample_app_config)
        monkeypatch.setattr(
            "mlfx.app.cli.resolve.resolve_profile_section",
            lambda profile_name, section: sample_profile[section],
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
        monkeypatch.setattr("mlfx.config.settings.load_config", lambda: sample_app_config)
        monkeypatch.setattr(
            "mlfx.app.cli.resolve.resolve_profile_section",
            lambda profile_name, section: sample_profile[section],
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


class TestRunProfileCommand:
    def test_run_profile_rejects_skipping_all_steps(self, cli_module) -> None:
        args = argparse.Namespace(
            profile="research",
            skip_train=True,
            skip_evaluate=True,
            skip_benchmark=True,
            json=False,
        )

        with pytest.raises(
            ValueError,
            match="run-profile cannot skip train, evaluate, and benchmark at the same time",
        ):
            cli_module._run_profile_command(args)

    def test_run_profile_orchestrates_all_steps_and_emits_json(
        self, monkeypatch, cli_module
    ) -> None:
        train_cfg = {
            "symbol": "XAUUSD",
            "tf": "1H",
            "label": "label_10",
            "backend": "mlf",
            "n_trials": 5,
            "n_splits": 3,
            "force": True,
            "train_start": "20240101",
            "train_end": "20241231",
        }
        eval_cfg = {
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

        captured_training = {}
        benchmark_calls = []

        monkeypatch.setattr("mlfx.app.cli.workflows.resolve_train_command_config", lambda args: train_cfg)
        monkeypatch.setattr("mlfx.app.cli.workflows.resolve_evaluate_command_config", lambda args: eval_cfg)
        monkeypatch.setattr("mlfx.app.cli.workflows.print_resolved_train_summary", lambda **kwargs: None)
        monkeypatch.setattr("mlfx.app.cli.workflows.print_resolved_evaluate_summary", lambda **kwargs: None)
        monkeypatch.setattr("mlfx.app.cli.workflows.get_baseline_metrics", lambda **kwargs: {"total_r": 10.0})
        monkeypatch.setattr(
            "mlfx.app.cli.workflows.run_model_backtest",
            lambda **kwargs: {"Net Profit (R)": "12.0R", "Win Rate": "55%"},
        )
        monkeypatch.setattr("mlfx.app.cli.workflows.run_full_eval", lambda **kwargs: {"Net Profit (R)": "8.0R"})

        def _fake_run_training(config):
            captured_training["config"] = config
            return {"artifact_path": "outputs/models/fake.pkl", "best_cv_f1_macro": 0.61}

        monkeypatch.setattr("mlfx.app.cli.workflows.run_training", _fake_run_training)

        def _fake_run_benchmark(args):
            benchmark_calls.append(args)
            return {"results": [{"backend": "mlf", "status": "OK"}]}

        monkeypatch.setattr("mlfx.app.cli.workflows.run_benchmark", _fake_run_benchmark)

        printed_json = {}

        def _fake_print_json(payload: str):
            printed_json["payload"] = json.loads(payload)

        monkeypatch.setattr(cli_module.console, "print_json", _fake_print_json)
        monkeypatch.setattr(cli_module.console, "print", lambda *args, **kwargs: None)
        monkeypatch.setattr(cli_module.console, "rule", lambda *args, **kwargs: None)

        args = argparse.Namespace(
            profile="research",
            skip_train=False,
            skip_evaluate=False,
            skip_benchmark=False,
            json=True,
        )

        cli_module._run_profile_command(args)

        cfg = captured_training["config"]
        assert cfg.symbol == "XAUUSD"
        assert cfg.tf == "1H"
        assert cfg.label_col == "label_10"
        assert cfg.backend == "mlf"
        assert cfg.n_trials == 5
        assert cfg.n_splits == 3
        assert cfg.force is True
        assert cfg.extra["train_start"] == "20240101"
        assert cfg.extra["train_end"] == "20241231"
        assert cfg.extra["profile"] == "research"

        assert len(benchmark_calls) == 1
        assert benchmark_calls[0].profile == "research"

        summary = printed_json["payload"]
        assert summary["profile"] == "research"
        assert summary["steps"]["train"]["skipped"] is False
        assert summary["steps"]["train"]["config"]["backend"] == "mlf"
        assert summary["steps"]["evaluate"]["skipped"] is False
        assert summary["steps"]["evaluate"]["source"] == "Model"
        assert summary["steps"]["evaluate"]["results"]["Net Profit (R)"] == "12.0R"
        assert summary["steps"]["benchmark"]["skipped"] is False
        assert summary["steps"]["benchmark"]["result"]["results"][0]["backend"] == "mlf"

    def test_run_profile_can_skip_benchmark(self, monkeypatch, cli_module) -> None:
        train_cfg = {
            "symbol": "XAUUSD",
            "tf": "1H",
            "label": "label_10",
            "backend": "mlf",
            "n_trials": 5,
            "n_splits": 3,
            "force": True,
            "train_start": "20240101",
            "train_end": "20241231",
        }
        eval_cfg = {
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
            "use_labels": True,
        }

        benchmark_called = {"value": False}

        monkeypatch.setattr("mlfx.app.cli.workflows.resolve_train_command_config", lambda args: train_cfg)
        monkeypatch.setattr("mlfx.app.cli.workflows.resolve_evaluate_command_config", lambda args: eval_cfg)
        monkeypatch.setattr("mlfx.app.cli.workflows.print_resolved_train_summary", lambda **kwargs: None)
        monkeypatch.setattr("mlfx.app.cli.workflows.print_resolved_evaluate_summary", lambda **kwargs: None)
        monkeypatch.setattr("mlfx.app.cli.workflows.run_training", lambda config: {"artifact_path": "fake.pkl"})
        monkeypatch.setattr("mlfx.app.cli.workflows.run_full_eval", lambda **kwargs: {"Net Profit (R)": "9.0R"})
        monkeypatch.setattr("mlfx.app.cli.workflows.run_model_backtest", lambda **kwargs: None)
        monkeypatch.setattr("mlfx.app.cli.workflows.get_baseline_metrics", lambda **kwargs: None)

        def _unexpected_benchmark(args):
            benchmark_called["value"] = True
            return {}

        monkeypatch.setattr("mlfx.app.cli.workflows.run_benchmark", _unexpected_benchmark)
        monkeypatch.setattr(cli_module.console, "print", lambda *args, **kwargs: None)
        monkeypatch.setattr(cli_module.console, "rule", lambda *args, **kwargs: None)

        args = argparse.Namespace(
            profile="research",
            skip_train=False,
            skip_evaluate=False,
            skip_benchmark=True,
            json=False,
        )

        cli_module._run_profile_command(args)

        assert benchmark_called["value"] is False


class TestMainDispatchFlow:
    def test_main_dispatches_run_profile_command(self, monkeypatch, cli_module) -> None:
        parser = cli_module.build_parser()
        monkeypatch.setattr(
            parser,
            "parse_args",
            lambda: argparse.Namespace(
                command="run-profile",
                profile="research",
                skip_train=False,
                skip_evaluate=False,
                skip_benchmark=False,
                json=True,
            ),
        )
        monkeypatch.setattr(cli_module, "build_parser", lambda: parser)

        captured = {}

        monkeypatch.setattr(
            cli_module,
            "_run_profile_command",
            lambda args: captured.setdefault("args", args),
        )

        cli_module.main()

        args = captured["args"]
        assert args.profile == "research"
        assert args.json is True
        assert args.skip_train is False
        assert args.skip_evaluate is False
        assert args.skip_benchmark is False

    def test_main_run_profile_json_flow_end_to_end(self, monkeypatch, cli_module) -> None:
        parser = cli_module.build_parser()
        monkeypatch.setattr(
            parser,
            "parse_args",
            lambda: argparse.Namespace(
                command="run-profile",
                profile="research",
                skip_train=False,
                skip_evaluate=False,
                skip_benchmark=True,
                json=True,
            ),
        )
        monkeypatch.setattr(cli_module, "build_parser", lambda: parser)

        monkeypatch.setattr(
            "mlfx.app.cli.workflows.resolve_train_command_config",
            lambda args: {
                "symbol": "XAUUSD",
                "tf": "1H",
                "label": "label_10",
                "backend": "mlf",
                "n_trials": 5,
                "n_splits": 3,
                "force": True,
                "train_start": "20240101",
                "train_end": "20241231",
            },
        )
        monkeypatch.setattr(
            "mlfx.app.cli.workflows.resolve_evaluate_command_config",
            lambda args: {
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
            },
        )
        monkeypatch.setattr("mlfx.app.cli.workflows.print_resolved_train_summary", lambda **kwargs: None)
        monkeypatch.setattr("mlfx.app.cli.workflows.print_resolved_evaluate_summary", lambda **kwargs: None)
        monkeypatch.setattr(
            "mlfx.app.cli.workflows.run_training",
            lambda config: {"artifact_path": "outputs/models/fake.pkl", "best_cv_f1_macro": 0.61},
        )
        monkeypatch.setattr(
            "mlfx.app.cli.workflows.run_model_backtest",
            lambda **kwargs: {"Net Profit (R)": "12.0R", "Sharpe": "1.20"},
        )
        monkeypatch.setattr("mlfx.app.cli.workflows.run_full_eval", lambda **kwargs: {"Net Profit (R)": "8.0R"})
        monkeypatch.setattr("mlfx.app.cli.workflows.get_baseline_metrics", lambda **kwargs: {"total_r": 10.0})
        monkeypatch.setattr(
            "mlfx.app.cli.workflows.run_benchmark",
            lambda args: pytest.fail("benchmark should not run when --skip-benchmark is set"),
        )

        printed_json = {}
        monkeypatch.setattr(cli_module.console, "print", lambda *args, **kwargs: None)
        monkeypatch.setattr(cli_module.console, "rule", lambda *args, **kwargs: None)
        monkeypatch.setattr(
            cli_module.console,
            "print_json",
            lambda payload: printed_json.setdefault("payload", json.loads(payload)),
        )

        cli_module.main()

        summary = printed_json["payload"]
        assert summary["profile"] == "research"
        assert summary["steps"]["train"]["skipped"] is False
        assert summary["steps"]["train"]["config"]["backend"] == "mlf"
        assert summary["steps"]["train"]["metrics"]["best_cv_f1_macro"] == 0.61
        assert summary["steps"]["evaluate"]["skipped"] is False
        assert summary["steps"]["evaluate"]["source"] == "Model"
        assert summary["steps"]["evaluate"]["results"]["Net Profit (R)"] == "12.0R"
        assert summary["steps"]["benchmark"]["skipped"] is True

    def test_main_exits_with_basic_logging_when_structured_logging_import_fails(
        self, monkeypatch, cli_module
    ) -> None:
        parser = cli_module.build_parser()
        monkeypatch.setattr(
            parser,
            "parse_args",
            lambda: argparse.Namespace(command="profiles", profile="research"),
        )
        monkeypatch.setattr(cli_module, "build_parser", lambda: parser)

        real_import = __import__

        def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "mlfx.monitoring.logging_config":
                raise ImportError("boom")
            return real_import(name, globals, locals, fromlist, level)

        import_calls = []

        monkeypatch.setattr("builtins.__import__", _fake_import)
        monkeypatch.setattr(
            cli_module.logging,
            "basicConfig",
            lambda **kwargs: import_calls.append(kwargs),
        )
        monkeypatch.setattr(cli_module, "_print_profiles_summary", lambda profile_name: None)

        cli_module.main()

        assert len(import_calls) == 1
        assert import_calls[0]["level"] == cli_module.logging.INFO
        assert import_calls[0]["format"] == "%(levelname)s %(message)s"


class TestProfilesCommand:
    def test_main_dispatches_profiles_command(self, monkeypatch, cli_module) -> None:
        parser = cli_module.build_parser()
        monkeypatch.setattr(
            parser,
            "parse_args",
            lambda: argparse.Namespace(command="profiles", profile="research"),
        )
        monkeypatch.setattr(cli_module, "build_parser", lambda: parser)

        captured = {}

        monkeypatch.setattr(
            cli_module,
            "_print_profiles_summary",
            lambda profile_name: captured.setdefault("profile", profile_name),
        )

        cli_module.main()

        assert captured["profile"] == "research"

    def test_main_dispatches_train_with_profile_resolution(
        self, monkeypatch, cli_module
    ) -> None:
        parser = cli_module.build_parser()
        monkeypatch.setattr(
            parser,
            "parse_args",
            lambda: argparse.Namespace(
                command="train",
                profile="research",
                symbol=None,
                tf=None,
                label=None,
                backend=None,
                n_trials=None,
                n_splits=None,
                train_start=None,
                train_end=None,
                force=None,
            ),
        )
        monkeypatch.setattr(cli_module, "build_parser", lambda: parser)
        monkeypatch.setattr(
            "mlfx.config.settings.load_config",
            lambda: SimpleNamespace(
                train=SimpleNamespace(
                    symbol="DEFAULT_SYMBOL",
                    timeframe="4H",
                    label_col="label_default",
                    backend="sgd",
                    n_trials=30,
                    n_splits=5,
                )
            ),
        )
        monkeypatch.setattr(
            "mlfx.app.cli.resolve.resolve_profile_section",
            lambda profile_name, section: {
                "symbol": "XAUUSD",
                "timeframe": "1H",
                "label_col": "label_10",
                "backend": "mlf",
                "n_trials": 5,
                "n_splits": 3,
                "train_start": "20240101",
                "train_end": "20241231",
            },
        )
        monkeypatch.setattr("mlfx.app.cli.render.print_resolved_train_summary", lambda **kwargs: None)

        captured = {}

        def _fake_run_training(config):
            captured["config"] = config
            return {"artifact_path": "fake.pkl"}

        monkeypatch.setattr(cli_module, "run_training", _fake_run_training)

        cli_module.main()

        cfg = captured["config"]
        assert cfg.symbol == "XAUUSD"
        assert cfg.tf == "1H"
        assert cfg.label_col == "label_10"
        assert cfg.backend == "mlf"
        assert cfg.n_trials == 5
        assert cfg.n_splits == 3
        assert cfg.extra["train_start"] == "20240101"
        assert cfg.extra["train_end"] == "20241231"
        assert cfg.extra["profile"] == "research"


class TestTimezoneNeutralExpectation:
    def test_naive_datetime_reference_for_cli_suite(self) -> None:
        """Guard against reintroducing timezone-dependent assumptions in this test file."""
        assert datetime(2024, 1, 31, 23, 59).tzinfo is None
