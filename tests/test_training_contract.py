from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import polars as pl


class TestTrainingDatasetHelpers:
    def test_load_labelled_dataset_reads_and_sorts_months(self, tmp_path: Path):
        from mlfx.config.paths import ProjectPaths
        from mlfx.training.dataset import load_labelled_dataset

        paths = ProjectPaths(project_root=tmp_path)
        labels_dir = paths.labels_dir("XAUUSD", "1H")
        labels_dir.mkdir(parents=True, exist_ok=True)

        pl.DataFrame(
            {
                "timestamp": [datetime(2024, 2, 1, tzinfo=timezone.utc)],
                "close": [2030.0],
                "label_10": [1],
            }
        ).write_parquet(labels_dir / "2024-02.parquet")
        pl.DataFrame(
            {
                "timestamp": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
                "close": [2020.0],
                "label_10": [0],
            }
        ).write_parquet(labels_dir / "2024-01.parquet")

        df = load_labelled_dataset("XAUUSD", "1H", paths=paths)
        assert df is not None
        assert df["timestamp"].to_list() == sorted(df["timestamp"].to_list())


class TestTrainingFeatureHelpers:
    def test_select_numeric_feature_columns_excludes_targets_and_prices(self):
        from mlfx.training.features import select_numeric_feature_columns

        df = pl.DataFrame(
            {
                "timestamp": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
                "open": [1.0],
                "close": [2.0],
                "feature_a": [3.0],
                "feature_b": [4],
                "label_10": [1],
            }
        )

        cols = select_numeric_feature_columns(df)
        assert cols == ["feature_a", "feature_b"]


class TestTrainingPersistenceHelpers:
    def test_write_metrics_json_persists_metrics_file(self, tmp_path: Path):
        from mlfx.training.persistence import write_metrics_json

        metrics_path = tmp_path / "model.metrics.json"
        write_metrics_json({"f1": 0.8}, metrics_path)
        assert metrics_path.exists()
        assert '"f1": 0.8' in metrics_path.read_text()
