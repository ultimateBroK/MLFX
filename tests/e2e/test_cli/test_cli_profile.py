"""Tests for CLI run-profile command."""

from __future__ import annotations

import argparse
import importlib
import json
from types import SimpleNamespace

import pytest
from mlfx.workflow import StageResult


@pytest.fixture
def cli_module(monkeypatch):
    """Import the CLI module with logging setup neutralized."""
    monkeypatch.setattr(
        "mlfx.monitoring.logging_config.configure_logging",
        lambda level="INFO": None,
    )
    cli = importlib.import_module("mlfx.cli.main")
    return importlib.reload(cli)


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

        monkeypatch.setattr("mlfx.cli.resolve.resolve_train_command_config", lambda args: train_cfg)
        monkeypatch.setattr("mlfx.cli.resolve.resolve_evaluate_command_config", lambda args: eval_cfg)
        monkeypatch.setattr("mlfx.cli.render.print_resolved_train_summary", lambda **kwargs: None)
        monkeypatch.setattr("mlfx.cli.render.print_resolved_evaluate_summary", lambda **kwargs: None)

        def _fake_run_train(config):
            captured_training["config"] = config
            return StageResult(
                stage="train",
                status="ok",
                metrics={
                    "artifact_path": "outputs/models/fake.pkl",
                    "best_cv_f1_macro": 0.61,
                },
            )

        monkeypatch.setattr("mlfx.cli.handlers.train.run_train", _fake_run_train)
        monkeypatch.setattr(
            "mlfx.cli.handlers.evaluate.run_evaluate",
            lambda **kwargs: StageResult(
                stage="evaluate",
                status="ok",
                metrics={
                    "results": {"Net Profit (R)": "12.0R", "Win Rate": "55%"},
                    "source": "model",
                    "baseline": {"total_r": 10.0},
                },
            ),
        )

        def _fake_run_benchmark(args):
            benchmark_calls.append(args)
            return {"results": [{"backend": "mlf", "status": "OK"}]}

        monkeypatch.setattr("mlfx.workflow.orchestration.run_benchmark", _fake_run_benchmark)

        # Mock Path.write_text to capture JSON output
        import pathlib
        written_files = {}
        original_write_text = pathlib.Path.write_text
        def mock_write_text(self, content, encoding=None, errors=None):
            if "_summary.json" in str(self):
                written_files[str(self)] = content
            return original_write_text(self, content, encoding=encoding, errors=errors)
        monkeypatch.setattr(pathlib.Path, "write_text", mock_write_text)

        from mlfx.cli.render import console
        monkeypatch.setattr(console, "print", lambda *args, **kwargs: None)
        monkeypatch.setattr(console, "rule", lambda *args, **kwargs: None)

        args = argparse.Namespace(
            profile="research",
            skip_train=False,
            skip_evaluate=False,
            skip_benchmark=False,
            json=True,
            force=False,
        )

        cli_module._run_profile_command(args)

        cfg = captured_training["config"]
        assert cfg.symbol == "XAUUSD"
        assert cfg.tf == "1H"
        assert cfg.label == "label_10"
        assert cfg.backend == "mlf"
        assert cfg.n_trials == 5
        assert cfg.n_splits == 3
        assert cfg.force is True
        assert cfg.extra["train_start"] == "20240101"
        assert cfg.extra["train_end"] == "20241231"
        assert cfg.extra["profile"] == "research"

        assert len(benchmark_calls) == 1
        assert benchmark_calls[0].profile == "research"

        # Find the JSON file that was created
        assert len(written_files) == 1
        json_path = list(written_files.keys())[0]
        assert "_summary.json" in json_path
        summary = json.loads(written_files[json_path])

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

        monkeypatch.setattr("mlfx.cli.resolve.resolve_train_command_config", lambda args: train_cfg)
        monkeypatch.setattr("mlfx.cli.resolve.resolve_evaluate_command_config", lambda args: eval_cfg)
        monkeypatch.setattr("mlfx.cli.render.print_resolved_train_summary", lambda **kwargs: None)
        monkeypatch.setattr("mlfx.cli.render.print_resolved_evaluate_summary", lambda **kwargs: None)
        monkeypatch.setattr(
            "mlfx.cli.handlers.train.run_train",
            lambda config: StageResult(
                stage="train",
                status="ok",
                metrics={"artifact_path": "fake.pkl"},
            ),
        )
        monkeypatch.setattr(
            "mlfx.cli.handlers.evaluate.run_evaluate",
            lambda **kwargs: StageResult(
                stage="evaluate",
                status="ok",
                metrics={
                    "results": {"Net Profit (R)": "9.0R"},
                    "source": "labels",
                },
            ),
        )

        def _unexpected_benchmark(args):
            benchmark_called["value"] = True
            return {}

        monkeypatch.setattr("mlfx.workflow.orchestration.run_benchmark", _unexpected_benchmark)
        from mlfx.cli.render import console
        monkeypatch.setattr(console, "print", lambda *args, **kwargs: None)
        monkeypatch.setattr(console, "rule", lambda *args, **kwargs: None)

        args = argparse.Namespace(
            profile="research",
            skip_train=False,
            skip_evaluate=False,
            skip_benchmark=True,
            json=False,
            force=False,
        )

        cli_module._run_profile_command(args)

        assert benchmark_called["value"] is False
