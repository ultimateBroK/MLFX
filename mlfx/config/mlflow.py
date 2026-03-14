"""MLflow configuration for MLFX experiment tracking and model registry.

Provides centralized configuration for MLflow tracking URI, artifact storage,
and experiment naming conventions. Supports environment variable overrides for
flexible deployment scenarios.

Environment Variables
---------------------
MLFLOW_TRACKING_URI
    Override the MLflow tracking server URI. Defaults to local ``mlruns/`` directory.
MLFLOW_ARTIFACT_ROOT
    Override the root directory for artifact storage. Defaults to ``outputs/mlflow_artifacts/``.
MLFLOW_REGISTRY_URI
    Override the model registry URI. Defaults to the tracking URI.

Usage
-----
>>> from mlfx.config.mlflow import MLflowConfig, get_mlflow_config
>>> config = get_mlflow_config()
>>> config.setup_mlflow()  # Configure MLflow with project settings
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


def _get_env_str(key: str, default: str | None = None) -> str | None:
    """Get string value from environment variable."""
    return os.environ.get(key, default)


def _get_env_path(key: str, default: Path | None = None) -> Path | None:
    """Get path value from environment variable."""
    value = os.environ.get(key)
    if value:
        return Path(value).resolve()
    return default


@dataclass(frozen=True)
class MLflowConfig:
    """Configuration for MLflow integration.

    Attributes
    ----------
    tracking_uri
        URI for MLflow tracking server. Can be:
        - Local path: ``./mlruns`` or ``file:///path/to/mlruns``
        - HTTP server: ``http://localhost:5000``
        - Databricks: ``databricks``
    artifact_root
        Root directory for artifact storage when using local file backend.
    registry_uri
        URI for model registry. Defaults to tracking_uri if not specified.
    experiment_prefix
        Prefix for experiment names. Default: ``mlfx``.
    default_artifact_store
        Default artifact store type: ``file``, ``s3``, ``gs``, ``azure``.
    """

    tracking_uri: str | None = None
    artifact_root: Path | None = None
    registry_uri: str | None = None
    experiment_prefix: str = "mlfx"
    default_artifact_store: Literal["file", "s3", "gs", "azure"] = "file"

    # Environment variable names
    _ENV_TRACKING_URI: str = field(default="MLFLOW_TRACKING_URI", repr=False)
    _ENV_ARTIFACT_ROOT: str = field(default="MLFLOW_ARTIFACT_ROOT", repr=False)
    _ENV_REGISTRY_URI: str = field(default="MLFLOW_REGISTRY_URI", repr=False)

    @property
    def resolved_tracking_uri(self) -> str:
        """Return tracking URI with environment variable override."""
        env_value = _get_env_str(self._ENV_TRACKING_URI)
        if env_value:
            return env_value
        if self.tracking_uri:
            return self.tracking_uri
        # Default to SQLite database (recommended over deprecated file-based store)
        return f"sqlite:///{self._default_db_path()}"

    @property
    def resolved_artifact_root(self) -> Path:
        """Return artifact root with environment variable override."""
        env_value = _get_env_path(self._ENV_ARTIFACT_ROOT)
        if env_value:
            return env_value
        if self.artifact_root:
            return self.artifact_root
        # Default to outputs/mlflow_artifacts
        return self._default_artifact_path()

    @property
    def resolved_registry_uri(self) -> str | None:
        """Return registry URI with environment variable override."""
        env_value = _get_env_str(self._ENV_REGISTRY_URI)
        if env_value:
            return env_value
        return self.registry_uri

    def _default_mlruns_path(self) -> Path:
        """Return default mlruns directory path (legacy file-based store)."""
        # Use project root relative to this file
        project_root = Path(__file__).resolve().parents[2]
        return project_root / "mlruns"

    def _default_db_path(self) -> Path:
        """Return default SQLite database path for MLflow backend.
        
        SQLite is recommended over file-based store as of Feb 2026.
        """
        project_root = Path(__file__).resolve().parents[2]
        return project_root / "mlflow.db"

    def _default_artifact_path(self) -> Path:
        """Return default artifact storage path."""
        project_root = Path(__file__).resolve().parents[2]
        return project_root / "outputs" / "mlflow_artifacts"

    def experiment_name(
        self,
        symbol: str | None = None,
        tf: str | None = None,
        label: str | None = None,
        backend: str | None = None,
    ) -> str:
        """Generate experiment name following MLFX naming convention.

        Format: ``mlfx/<symbol>/<tf>/<label>`` or ``mlfx/<symbol>/<tf>/<backend>/<label>``

        Parameters
        ----------
        symbol
            Trading symbol (e.g., ``XAUUSD``).
        tf
            Timeframe (e.g., ``1H``).
        label
            Label column name (e.g., ``label_10``).
        backend
            Training backend name (e.g., ``mlf``, ``lstm``).

        Returns
        -------
        str
            Formatted experiment name.
        """
        parts = [self.experiment_prefix]
        if symbol:
            parts.append(symbol)
        if tf:
            parts.append(tf)
        if backend:
            parts.append(backend)
        if label:
            parts.append(label)
        return "/".join(parts)

    def model_name(
        self,
        symbol: str,
        tf: str,
        label: str,
        backend: str | None = None,
    ) -> str:
        """Generate model name for MLflow Model Registry.

        Format: ``mlfx-<symbol>-<tf>-<label>`` or ``mlfx-<symbol>-<tf>-<backend>-<label>``

        Parameters
        ----------
        symbol
            Trading symbol.
        tf
            Timeframe.
        label
            Label column name.
        backend
            Training backend name (optional).

        Returns
        -------
        str
            Formatted model name suitable for registry.
        """
        parts = [self.experiment_prefix, symbol, tf]
        if backend:
            parts.append(backend)
        parts.append(label)
        return "-".join(parts)

    def setup_mlflow(self) -> None:
        """Configure MLflow with project settings.

        Sets up tracking URI, registry URI, and creates necessary directories.
        This should be called before any MLflow operations.
        """
        try:
            import mlflow  # noqa: PLC0415
        except ImportError as e:
            logger.warning("MLflow not installed. Run: pixi add mlflow")
            raise ImportError("MLflow is required for this operation") from e

        # Set tracking URI
        tracking_uri = self.resolved_tracking_uri
        mlflow.set_tracking_uri(tracking_uri)
        logger.debug("MLflow tracking URI: %s", tracking_uri)

        # Set registry URI if specified
        registry_uri = self.resolved_registry_uri
        if registry_uri:
            mlflow.set_registry_uri(registry_uri)
            logger.debug("MLflow registry URI: %s", registry_uri)

        # Ensure artifact directory exists for local storage
        if tracking_uri.startswith("file://") or (
            not tracking_uri.startswith("http") and not tracking_uri.startswith("databricks")
        ):
            artifact_root = self.resolved_artifact_root
            artifact_root.mkdir(parents=True, exist_ok=True)
            logger.debug("MLflow artifact root: %s", artifact_root)

    def is_mlflow_available(self) -> bool:
        """Check if MLflow is installed and available."""
        try:
            import mlflow  # noqa: PLC0415, F401
            return True
        except ImportError:
            return False


# ---------------------------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------------------------

_mlflow_config: MLflowConfig | None = None


def get_mlflow_config(
    tracking_uri: str | None = None,
    artifact_root: Path | None = None,
    registry_uri: str | None = None,
    experiment_prefix: str = "mlfx",
) -> MLflowConfig:
    """Return the process-level MLflow configuration singleton.

    Parameters
    ----------
    tracking_uri
        Override tracking URI. If provided, creates new singleton.
    artifact_root
        Override artifact root path. If provided, creates new singleton.
    registry_uri
        Override registry URI. If provided, creates new singleton.
    experiment_prefix
        Prefix for experiment names.

    Returns
    -------
    MLflowConfig
        The MLflow configuration instance.
    """
    global _mlflow_config
    if _mlflow_config is None or any(
        [tracking_uri is not None, artifact_root is not None, registry_uri is not None]
    ):
        _mlflow_config = MLflowConfig(
            tracking_uri=tracking_uri,
            artifact_root=artifact_root,
            registry_uri=registry_uri,
            experiment_prefix=experiment_prefix,
        )
    return _mlflow_config


def reset_mlflow_config() -> None:
    """Reset the MLflow configuration singleton. Use in tests for isolation."""
    global _mlflow_config
    _mlflow_config = None
