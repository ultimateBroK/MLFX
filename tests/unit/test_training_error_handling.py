"""Tests for boundary conditions and error paths in the training layer.

Covers:
  - ``create_sequences`` raises ``ValueError`` when dataset is too small
  - ``get_backend_runner`` raises ``ValueError`` for unknown backend key
    - LSTM backend returns ``{}`` when upstream data-loader returns ``None``
"""

from __future__ import annotations

import numpy as np
import pytest

from mlfx.training.backends._sequence_utils import create_sequences
from mlfx.training.backends.lstm import run_lstm
from mlfx.training.registry import get_backend_runner


# ── create_sequences ──────────────────────────────────────────────────────────


def test_create_sequences_raises_when_rows_lt_seq_len() -> None:
    """n_rows < seq_len must raise ValueError."""
    X = np.zeros((5, 3), dtype=np.float32)
    y = np.zeros(5, dtype=np.int64)
    with pytest.raises(ValueError, match="Dataset too small"):
        create_sequences(X, y, seq_len=10)


def test_create_sequences_raises_when_rows_equal_seq_len() -> None:
    """n_rows == seq_len is still too small (needs *strictly* more rows)."""
    X = np.zeros((10, 3), dtype=np.float32)
    y = np.zeros(10, dtype=np.int64)
    with pytest.raises(ValueError, match="Dataset too small"):
        create_sequences(X, y, seq_len=10)


def test_create_sequences_output_shape() -> None:
    """n_seqs == n_rows - seq_len; output shapes must be consistent."""
    n_rows, n_feats, seq_len = 50, 4, 10
    X = np.random.default_rng(0).standard_normal((n_rows, n_feats)).astype(np.float32)
    y = np.zeros(n_rows, dtype=np.int64)
    X_seq, y_seq = create_sequences(X, y, seq_len=seq_len)
    assert X_seq.shape == (n_rows - seq_len, seq_len, n_feats)
    assert y_seq.shape == (n_rows - seq_len,)


# ── get_backend_runner ────────────────────────────────────────────────────────


def test_get_backend_runner_unknown_raises() -> None:
    """Unknown backend key must raise ValueError."""
    with pytest.raises(ValueError):
        get_backend_runner("__totally_bogus_backend__")


def test_get_backend_runner_unknown_mentions_backend_name() -> None:
    """Error message must include the unrecognised key so users can debug it."""
    bad_key = "__totally_bogus_backend__"
    with pytest.raises(ValueError, match=bad_key):
        get_backend_runner(bad_key)


def test_get_backend_runner_known_backends() -> None:
    """All known backend keys must resolve without raising."""
    known_backends = ["mlf", "lstm", "sgd", "stats"]
    for name in known_backends:
        runner = get_backend_runner(name)
        assert callable(runner), f"Backend '{name}' must return a callable"


# ── DL backend null-data guard ────────────────────────────────────────────────


def test_run_lstm_returns_empty_dict_when_no_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """If prepare_tabular_data returns None the runner must short-circuit to {}."""
    monkeypatch.setattr(
        "mlfx.training.backends.lstm.prepare_tabular_data",
        lambda *a, **kw: None,
    )
    result = run_lstm(force=True)
    assert result == {}, "Expected empty dict when upstream data loader returns None"
