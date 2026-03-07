"""Centralized path policy for ML_FX runtime artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """Resolve canonical project paths while preserving the current layout."""

    project_root: Path

    @property
    def config_file(self) -> Path:
        return self.project_root / "config.toml"

    @property
    def data_root(self) -> Path:
        return self.project_root / "data"

    @property
    def outputs_root(self) -> Path:
        return self.project_root / "outputs"

    @property
    def raw_root(self) -> Path:
        return self.data_root / "raw"

    @property
    def ohlcv_root(self) -> Path:
        return self.data_root / "ohlcv"

    @property
    def features_root(self) -> Path:
        return self.data_root / "features"

    @property
    def labels_root(self) -> Path:
        return self.data_root / "labels"

    @property
    def models_root(self) -> Path:
        return self.outputs_root / "models"

    @property
    def reports_root(self) -> Path:
        return self.outputs_root / "reports"

    @property
    def runs_root(self) -> Path:
        return self.outputs_root / "runs"

    @property
    def predictions_root(self) -> Path:
        return self.outputs_root / "predictions"

    @property
    def monitoring_root(self) -> Path:
        return self.outputs_root / "monitoring"

    @property
    def lightning_logs_dir(self) -> Path:
        return self.project_root / "lightning_logs"

    def raw_data_dir(self, symbol: str) -> Path:
        return self.raw_root / symbol

    def state_file(self, symbol: str) -> Path:
        return self.raw_data_dir(symbol) / "completed_months.json"

    def ohlcv_dir(self, symbol: str, tf: str) -> Path:
        return self.ohlcv_root / symbol / tf

    def features_dir(self, symbol: str, tf: str) -> Path:
        return self.features_root / symbol / tf

    def labels_dir(self, symbol: str, tf: str) -> Path:
        return self.labels_root / symbol / tf

    def models_dir(self, symbol: str, tf: str) -> Path:
        return self.models_root / symbol / tf

    def reports_dir(self, symbol: str, tf: str) -> Path:
        return self.reports_root / symbol / tf

    def runs_dir(self, symbol: str, tf: str) -> Path:
        return self.runs_root / symbol / tf

    def predictions_dir(self, symbol: str, tf: str) -> Path:
        return self.predictions_root / symbol / tf

    def monitoring_dir(self, symbol: str, tf: str) -> Path:
        return self.monitoring_root / symbol / tf


DEFAULT_PATHS = ProjectPaths(project_root=Path(__file__).resolve().parents[2])
