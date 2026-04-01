"""Tracking system integration tests for training orchestrator.

Validates:
- _start_tracking_run() and _end_tracking_run() functions (lines 116-157 in runner.py)
- Graceful degradation when tracking starts fails (CRITICAL: end should not be called)
- Failed training status tracking (status=FAILED)
- Tracking can be disabled via enable_tracking=False
- Metrics filtering for logging (only float/int types)
"""

from __future__ import annotations

from typing import Any

import pytest

from mlfx.training.config import TrainingConfig


def test_run_training_calls_tracking_lifecycle(monkeypatch):
    """Test that successful training calls start_tracking -> backend -> end_tracking."""
    from mlfx.training.runner import run_training

    tracking_calls: dict[str, list[Any]] = {"start": [], "end": []}

    def _fake_start_tracking(config: TrainingConfig) -> str | None:
        tracking_calls["start"].append(config.backend)
        return "run_id_123"

    def _fake_end_tracking(run_id: str, status: str, metrics: dict[str, Any], config: TrainingConfig) -> None:
        tracking_calls["end"].append({"run_id": run_id, "status": status, "config": config.backend})

    def _fake_runner(**_: Any) -> dict[str, Any]:
        return {
            "best_cv_f1_macro": 0.42,
            "artifact_path": "/tmp/model.pkl",
        }

    monkeypatch.setattr("mlfx.training.runner._start_tracking_run", _fake_start_tracking)
    monkeypatch.setattr("mlfx.training.runner._end_tracking_run", _fake_end_tracking)
    monkeypatch.setattr("mlfx.training.runner.get_backend_runner", lambda backend: _fake_runner)
    monkeypatch.setattr("mlfx.training.runner.get_runner_kwargs", lambda config: {})
    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: None)

    cfg = TrainingConfig(symbol="XAUUSD", tf="1H", backend="mlf", label="label_10")
    metrics = run_training(cfg, enable_tracking=True, enable_registry=False)

    # Verify start_tracking called
    assert len(tracking_calls["start"]) == 1
    assert tracking_calls["start"][0] == "mlf"

    # Verify end_tracking called with status=FINISHED
    assert len(tracking_calls["end"]) == 1
    assert tracking_calls["end"][0]["run_id"] == "run_id_123"
    assert tracking_calls["end"][0]["status"] == "FINISHED"
    assert tracking_calls["end"][0]["config"] == "mlf"

    # Verify metrics were returned
    assert "elapsed_seconds" in metrics


def test_run_training_skip_tracking_when_disabled(monkeypatch):
    """Test that enable_tracking=False skips all tracking calls."""
    from mlfx.training.runner import run_training

    tracking_calls: dict[str, list[Any]] = {"start": [], "end": []}

    def _fake_start_tracking(config: TrainingConfig) -> str | None:
        tracking_calls["start"].append(config.backend)
        raise AssertionError("Should not be called when enable_tracking=False")

    def _fake_end_tracking(run_id: str, status: str, metrics: dict[str, Any], config: TrainingConfig) -> None:
        tracking_calls["end"].append({"run_id": run_id, "status": status})
        raise AssertionError("Should not be called when enable_tracking=False")

    def _fake_runner(**_: Any) -> dict[str, Any]:
        return {
            "best_cv_f1_macro": 0.42,
            "artifact_path": "/tmp/model.pkl",
        }

    monkeypatch.setattr("mlfx.training.runner._start_tracking_run", _fake_start_tracking)
    monkeypatch.setattr("mlfx.training.runner._end_tracking_run", _fake_end_tracking)
    monkeypatch.setattr("mlfx.training.runner.get_backend_runner", lambda backend: _fake_runner)
    monkeypatch.setattr("mlfx.training.runner.get_runner_kwargs", lambda config: {})
    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: None)

    cfg = TrainingConfig(symbol="XAUUSD", tf="1H", backend="mlf", label="label_10")

    # Should not raise the AssertionError from tracking functions
    metrics = run_training(cfg, enable_tracking=False, enable_registry=False)

    # Verify no tracking calls were made
    assert len(tracking_calls["start"]) == 0
    assert len(tracking_calls["end"]) == 0

    # Verify training still completed
    assert "elapsed_seconds" in metrics
    assert metrics["best_cv_f1_macro"] == 0.42


def test_run_training_graceful_degradation_start_tracking_fails(monkeypatch):
    """CRITICAL: Test that if start_tracking fails, training continues and end_tracking is NOT called.
    
    This validates the guard condition: if run_id is None, don't call _end_tracking_run.
    """
    from mlfx.training.runner import run_training

    tracking_calls: dict[str, list[Any]] = {"start": [], "end": []}

    def _fake_start_tracking(config: TrainingConfig) -> str | None:
        tracking_calls["start"].append(config.backend)
        return None  # Graceful degradation: return None instead of raising

    def _fake_end_tracking(run_id: str, status: str, metrics: dict[str, Any], config: TrainingConfig) -> None:
        tracking_calls["end"].append({"run_id": run_id, "status": status})
        raise AssertionError("end_tracking should NOT be called if start_tracking returned None")

    def _fake_runner(**_: Any) -> dict[str, Any]:
        return {
            "best_cv_f1_macro": 0.42,
            "artifact_path": "/tmp/model.pkl",
        }

    monkeypatch.setattr("mlfx.training.runner._start_tracking_run", _fake_start_tracking)
    monkeypatch.setattr("mlfx.training.runner._end_tracking_run", _fake_end_tracking)
    monkeypatch.setattr("mlfx.training.runner.get_backend_runner", lambda backend: _fake_runner)
    monkeypatch.setattr("mlfx.training.runner.get_runner_kwargs", lambda config: {})
    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: None)

    cfg = TrainingConfig(symbol="XAUUSD", tf="1H", backend="mlf", label="label_10")

    # Should NOT raise the AssertionError from _end_tracking_run
    metrics = run_training(cfg, enable_tracking=True, enable_registry=False)

    # Verify start_tracking was called and returned None
    assert len(tracking_calls["start"]) == 1

    # CRITICAL: Verify end_tracking was NOT called (because run_id was None)
    assert len(tracking_calls["end"]) == 0

    # Verify training still completed successfully
    assert "elapsed_seconds" in metrics
    assert metrics["best_cv_f1_macro"] == 0.42


