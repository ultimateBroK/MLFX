from __future__ import annotations

from pathlib import Path


def test_runner_registers_artifact_path(monkeypatch, tmp_path: Path):
    from mlfx.training.config import TrainingConfig
    from mlfx.training.runner import run_training

    captured: dict[str, object] = {}

    def _fake_runner(**_: object) -> dict[str, object]:
        return {
            "best_cv_f1_macro": 0.42,
            "artifact_path": str(tmp_path / "artifact.pkl"),
            "selected_features": ["f1", "f2"],
        }

    class _FakeRegistry:
        def register(self, **kwargs: object) -> dict[str, object]:
            captured.update(kwargs)
            return kwargs

    monkeypatch.setattr("mlfx.training.runner.get_backend_runner", lambda backend: _fake_runner)
    monkeypatch.setattr("mlfx.registry.models.get_registry", lambda: _FakeRegistry())

    cfg = TrainingConfig(symbol="XAUUSD", tf="1H", label_col="label_10", backend="mlf")
    metrics = run_training(cfg, enable_tracking=False, enable_registry=True)

    assert "elapsed_seconds" in metrics
    assert captured["artifact_path"] == str(tmp_path / "artifact.pkl")
    assert captured["backend"] == "mlf"
