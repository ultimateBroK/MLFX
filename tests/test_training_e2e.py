"""End-to-end integration tests for training orchestrator.

Validates:
- Data threading to DL backends (lines 68-72 in runner.py)
- Non-DL backend data exclusion (no prepare_tabular_data call)
- Graceful degradation for empty metrics and missing artifacts
- Registry integration with proper metrics capture
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mlfx.training.config import TrainingConfig


def test_run_training_dl_backend_threads_data(monkeypatch, tmp_path: Path):
    """Test that DL backends receive X, y, feature_cols via data threading."""
    from mlfx.training.runner import run_training

    # Track calls to prepare_tabular_data
    prepare_data_calls: list[tuple] = []

    def _fake_prepare_tabular_data(symbol: str, tf: str, label_col: str) -> tuple:
        prepare_data_calls.append((symbol, tf, label_col))
        import numpy as np

        X = np.random.randn(100, 10)
        y = np.random.randint(0, 2, 100)
        feature_cols = [f"f{i}" for i in range(10)]
        return X, y, feature_cols

    # Track kwargs passed to backend
    backend_calls: list[dict[str, Any]] = []

    def _fake_dl_runner(**kwargs: Any) -> dict[str, Any]:
        backend_calls.append(kwargs)
        return {
            "best_cv_f1_macro": 0.42,
            "artifact_path": str(tmp_path / "model.pkl"),
            "selected_features": ["f1", "f2"],
        }

    monkeypatch.setattr("mlfx.training.runner.get_backend_runner", lambda backend: _fake_dl_runner)
    monkeypatch.setattr(
        "mlfx.training.data.prepare_tabular_data",
        _fake_prepare_tabular_data,
    )
    monkeypatch.setattr("mlfx.training.runner.get_runner_kwargs", lambda config: {})
    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: None)

    cfg = TrainingConfig(symbol="XAUUSD", tf="1H", backend="lstm", label_col="label_10")
    metrics = run_training(cfg, enable_tracking=False, enable_registry=False)

    # Verify prepare_tabular_data was called with correct args
    assert len(prepare_data_calls) == 1
    assert prepare_data_calls[0] == ("XAUUSD", "1H", "label_10")

    # Verify backend received X, y, feature_cols
    assert len(backend_calls) == 1
    assert "X" in backend_calls[0]
    assert "y" in backend_calls[0]
    assert "feature_cols" in backend_calls[0]

    # Verify result includes elapsed_seconds
    assert "elapsed_seconds" in metrics
    assert metrics["best_cv_f1_macro"] == 0.42


def test_run_training_non_dl_backend_no_data_threading(monkeypatch):
    """Test that non-DL backends do NOT receive X, y, feature_cols."""
    from mlfx.training.runner import run_training

    # Track prepare_tabular_data calls
    prepare_calls: list[tuple] = []

    def _fake_prepare_tabular_data(symbol: str, tf: str, label_col: str) -> tuple:
        prepare_calls.append((symbol, tf, label_col))
        return None  # Should never be called for non-DL

    # Track what kwargs backend receives
    backend_calls: list[dict[str, Any]] = []

    def _fake_stats_runner(**kwargs: Any) -> dict[str, Any]:
        backend_calls.append(kwargs)
        return {
            "best_cv_f1_macro": 0.35,
            "artifact_path": "/tmp/model.pkl",
        }

    monkeypatch.setattr("mlfx.training.runner.get_backend_runner", lambda backend: _fake_stats_runner)
    monkeypatch.setattr(
        "mlfx.training.data.prepare_tabular_data",
        _fake_prepare_tabular_data,
    )
    monkeypatch.setattr("mlfx.training.runner.get_runner_kwargs", lambda config: {})
    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: None)

    cfg = TrainingConfig(symbol="XAUUSD", tf="1H", backend="stats", label_col="label_10")
    metrics = run_training(cfg, enable_tracking=False, enable_registry=False)

    # Verify prepare_tabular_data was NOT called (non-DL backend)
    assert len(prepare_calls) == 0

    # Verify backend did NOT receive X, y, feature_cols
    assert len(backend_calls) == 1
    assert "X" not in backend_calls[0]
    assert "y" not in backend_calls[0]
    assert "feature_cols" not in backend_calls[0]

    # Verify result is still valid
    assert "elapsed_seconds" in metrics
    assert metrics["best_cv_f1_macro"] == 0.35


def test_run_training_backend_returns_empty_metrics(monkeypatch):
    """Test graceful degradation when backend returns empty dict."""
    from mlfx.training.runner import run_training

    def _fake_runner(**_: Any) -> dict[str, Any]:
        return {}  # Empty metrics

    monkeypatch.setattr("mlfx.training.runner.get_backend_runner", lambda backend: _fake_runner)
    monkeypatch.setattr("mlfx.training.runner.get_runner_kwargs", lambda config: {})
    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: None)

    cfg = TrainingConfig(symbol="XAUUSD", tf="1H", backend="stats", label_col="label_10")
    metrics = run_training(cfg, enable_tracking=False, enable_registry=False)

    # Should still return elapsed_seconds even with empty backend result
    assert "elapsed_seconds" in metrics
    assert isinstance(metrics["elapsed_seconds"], float)
    assert len(metrics) == 1  # Only elapsed_seconds


def test_run_training_backend_returns_none(monkeypatch):
    """Test graceful degradation when backend returns None instead of dict."""
    from mlfx.training.runner import run_training

    def _fake_runner(**_: Any) -> Any:
        return None  # None instead of dict

    monkeypatch.setattr("mlfx.training.runner.get_backend_runner", lambda backend: _fake_runner)
    monkeypatch.setattr("mlfx.training.runner.get_runner_kwargs", lambda config: {})
    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: None)

    cfg = TrainingConfig(symbol="XAUUSD", tf="1H", backend="stats", label_col="label_10")
    metrics = run_training(cfg, enable_tracking=False, enable_registry=False)

    # Should gracefully convert None to empty dict (or {})
    assert "elapsed_seconds" in metrics
    assert isinstance(metrics["elapsed_seconds"], float)


def test_run_training_missing_artifact_path_logs_warning(monkeypatch, caplog):
    """Test that missing artifact_path doesn't crash but logs warning."""
    from mlfx.training.runner import run_training

    backend_ran = False

    def _fake_runner(**_: Any) -> dict[str, Any]:
        return {
            "best_cv_f1_macro": 0.42,
            # Note: no artifact_path
        }

    class _FakeRegistry:
        def register(self, **kwargs: Any) -> None:
            pass

    monkeypatch.setattr("mlfx.training.runner.get_backend_runner", lambda backend: _fake_runner)
    monkeypatch.setattr("mlfx.training.runner.get_runner_kwargs", lambda config: {})
    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: _FakeRegistry())

    cfg = TrainingConfig(symbol="XAUUSD", tf="1H", backend="stats", label_col="label_10")

    # Should not raise, but should log warning
    metrics = run_training(cfg, enable_tracking=False, enable_registry=True)

    # Verify warning was logged
    assert any("artifact_path" in record.message for record in caplog.records if record.levelname == "WARNING")
    assert metrics["best_cv_f1_macro"] == 0.42
