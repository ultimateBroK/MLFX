"""Tests for CLI main dispatch flow and profiles command."""

from __future__ import annotations

import argparse
import importlib
import json
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
    cli = importlib.import_module("mlfx.cli.main")
    return importlib.reload(cli)


class TestMainDispatchFlow:
    def test_main_dispatches_run_all_command(self, monkeypatch, cli_module) -> None:
        parser = cli_module.build_parser()
        monkeypatch.setattr(
            parser,
            "parse_args",
            lambda: argparse.Namespace(
                command="run-all",
                profile="research",
                skip_download=False,
                skip_qa=False,
                skip_pipeline=False,
                skip_train=False,
                skip_evaluate=False,
                skip_benchmark=False,
                skip_serve=False,
                skip_batch=False,
                skip_drift_retrain=False,
                continue_on_error=False,
                json=True,
            ),
        )
        monkeypatch.setattr(cli_module, "build_parser", lambda: parser)

        captured = {}

        def _fake_run_all(args):
            captured["args"] = args
            return []

        monkeypatch.setattr(cli_module, "_run_all_command", _fake_run_all)
        monkeypatch.setattr(cli_module, "_persist_cli_workflow", lambda *args, **kwargs: None)

        cli_module.main()

        args = captured["args"]
        assert args.profile == "research"
        assert args.skip_download is False
        assert args.skip_drift_retrain is False
        assert args.continue_on_error is False
        assert args.json is True

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
            "mlfx.cli.workflows.resolve_train_command_config",
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
            "mlfx.cli.workflows.resolve_evaluate_command_config",
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
        monkeypatch.setattr("mlfx.cli.workflows.print_resolved_train_summary", lambda **kwargs: None)
        monkeypatch.setattr("mlfx.cli.workflows.print_resolved_evaluate_summary", lambda **kwargs: None)
        monkeypatch.setattr(
            "mlfx.cli.workflows.run_training",
            lambda config: {"artifact_path": "outputs/models/fake.pkl", "best_cv_f1_macro": 0.61},
        )
        monkeypatch.setattr(
            "mlfx.cli.workflows.run_model_backtest",
            lambda **kwargs: {"Net Profit (R)": "12.0R", "Sharpe": "1.20"},
        )
        monkeypatch.setattr("mlfx.cli.workflows.run_full_eval", lambda **kwargs: {"Net Profit (R)": "8.0R"})
        monkeypatch.setattr("mlfx.cli.workflows.get_baseline_metrics", lambda **kwargs: {"total_r": 10.0})
        monkeypatch.setattr(
            "mlfx.cli.workflows.run_benchmark",
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
            "mlfx.cli.resolve.load_config",
            lambda: SimpleNamespace(
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
                )
            ),
        )
        monkeypatch.setattr(
            "mlfx.cli.resolve.resolve_profile_section",
            lambda cfg, profile_name, section: {
                "symbol": "XAUUSD",
                "tf": "1H",
                "label": "label_10",
                "backend": "mlf",
                "n_trials": 5,
                "n_splits": 3,
                "train_start": "20240101",
                "train_end": "20241231",
                "force": True,
            },
        )
        monkeypatch.setattr("mlfx.cli.render.print_resolved_train_summary", lambda **kwargs: None)
        monkeypatch.setattr(cli_module, "_persist_cli_workflow", lambda *args, **kwargs: None)

        captured = {}

        def _fake_run_train(config):
            from mlfx.workflow.results import StageResult

            captured["config"] = config
            return StageResult(stage="train", status="ok", metrics={"artifact_path": "fake.pkl"})

        monkeypatch.setattr(cli_module, "run_train", _fake_run_train)

        cli_module.main()

        cfg = captured["config"]
        assert cfg.symbol == "XAUUSD"
        assert cfg.tf == "1H"
        assert cfg.label == "label_10"
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
