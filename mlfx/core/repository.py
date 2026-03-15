"""Repository pattern for data access in MLFX.

This module defines abstract repository interfaces and concrete implementations
for accessing data artifacts. The repository pattern provides:
- A clean separation between data access logic and business logic
- Consistent interfaces for different data sources
- Easier testing through dependency injection
- Single point of change for data access modifications
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import polars as pl

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths

if TYPE_CHECKING:
    from mlfx.core.domain import DataKey, ModelKey

# =============================================================================
# Protocols (Interfaces)
# =============================================================================


class DataRepository(Protocol):
    """Protocol for data repository implementations."""

    def load_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame | None:
        """Load OHLCV data for a symbol and timeframe."""
        ...

    def load_features(
        self,
        symbol: str,
        timeframe: str,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame | None:
        """Load feature data for a symbol and timeframe."""
        ...

    def load_labels(
        self,
        symbol: str,
        timeframe: str,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame | None:
        """Load labeled data for a symbol and timeframe."""
        ...

    def save_features(
        self,
        df: pl.DataFrame,
        symbol: str,
        timeframe: str,
        *,
        partition_by: str = "month",
    ) -> list[Path]:
        """Save feature data."""
        ...

    def save_labels(
        self,
        df: pl.DataFrame,
        symbol: str,
        timeframe: str,
        *,
        partition_by: str = "month",
    ) -> list[Path]:
        """Save labeled data."""
        ...


class ModelRepository(Protocol):
    """Protocol for model repository implementations."""

    def load_model(
        self,
        symbol: str,
        timeframe: str,
        label: str,
        backend: str,
    ) -> tuple[Any, dict[str, Any]] | None:
        """Load a trained model and its metadata."""
        ...

    def save_model(
        self,
        model: Any,
        metadata: dict[str, Any],
        symbol: str,
        timeframe: str,
        label: str,
        backend: str,
    ) -> Path:
        """Save a trained model with metadata."""
        ...

    def list_models(
        self,
        symbol: str | None = None,
        timeframe: str | None = None,
        label: str | None = None,
        backend: str | None = None,
    ) -> list[dict[str, Any]]:
        """List available models matching the criteria."""
        ...

    def best_model(
        self,
        symbol: str,
        timeframe: str,
        label: str,
        backend: str | None = None,
    ) -> dict[str, Any] | None:
        """Get the best model for the given criteria."""
        ...


# =============================================================================
# Concrete Implementations
# =============================================================================


class ParquetDataRepository:
    """Data repository backed by Parquet files."""

    def __init__(self, paths: ProjectPaths = DEFAULT_PATHS) -> None:
        self._paths = paths

    def load_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame | None:
        """Load OHLCV data for a symbol and timeframe."""
        in_dir = Path(self._paths.ohlcv_dir(symbol, timeframe))
        files = sorted(in_dir.glob("*.parquet"))
        if not files:
            return None

        frames = [pl.read_parquet(f) for f in files]
        df = pl.concat(frames).sort("timestamp")

        # Apply date filters if provided
        if start:
            df = df.filter(pl.col("timestamp") >= start)
        if end:
            df = df.filter(pl.col("timestamp") <= end)

        return df

    def load_features(
        self,
        symbol: str,
        timeframe: str,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame | None:
        """Load feature data for a symbol and timeframe."""
        in_dir = Path(self._paths.features_dir(symbol, timeframe))
        files = sorted(in_dir.glob("*.parquet"))
        if not files:
            return None

        frames = [pl.read_parquet(f) for f in files]
        df = pl.concat(frames).sort("timestamp")

        if start:
            df = df.filter(pl.col("timestamp") >= start)
        if end:
            df = df.filter(pl.col("timestamp") <= end)

        return df

    def load_labels(
        self,
        symbol: str,
        timeframe: str,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> pl.DataFrame | None:
        """Load labeled data for a symbol and timeframe."""
        in_dir = Path(self._paths.labels_dir(symbol, timeframe))
        files = sorted(in_dir.glob("*.parquet"))
        if not files:
            return None

        frames = [pl.read_parquet(f) for f in files]
        df = pl.concat(frames).sort("timestamp")

        if start:
            df = df.filter(pl.col("timestamp") >= start)
        if end:
            df = df.filter(pl.col("timestamp") <= end)

        return df

    def save_features(
        self,
        df: pl.DataFrame,
        symbol: str,
        timeframe: str,
        *,
        partition_by: str = "month",
    ) -> list[Path]:
        """Save feature data partitioned by month."""
        out_dir = Path(self._paths.features_dir(symbol, timeframe))
        out_dir.mkdir(parents=True, exist_ok=True)

        if partition_by == "month":
            return self._partition_by_month(df, out_dir)
        else:
            # Single file
            path = out_dir / "features.parquet"
            df.write_parquet(path)
            return [path]

    def save_labels(
        self,
        df: pl.DataFrame,
        symbol: str,
        timeframe: str,
        *,
        partition_by: str = "month",
    ) -> list[Path]:
        """Save labeled data partitioned by month."""
        out_dir = Path(self._paths.labels_dir(symbol, timeframe))
        out_dir.mkdir(parents=True, exist_ok=True)

        if partition_by == "month":
            return self._partition_by_month(df, out_dir)
        else:
            path = out_dir / "labels.parquet"
            df.write_parquet(path)
            return [path]

    def _partition_by_month(self, df: pl.DataFrame, out_dir: Path) -> list[Path]:
        """Partition DataFrame by month and write to parquet files."""
        # Add year-month column for partitioning
        df = df.with_columns(
            pl.from_epoch("timestamp", time_unit="ms")
            .dt.strftime("%Y-%m")
            .alias("year_month")
        )

        paths = []
        for year_month in df["year_month"].unique().sort():
            month_df = df.filter(pl.col("year_month") == year_month)
            month_df = month_df.drop("year_month")
            path = out_dir / f"{year_month}.parquet"
            month_df.write_parquet(path)
            paths.append(path)

        return paths


class FileSystemModelRepository:
    """Model repository backed by filesystem storage."""

    def __init__(self, paths: ProjectPaths = DEFAULT_PATHS) -> None:
        self._paths = paths

    def load_model(
        self,
        symbol: str,
        timeframe: str,
        label: str,
        backend: str,
    ) -> tuple[Any, dict[str, Any]] | None:
        """Load a trained model and its metadata."""
        import joblib

        model_dir = Path(self._paths.models_label_dir(symbol, timeframe, label))
        model_file = model_dir / f"{backend}_model.pkl"
        meta_file = model_dir / f"{backend}_metadata.json"

        if not model_file.exists():
            return None

        model = joblib.load(model_file)
        metadata = {}
        if meta_file.exists():
            import json

            metadata = json.loads(meta_file.read_text())

        return model, metadata

    def save_model(
        self,
        model: Any,
        metadata: dict[str, Any],
        symbol: str,
        timeframe: str,
        label: str,
        backend: str,
    ) -> Path:
        """Save a trained model with metadata."""
        import json

        import joblib

        model_dir = Path(self._paths.models_label_dir(symbol, timeframe, label))
        model_dir.mkdir(parents=True, exist_ok=True)

        model_file = model_dir / f"{backend}_model.pkl"
        meta_file = model_dir / f"{backend}_metadata.json"

        joblib.dump(model, model_file)
        meta_file.write_text(json.dumps(metadata, indent=2, default=str))

        return model_file

    def list_models(
        self,
        symbol: str | None = None,
        timeframe: str | None = None,
        label: str | None = None,
        backend: str | None = None,
    ) -> list[dict[str, Any]]:
        """List available models matching the criteria."""
        import json

        models_dir = Path(self._paths.models_root)
        if not models_dir.exists():
            return []

        results = []
        for meta_file in models_dir.rglob("*_metadata.json"):
            try:
                metadata = json.loads(meta_file.read_text())
                # Extract symbol, tf, label, backend from path
                parts = meta_file.relative_to(models_dir).parts
                if len(parts) >= 4:
                    meta_symbol = parts[0]
                    meta_tf = parts[1]
                    meta_label = parts[2]
                    meta_backend = meta_file.stem.replace("_metadata", "")

                    # Apply filters
                    if symbol and meta_symbol != symbol:
                        continue
                    if timeframe and meta_tf != timeframe:
                        continue
                    if label and meta_label != label:
                        continue
                    if backend and meta_backend != backend:
                        continue

                    results.append({
                        "symbol": meta_symbol,
                        "timeframe": meta_tf,
                        "label": meta_label,
                        "backend": meta_backend,
                        "metadata": metadata,
                        "path": str(meta_file.parent),
                    })
            except (json.JSONDecodeError, KeyError):
                continue

        return results

    def best_model(
        self,
        symbol: str,
        timeframe: str,
        label: str,
        backend: str | None = None,
    ) -> dict[str, Any] | None:
        """Get the best model for the given criteria."""
        models = self.list_models(
            symbol=symbol,
            timeframe=timeframe,
            label=label,
            backend=backend,
        )
        if not models:
            return None

        # Sort by cv_f1_macro descending
        def get_f1(model: dict) -> float:
            metrics = model.get("metadata", {}).get("metrics", {})
            return float(metrics.get("cv_f1_macro", 0) or 0)

        models.sort(key=get_f1, reverse=True)
        return models[0]


# =============================================================================
# Default Repository Instances
# =============================================================================

DEFAULT_DATA_REPO = ParquetDataRepository()
DEFAULT_MODEL_REPO = FileSystemModelRepository()
