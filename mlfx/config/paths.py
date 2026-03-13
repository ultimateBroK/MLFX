"""Centralized path policy for MLFX runtime artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """Resolve canonical project paths while preserving the current layout."""

    project_root: Path

    @property
    def config_file(self) -> Path:
        """Path to config.toml."""
        return self.project_root / "config.toml"

    @property
    def data_root(self) -> Path:
        """Root directory for all data (raw, ohlcv, features, labels)."""
        return self.project_root / "data"

    @property
    def outputs_root(self) -> Path:
        """Root directory for outputs (models, reports, runs, predictions, monitoring)."""
        return self.project_root / "outputs"

    @property
    def raw_root(self) -> Path:
        """Root for raw tick data."""
        return self.data_root / "raw"

    @property
    def ohlcv_root(self) -> Path:
        """Root for resampled OHLCV parquet files."""
        return self.data_root / "ohlcv"

    @property
    def features_root(self) -> Path:
        """Root for feature-engineered parquet files."""
        return self.data_root / "features"

    @property
    def labels_root(self) -> Path:
        """Root for labelled parquet files."""
        return self.data_root / "labels"

    @property
    def models_root(self) -> Path:
        """Root for model artifacts and registry.json."""
        return self.outputs_root / "models"

    @property
    def reports_root(self) -> Path:
        """Root for backtest HTML/PNG reports."""
        return self.outputs_root / "reports"

    @property
    def runs_root(self) -> Path:
        """Root for experiment tracking run metadata."""
        return self.outputs_root / "runs"

    @property
    def predictions_root(self) -> Path:
        """Root for batch inference output parquet files."""
        return self.outputs_root / "predictions"

    @property
    def monitoring_root(self) -> Path:
        """Root for drift reference snapshots and alerts."""
        return self.outputs_root / "monitoring"

    @property
    def lightning_logs_dir(self) -> Path:
        """Directory for PyTorch Lightning logs."""
        return self.project_root / "lightning_logs"

    def raw_data_dir(self, symbol: str) -> Path:
        """Path to raw tick data directory for symbol."""
        return self.raw_root / symbol

    def state_file(self, symbol: str) -> Path:
        """Path to completed-months state JSON for symbol."""
        return self.raw_data_dir(symbol) / "completed_months.json"

    def ohlcv_dir(self, symbol: str, tf: str) -> Path:
        """Path to OHLCV parquet directory for symbol/timeframe."""
        return self.ohlcv_root / symbol / tf

    def features_dir(self, symbol: str, tf: str) -> Path:
        """Path to feature parquet directory for symbol/timeframe."""
        return self.features_root / symbol / tf

    def labels_dir(self, symbol: str, tf: str) -> Path:
        """Path to label parquet directory for symbol/timeframe."""
        return self.labels_root / symbol / tf

    def models_dir(self, symbol: str, tf: str) -> Path:
        """Path to model artifacts directory for symbol/timeframe."""
        return self.models_root / symbol / tf

    def models_label_dir(self, symbol: str, tf: str, label: str) -> Path:
        """Path to model artifacts directory for a specific label column."""
        return self.models_dir(symbol, tf) / label

    def reports_dir(self, symbol: str, tf: str) -> Path:
        """Path to backtest reports directory for symbol/timeframe."""
        return self.reports_root / symbol / tf

    def reports_label_dir(self, symbol: str, tf: str, label: str) -> Path:
        """Path to backtest reports directory for a specific label column."""
        return self.reports_dir(symbol, tf) / label

    def report_run_dir(
        self,
        symbol: str,
        tf: str,
        label: str,
        mode: str,
        run_name: str,
    ) -> Path:
        """Path to a specific report run bundle grouped by label and mode."""
        return self.reports_label_dir(symbol, tf, label) / mode / run_name

    def runs_dir(self, symbol: str, tf: str) -> Path:
        """Path to experiment runs directory for symbol/timeframe."""
        return self.runs_root / symbol / tf

    def runs_label_dir(self, symbol: str, tf: str, label: str) -> Path:
        """Path to experiment runs directory for a specific label column."""
        return self.runs_dir(symbol, tf) / label

    def predictions_dir(self, symbol: str, tf: str) -> Path:
        """Path to batch predictions directory for symbol/timeframe."""
        return self.predictions_root / symbol / tf

    def predictions_label_dir(self, symbol: str, tf: str, label: str) -> Path:
        """Path to batch predictions directory for a specific label column."""
        return self.predictions_dir(symbol, tf) / label

    def monitoring_dir(self, symbol: str, tf: str) -> Path:
        """Path to drift monitoring directory for symbol/timeframe."""
        return self.monitoring_root / symbol / tf


DEFAULT_PATHS = ProjectPaths(project_root=Path(__file__).resolve().parents[2])


def get_project_paths(settings: "ServingSettings | None" = None) -> ProjectPaths:
    """Build a :class:`ProjectPaths` instance, honoring env-var overrides.

    When ``MLFX_DATA_ROOT`` or ``MLFX_OUTPUTS_ROOT`` are set the returned
    paths reflect those overrides; otherwise ``DEFAULT_PATHS`` is returned
    unchanged (zero extra cost for the common case).
    """
    # Lazy import to avoid a circular dependency at module load time.
    from .schema import ServingSettings as _ServingSettings  # noqa: PLC0415

    cfg = settings or _ServingSettings()
    if cfg.data_root is None and cfg.outputs_root is None:
        return DEFAULT_PATHS

    # Neither field accepts a relative path, so resolve unconditionally.
    data_root = Path(cfg.data_root).resolve() if cfg.data_root else None
    outputs_root = Path(cfg.outputs_root).resolve() if cfg.outputs_root else None

    base = DEFAULT_PATHS
    # Build a fresh instance with the same project_root so every *other*
    # property keeps working, then wrap with a subclass that overrides only
    # the two roots that actually changed.

    class _Overridden(ProjectPaths):  # type: ignore[misc]
        @property
        def data_root(self) -> Path:  # type: ignore[override]
            return data_root or super().data_root

        @property
        def outputs_root(self) -> Path:  # type: ignore[override]
            return outputs_root or super().outputs_root

    return _Overridden(project_root=base.project_root)
