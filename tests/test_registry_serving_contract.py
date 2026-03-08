from __future__ import annotations

import pickle
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import polars as pl
import pytest


class _OrderSensitiveModel:
    def predict(self, X: np.ndarray) -> np.ndarray:
        # Class 4 when first feature column dominates, else class 0.
        return np.where(X[:, 0] > X[:, 1], 4, 0)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:  # pragma: no cover - simple helper
        proba = np.full((len(X), 5), 0.05, dtype=np.float32)
        labels = self.predict(X)
        for idx, label in enumerate(labels):
            proba[idx, int(label)] = 0.8
        return proba


def test_batch_inference_uses_registry_feature_order(tmp_path: Path):
    from mlfx.config.paths import ProjectPaths
    from mlfx.registry.models import get_registry, reset_registry

    reset_registry()
    from mlfx.serving.batch import run_batch_inference

    paths = ProjectPaths(project_root=tmp_path)

    # Build a tiny feature dataset.
    feature_dir = paths.features_dir("XAUUSD", "1H")
    feature_dir.mkdir(parents=True, exist_ok=True)
    base_ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    pl.DataFrame(
        {
            "timestamp": [base_ts + timedelta(hours=i) for i in range(3)],
            "open": [1.0, 1.1, 1.2],
            "high": [1.1, 1.2, 1.3],
            "low": [0.9, 1.0, 1.1],
            "close": [1.0, 1.1, 1.2],
            "feat_a": [0.2, 0.3, 0.4],
            "feat_b": [0.8, 0.7, 0.6],
        }
    ).write_parquet(feature_dir / "2024-01.parquet")

    artifact_path = paths.models_dir("XAUUSD", "1H") / "dummy.pkl"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    with artifact_path.open("wb") as file_handle:
        pickle.dump(_OrderSensitiveModel(), file_handle)

    registry = get_registry(paths.models_root / "registry.json")
    registry.register(
        backend="mlf",
        symbol="XAUUSD",
        tf="1H",
        label_col="label_10",
        metrics={"best_cv_f1_macro": 0.9, "selected_features": ["feat_b", "feat_a"]},
        artifact_path=artifact_path,
    )

    result = run_batch_inference("XAUUSD", "1H", "label_10", paths=paths)
    assert result["rows"] == 3
    output_path = Path(result["output_path"])
    assert output_path.exists()

    output_df = pl.read_parquet(output_path)
    # With feature order feat_b, feat_a all rows satisfy feat_b > feat_a.
    assert output_df["prediction"].to_list() == [2, 2, 2]


def test_predict_labels_handles_torch_state_dict_payload():
    """predict_labels supports PyTorch LSTM/BiLSTM/CNN-LSTM/Transformer artifacts."""
    pytest.importorskip("torch")

    from mlfx.serving.inference import predict_labels
    from mlfx.training.backends.lstm import FXLstm

    # Minimal LSTM: 2 features, seq_len=5
    model = FXLstm(input_size=2, hidden_size=8, num_layers=1, dropout=0.1, num_classes=5)
    payload = {
        "state_dict": model.state_dict(),
        "metrics": {
            "model_type": "LSTM",
            "seq_len": 5,
            "selected_features": ["feat_a", "feat_b"],
            "best_params": {
                "hidden_size": 8,
                "num_layers": 1,
                "dropout": 0.1,
            },
        },
    }

    # X with 10 rows, 2 features - after seq_len=5 we get 6 sequence predictions
    X = np.random.randn(10, 2).astype(np.float32)
    preds = predict_labels(payload, X)

    assert preds.shape == (10,)
    assert preds.dtype == np.int64
    # First seq_len=5 rows are padded with neutral (2)
    assert (preds[:5] == 2).all()
    # Remaining 5 are model predictions in [0, 4]
    assert (preds[5:] >= 0).all()
    assert (preds[5:] <= 4).all()