def test_run_training_tracks_failed_status_on_exception(monkeypatch):
    """Test that when backend raises exception, _end_tracking_run is called with status=FAILED.
    
    Validates: if run_id is not None but backend raises, end_tracking IS called with status=FAILED.
    """
    from mlfx.training.runner import run_training

    tracking_calls: dict[str, list[Any]] = {"start": [], "end": []}

    def _fake_start_tracking(config: TrainingConfig) -> str | None:
        tracking_calls["start"].append(config.backend)
        return "run_id_456"  # Tracking started successfully

    def _fake_end_tracking(run_id: str, status: str, metrics: dict[str, Any], config: TrainingConfig) -> None:
        tracking_calls["end"].append({
            "run_id": run_id,
            "status": status,
            "metrics": metrics,
            "config": config.backend,
        })

    def _fake_runner_fails(**_: Any) -> dict[str, Any]:
        raise ValueError("Training failed")

    monkeypatch.setattr("mlfx.training.runner._start_tracking_run", _fake_start_tracking)
    monkeypatch.setattr("mlfx.training.runner._end_tracking_run", _fake_end_tracking)
    monkeypatch.setattr("mlfx.training.runner.get_backend_runner", lambda backend: _fake_runner_fails)
    monkeypatch.setattr("mlfx.training.runner.get_runner_kwargs", lambda config: {})
    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: None)

    cfg = TrainingConfig(symbol="XAUUSD", tf="1H", backend="mlf", label="label_10")

    # Should raise ValueError, but before that should have called end_tracking with FAILED
    with pytest.raises(ValueError, match="Training failed"):
        run_training(cfg, enable_tracking=True, enable_registry=False)

    # Verify start_tracking was called
    assert len(tracking_calls["start"]) == 1

    # Verify end_tracking was called with status=FAILED and run_id
    assert len(tracking_calls["end"]) == 1
    assert tracking_calls["end"][0]["run_id"] == "run_id_456"
    assert tracking_calls["end"][0]["status"] == "FAILED"
    assert tracking_calls["end"][0]["metrics"] == {}  # Empty metrics on failure


def test_run_training_filters_metrics_for_logging(monkeypatch):
    """Test that end_tracking only receives numeric and string metrics.
    
    Validates: non-serializable types (arrays, objects) are filtered out.
    """
    from mlfx.training.runner import run_training

    tracking_metrics: list[dict[str, Any]] = []

    def _fake_start_tracking(config: TrainingConfig) -> str | None:
        return "run_id_789"

    def _fake_end_tracking(run_id: str, status: str, metrics: dict[str, Any], config: TrainingConfig) -> None:
        tracking_metrics.append(metrics)

    def _fake_runner(**_: Any) -> dict[str, Any]:
        import numpy as np

        return {
            "best_cv_f1_macro": 0.42,  # Should be included (float)
            "f1_macro_train": 1.0,  # Should be included (float)
            "n_samples": 100,  # Should be filtered out (filtered explicitly)
            "selected_features": ["f1", "f2"],  # Should be filtered (list)
            "history": np.array([1, 2, 3]),  # Should be filtered (numpy array)
            "artifact_path": "/tmp/model.pkl",  # Should be filtered (not in loggable check)
        }

    monkeypatch.setattr("mlfx.training.runner._start_tracking_run", _fake_start_tracking)
    monkeypatch.setattr("mlfx.training.runner._end_tracking_run", _fake_end_tracking)
    monkeypatch.setattr("mlfx.training.runner.get_backend_runner", lambda backend: _fake_runner)
    monkeypatch.setattr("mlfx.training.runner.get_runner_kwargs", lambda config: {})
    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: None)

    cfg = TrainingConfig(symbol="XAUUSD", tf="1H", backend="mlf", label="label_10")
    metrics = run_training(cfg, enable_tracking=True, enable_registry=False)

    # Verify what was passed to end_tracking (only numeric metrics, excluding n_samples)
    assert len(tracking_metrics) == 1
    logged_metrics = tracking_metrics[0]

    # These should be included
    assert "best_cv_f1_macro" in logged_metrics
    assert "f1_macro_train" in logged_metrics

    # These should be filtered out
    assert "n_samples" not in logged_metrics  # Explicitly excluded
    assert "selected_features" not in logged_metrics  # Not int/float
    assert "history" not in logged_metrics  # Not int/float
    assert "artifact_path" not in logged_metrics  # String type filtered out in loggable check
