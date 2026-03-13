"""
tests/test_project_contract.py
================================
Contract tests for the new `mlfx` package structure.
"""

from __future__ import annotations

import re
import tomllib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl
import pytest


class TestProjectPaths:
    def test_default_layout_matches_current_repo_convention(self, tmp_path: Path):
        from mlfx.config.paths import ProjectPaths

        paths = ProjectPaths(project_root=tmp_path)

        assert paths.config_file == tmp_path / "config.toml"
        assert paths.raw_data_dir("XAUUSD") == tmp_path / "data" / "raw" / "XAUUSD"
        assert paths.ohlcv_dir("XAUUSD", "1H") == tmp_path / "data" / "ohlcv" / "XAUUSD" / "1H"
        assert (
            paths.features_dir("XAUUSD", "1H")
            == tmp_path / "data" / "features" / "XAUUSD" / "1H"
        )
        assert (
            paths.labels_dir("XAUUSD", "1H")
            == tmp_path / "data" / "labels" / "XAUUSD" / "1H"
        )
        assert (
            paths.models_dir("XAUUSD", "1H")
            == tmp_path / "outputs" / "models" / "XAUUSD" / "1H"
        )
        assert paths.reports_root == tmp_path / "outputs" / "reports"
        assert paths.runs_root == tmp_path / "outputs" / "runs"
        assert paths.predictions_root == tmp_path / "outputs" / "predictions"
        assert paths.monitoring_root == tmp_path / "outputs" / "monitoring"

        assert (
            paths.reports_dir("XAUUSD", "1H")
            == tmp_path / "outputs" / "reports" / "XAUUSD" / "1H"
        )
        assert (
            paths.runs_dir("XAUUSD", "1H")
            == tmp_path / "outputs" / "runs" / "XAUUSD" / "1H"
        )
        assert (
            paths.predictions_dir("XAUUSD", "1H")
            == tmp_path / "outputs" / "predictions" / "XAUUSD" / "1H"
        )
        assert (
            paths.monitoring_dir("XAUUSD", "1H")
            == tmp_path / "outputs" / "monitoring" / "XAUUSD" / "1H"
        )
        assert paths.lightning_logs_dir == tmp_path / "lightning_logs"

    def test_nested_artifact_layout_helpers(self, tmp_path: Path):
        from mlfx.config.paths import ProjectPaths

        paths = ProjectPaths(project_root=tmp_path)

        assert (
            paths.models_label_dir("XAUUSD", "1H", "label_10")
            == tmp_path / "outputs" / "models" / "XAUUSD" / "1H" / "label_10"
        )
        assert (
            paths.report_run_dir("XAUUSD", "1H", "label_10", "model", "R15")
            == tmp_path
            / "outputs"
            / "reports"
            / "XAUUSD"
            / "1H"
            / "label_10"
            / "model"
            / "R15"
        )
        assert (
            paths.report_run_dir("XAUUSD", "1H", "label_10", "labels", "R15")
            == tmp_path
            / "outputs"
            / "reports"
            / "XAUUSD"
            / "1H"
            / "label_10"
            / "labels"
            / "R15"
        )
        assert (
            paths.predictions_label_dir("XAUUSD", "1H", "label_10")
            == tmp_path / "outputs" / "predictions" / "XAUUSD" / "1H" / "label_10"
        )
        assert (
            paths.runs_label_dir("XAUUSD", "1H", "label_10")
            == tmp_path / "outputs" / "runs" / "XAUUSD" / "1H" / "label_10"
        )


class TestSettingsLoader:
    def test_load_config_merges_file_over_defaults(self, tmp_path: Path):
        from mlfx.config.settings import load_config

        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[download]
symbol = "BTCUSD"

[train]
backend = "stats"
n_splits = 3
""".strip()
        )

        config = load_config(config_file)

        assert config.download.symbol == "BTCUSD"
        assert config.train.backend == "stats"
        assert config.train.n_splits == 3
        assert config.pipeline.tf == ["1H"]


class TestBackendRegistry:
    def test_registry_contains_all_backends(self):
        from mlfx.training.registry import BACKEND_REGISTRY

        expected = {"mlf", "lstm", "sgd", "stats"}
        assert expected.issubset(BACKEND_REGISTRY.keys())

    def test_unknown_backend_raises_clear_error(self):
        from mlfx.training.registry import get_backend_runner

        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend_runner("missing")


class TestPackageBoundaries:
    def test_mlfx_has_no_reverse_imports_to_legacy_tree(self):
        repo_root = Path(__file__).resolve().parents[1]
        mlfx_root = repo_root / "mlfx"
        legacy_import_pattern = re.compile(
            r"^\s*(from|import)\s+(pipeline|models|eval|indicators|viz)\b",
            re.MULTILINE,
        )

        offenders: list[str] = []
        for path in mlfx_root.rglob("*.py"):
            source = path.read_text()
            if legacy_import_pattern.search(source):
                offenders.append(str(path.relative_to(repo_root)))

        assert offenders == []

    def test_wheel_only_packages_mlfx_namespace(self):
        repo_root = Path(__file__).resolve().parents[1]
        pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text())
        packages = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
        assert packages == ["mlfx"]


class TestEvaluationRunner:
    def test_load_labelled_dataset_combines_and_sorts_month_files(self, tmp_path: Path):
        from mlfx.config.paths import ProjectPaths
        from mlfx.evaluation.runner import load_labelled_dataset

        paths = ProjectPaths(project_root=tmp_path)
        labels_dir = paths.labels_dir("XAUUSD", "1H")
        labels_dir.mkdir(parents=True, exist_ok=True)

        later = datetime(2024, 1, 2, 0, tzinfo=timezone.utc)
        earlier = datetime(2024, 1, 1, 0, tzinfo=timezone.utc)

        pl.DataFrame(
            {
                "timestamp": [later + timedelta(hours=i) for i in range(2)],
                "close": [2025.0, 2026.0],
                "label_10": [1, 0],
            }
        ).write_parquet(labels_dir / "2024-02.parquet")
        pl.DataFrame(
            {
                "timestamp": [earlier + timedelta(hours=i) for i in range(2)],
                "close": [2020.0, 2021.0],
                "label_10": [0, 1],
            }
        ).write_parquet(labels_dir / "2024-01.parquet")

        df = load_labelled_dataset("XAUUSD", "1H", paths=paths)

        assert df is not None
        assert df["timestamp"].to_list() == sorted(df["timestamp"].to_list())
        assert len(df) == 4
