"""Smoke tests for every training backend.

DL backends (LSTM)
------------------
Accept ``X``, ``y``, ``feature_cols`` directly, so no data-on-disk required.
We inject tiny synthetic arrays, patch ``build_model_output_path`` to write
artefacts into ``tmp_path``, and run with the smallest possible
hyperparameter budget (1 trial, 2 CV splits, 2 epochs).

Non-DL backends (Online-SGD, Stats, MLForecast)
----------------------------------------------
These load data internally.  The SGD backend gets a full smoke test by
patching ``prepare_tabular_data``.  The three Nixtla-based backends (Stats,
MLForecast) are tested only for their *null-data guard*: when
the data loader returns ``None`` the runner must return an empty dict without
raising.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from mlfx.training.backends.lstm import run_lstm
from mlfx.training.backends.mlf import run_ml_models
from mlfx.training.backends.sgd import run_online_sgd
from mlfx.training.backends.stats import run_stats

# ── Hyperparameter constants shared by all DL smoke tests ─────────────────────

_DL_KWARGS = dict(
    n_trials=1,
    n_splits=2,
    seq_len=10,
    epochs=2,
    batch_size=16,
    top_k_features=5,
    force=True,
    seed=42,
)


# ── DL backend smoke tests (parametrized) ─────────────────────────────────────


@pytest.mark.parametrize(
    "run_fn,module_path",
    [
        (run_lstm, "mlfx.training.backends.lstm"),
    ],
    ids=["lstm"],
)
def test_dl_backend_smoke(
    run_fn,
    module_path,
    fake_X: np.ndarray,
    fake_y: np.ndarray,
    fake_feature_cols: list[str],
    tmp_path,
    monkeypatch,
) -> None:
    """Each DL backend returns a non-empty metrics dict with artifact_path."""
    model_file = tmp_path / "model.pkl"
    monkeypatch.setattr(
        f"{module_path}.build_model_output_path",
        lambda *a, **kw: model_file,
    )

    result = run_fn(
        X=fake_X,
        y=fake_y,
        feature_cols=fake_feature_cols,
        **_DL_KWARGS,
    )

    assert isinstance(result, dict), "smoke: must return a dict"
    assert result, "smoke: dict must be non-empty"
    assert "artifact_path" in result, "smoke: 'artifact_path' key must be present"
    assert Path(result["artifact_path"]).exists(), "smoke: artifact_path must point to a real file"


# ── Online-SGD smoke test ──────────────────────────────────────────────────────


def test_online_sgd_smoke(
    fake_X: np.ndarray,
    fake_y: np.ndarray,
    fake_feature_cols: list[str],
    tmp_path,
    monkeypatch,
) -> None:
    """Online-SGD backend returns a non-empty metrics dict with artifact_path."""
    model_file = tmp_path / "sgd.pkl"
    monkeypatch.setattr(
        "mlfx.training.backends.sgd.prepare_tabular_data",
        lambda *a, **kw: (fake_X, fake_y, fake_feature_cols),
    )
    monkeypatch.setattr(
        "mlfx.training.backends.sgd.build_model_output_path",
        lambda *a, **kw: model_file,
    )

    result = run_online_sgd(batch_size=50, force=True, seed=42)

    assert isinstance(result, dict), "sgd smoke: must return a dict"
    assert result, "sgd smoke: dict must be non-empty"
    assert "artifact_path" in result, "sgd smoke: 'artifact_path' key must be present"
    assert Path(result["artifact_path"]).exists(), "sgd smoke: artifact_path must point to a real file"


# ── Null-data guard tests for Nixtla backends ─────────────────────────────────


@pytest.mark.parametrize(
    "run_fn,module_path",
    [
        (run_stats, "mlfx.training.backends.stats"),
        (run_ml_models, "mlfx.training.backends.mlf"),
    ],
    ids=["stats", "mlforecast"],
)
def test_backend_returns_empty_when_no_data(run_fn, module_path, monkeypatch) -> None:
    """Backends that load data internally must handle missing data gracefully."""
    monkeypatch.setattr(
        f"{module_path}.load_labelled_dataset",
        lambda *a, **kw: None,
    )
    result = run_fn()
    # Backend should either return empty dict or indicate it was skipped
    is_valid = result == {} or result.get("skipped") is True
    assert is_valid, f"{run_fn.__name__} must return {{}} or {{'skipped': True}} when data is None, got {result}"
