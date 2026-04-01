"""Model registry for tracking trained artifact versions.

Provides both a lightweight JSON-backed registry and an MLflow-backed
registry for tracking trained model artifacts with their key metrics.

Usage (JSON registry)::

    from mlfx.registry import get_registry

    reg = get_registry(use_mlflow=False)
    reg.register(backend="mlf", symbol="XAUUSD", tf="1H",
                 label="label_10", metrics={"best_cv_f1_macro": 0.62})
    best = reg.best_model(symbol="XAUUSD", tf="1H", metric="best_cv_f1_macro")

Usage (MLflow registry)::

    from mlfx.registry import get_registry

    reg = get_registry(use_mlflow=True)
    reg.register(backend="mlf", symbol="XAUUSD", tf="1H",
                 label="label_10", metrics={"best_cv_f1_macro": 0.62})
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from .models import ModelRegistry, get_registry as _get_json_registry, reset_registry

if TYPE_CHECKING:
    from .mlflow_registry import MlflowModelRegistry

logger = logging.getLogger(__name__)

__all__ = [
    "ModelRegistry",
    "MlflowModelRegistry",
    "get_registry",
    "get_mlflow_registry",
    "reset_registry",
]


# Type alias for registry types
RegistryType = Union["ModelRegistry", "MlflowModelRegistry"]


def get_registry(
    use_mlflow: bool = True,
    registry_path: Path | str | None = None,
    tracking_uri: str | None = None,
) -> RegistryType:
    """Return the appropriate registry based on configuration.

    Parameters
    ----------
    use_mlflow
        If True, try to use MLflow registry. Falls back to JSON if MLflow
        is not available.
    registry_path
        Path for JSON registry (used when use_mlflow=False).
    tracking_uri
        MLflow tracking URI (used when use_mlflow=True).

    Returns
    -------
    ModelRegistry | MlflowModelRegistry
        The registry instance.
    """
    if use_mlflow:
        try:
            from .mlflow_registry import MlflowModelRegistry, get_mlflow_registry

            return get_mlflow_registry(tracking_uri=tracking_uri)
        except ImportError:
            logger.debug("MLflow not installed; using JSON registry.")
            return _get_json_registry(registry_path)

    return _get_json_registry(registry_path)


def get_mlflow_registry(
    tracking_uri: str | None = None,
    artifact_root: Path | None = None,
) -> "MlflowModelRegistry":
    """Return the MLflow model registry.

    Parameters
    ----------
    tracking_uri
        MLflow tracking URI.
    artifact_root
        Root directory for artifact storage.

    Returns
    -------
    MlflowModelRegistry
        The MLflow model registry instance.

    Raises
    ------
    ImportError
        If MLflow is not installed.
    """
    from .mlflow_registry import get_mlflow_registry as _get_mlflow_registry

    return _get_mlflow_registry(tracking_uri=tracking_uri, artifact_root=artifact_root)
