"""MLflow-backed model registry for MLFX.

Provides a model registry implementation that uses MLflow Model Registry
for versioning and stage management while maintaining the same interface
as the JSON-backed ModelRegistry for seamless compatibility.

Usage
-----
>>> from mlfx.registry.mlflow_registry import MlflowModelRegistry
>>> registry = MlflowModelRegistry()
>>> registry.register("mlf", "XAUUSD", "1H", "label_10", {"f1": 0.85})
>>> best = registry.best_model(symbol="XAUUSD", tf="1H", metric="f1")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal

from mlfx.config.mlflow import get_mlflow_config
from mlfx.config.paths import DEFAULT_PATHS

logger = logging.getLogger(__name__)

# Stage constants
STAGE_STAGING = "Staging"
STAGE_PRODUCTION = "Production"
STAGE_ARCHIVED = "Archived"
STAGE_NONE = "None"


class MlflowModelRegistry:
    """MLflow-backed model registry with same interface as ModelRegistry.

    This registry stores model metadata (metrics, params, tags) in MLflow
    while keeping binary artifacts on disk via MLflow's artifact store.

    Parameters
    ----------
    tracking_uri
        MLflow tracking server URI. If None, uses config default.
    registry_uri
        MLflow model registry URI. If None, uses tracking URI.
    artifact_root
        Root directory for artifact storage.
    """

    def __init__(
        self,
        tracking_uri: str | None = None,
        registry_uri: str | None = None,
        artifact_root: Path | None = None,
    ) -> None:
        self._config = get_mlflow_config(
            tracking_uri=tracking_uri,
            artifact_root=artifact_root,
            registry_uri=registry_uri,
        )
        self._artifact_root = artifact_root or DEFAULT_PATHS.models_root
        self._mlflow_client: Any | None = None

    def _get_client(self) -> Any:
        """Get or create MLflow client."""
        if self._mlflow_client is None:
            try:
                import mlflow  # noqa: PLC0415
                from mlflow.tracking import MlflowClient  # noqa: PLC0415

                self._config.setup_mlflow()
                self._mlflow_client = MlflowClient()
            except ImportError as e:
                logger.warning("MLflow not installed. Run: pixi add mlflow")
                raise ImportError("MLflow is required for MlflowModelRegistry") from e
        return self._mlflow_client

    def _model_name(
        self,
        symbol: str,
        tf: str,
        label: str,
        backend: str | None = None,
    ) -> str:
        """Generate model name for registry."""
        return self._config.model_name(symbol, tf, label, backend)

    def register(
        self,
        backend: str,
        symbol: str,
        tf: str,
        label: str,
        metrics: dict[str, Any],
        *,
        artifact_path: str | Path | None = None,
        tags: dict[str, str] | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """Register a new model version in MLflow Model Registry.

        Parameters
        ----------
        backend
            Training backend name.
        symbol
            Trading symbol.
        tf
            Timeframe.
        label
            Label column name.
        metrics
            Metrics dict from training.
        artifact_path
            Path to the model artifact file.
        tags
            Optional tags for the model version.
        run_id
            MLflow run ID if the model was logged during a run.

        Returns
        -------
        dict
            The registered model version info.
        """
        if not label:
            raise ValueError("Model registry requires a non-empty label")

        client = self._get_client()
        model_name = self._model_name(symbol, tf, label, backend)

        # Build tags
        full_tags = tags or {}
        full_tags.update({
            "symbol": symbol,
            "tf": tf,
            "label": label,
            "backend": backend,
        })

        # Build metrics dict for return
        numeric_metrics = {
            k: v for k, v in metrics.items()
            if isinstance(v, (int, float))
        }

        # Register model
        if run_id and artifact_path:
            # Register from existing run
            model_uri = f"runs:/{run_id}/{Path(artifact_path).name}"
            model_version = client.create_model_version(
                name=model_name,
                source=model_uri,
                tags=full_tags,
            )
        elif artifact_path:
            # Register from local file
            artifact_path = Path(artifact_path)
            model_uri = f"file://{artifact_path.parent}"
            model_version = client.create_model_version(
                name=model_name,
                source=model_uri,
                tags=full_tags,
            )
        else:
            # Create registered model without version (for metadata tracking)
            try:
                client.create_registered_model(model_name, tags=full_tags)
            except Exception:  # noqa: BLE001
                pass  # Model may already exist
            model_version = None

        entry: dict[str, Any] = {
            "backend": backend,
            "symbol": symbol,
            "tf": tf,
            "label": label,
            "model_name": model_name,
            "metrics": numeric_metrics,
            "feature_columns": [
                col for col in metrics.get("selected_features", [])
                if isinstance(col, str)
            ],
            "artifact_path": str(artifact_path or ""),
            "tags": full_tags,
        }

        if model_version:
            entry["version"] = model_version.version
            entry["stage"] = model_version.current_stage

        logger.info(
            "MLflow Registry: registered %s %s/%s %s (version=%s)",
            backend, symbol, tf, label,
            model_version.version if model_version else "N/A",
        )
        return entry

    def list_models(
        self,
        *,
        symbol: str | None = None,
        tf: str | None = None,
        backend: str | None = None,
        label: str | None = None,
    ) -> list[dict[str, Any]]:
        """List all registered models matching the given filters.

        Parameters
        ----------
        symbol
            Filter by symbol.
        tf
            Filter by timeframe.
        backend
            Filter by backend.
        label
            Filter by label column.

        Returns
        -------
        list[dict[str, Any]]
            List of model version dictionaries.
        """
        client = self._get_client()
        results: list[dict[str, Any]] = []

        # Search all registered models
        try:
            registered_models = client.search_registered_models()
        except Exception:  # noqa: BLE001
            return results

        for rm in registered_models:
            # Check if model matches our naming convention
            name = rm.name
            if not name.startswith(self._config.experiment_prefix):
                continue

            # Parse model name: mlfx-SYMBOL-TF-[BACKEND-]LABEL
            parts = name.split("-")
            if len(parts) < 4:
                continue

            model_symbol = parts[1]
            model_tf = parts[2]
            model_label = parts[-1]
            model_backend = parts[3] if len(parts) > 4 else None

            # Apply filters
            if symbol and model_symbol != symbol:
                continue
            if tf and model_tf != tf:
                continue
            if backend and model_backend != backend:
                continue
            if label and model_label != label:
                continue

            # Get latest versions
            try:
                # Use search_model_versions instead of deprecated get_latest_versions
                versions = list(client.search_model_versions(f"name='{name}'", max_results=100))
                for v in versions:
                    results.append({
                        "model_name": name,
                        "version": v.version,
                        "stage": v.current_stage,
                        "symbol": model_symbol,
                        "tf": model_tf,
                        "backend": model_backend,
                        "label": model_label,
                        "tags": v.tags,
                        "run_id": v.run_id,
                        "artifact_uri": v.source,
                    })
            except Exception:  # noqa: BLE001
                continue

        return results

    def best_model(
        self,
        *,
        symbol: str,
        tf: str,
        label: str | None = None,
        metric: str = "best_cv_f1_macro",
        backend: str | None = None,
    ) -> dict[str, Any] | None:
        """Return the best model version by the given metric.

        Parameters
        ----------
        symbol
            Trading symbol.
        tf
            Timeframe.
        label
            Label column name (optional).
        metric
            Metric name to compare.
        backend
            Backend filter (optional).

        Returns
        -------
        dict[str, Any] | None
            Best model version info, or None if not found.
        """
        client = self._get_client()

        # Build model name pattern
        model_name = self._model_name(symbol, tf, label or "*", backend)

        try:
            # Get all versions for this model
            # Use search_model_versions instead of deprecated get_latest_versions
            versions = list(client.search_model_versions(
                f"name='{model_name.replace('*', '')}'", max_results=100
            ))

            if not versions:
                return None

            # Find version with best metric
            best_version = None
            best_metric_value = float("-inf")

            for v in versions:
                # Get run to access metrics
                if v.run_id:
                    run = client.get_run(v.run_id)
                    metric_value = run.data.metrics.get(metric)
                    if metric_value is not None and metric_value > best_metric_value:
                        best_metric_value = metric_value
                        best_version = v
                else:
                    # Check tags for metric
                    metric_str = v.tags.get(f"metric.{metric}")
                    if metric_str:
                        try:
                            metric_value = float(metric_str)
                            if metric_value > best_metric_value:
                                best_metric_value = metric_value
                                best_version = v
                        except ValueError:
                            continue

            if best_version is None:
                return None

            # Parse model name
            parts = best_version.name.split("-")
            return {
                "model_name": best_version.name,
                "version": best_version.version,
                "stage": best_version.current_stage,
                "symbol": parts[1] if len(parts) > 1 else symbol,
                "tf": parts[2] if len(parts) > 2 else tf,
                "backend": parts[3] if len(parts) > 4 else None,
                "label": parts[-1] if len(parts) > 3 else label,
                "metrics": {metric: best_metric_value},
                "artifact_uri": best_version.source,
                "run_id": best_version.run_id,
            }

        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to find best model: %s", exc)
            return None

    def get_model_version(
        self,
        model_name: str,
        version: str | int | None = None,
        stage: Literal["Staging", "Production", "Archived", "None"] | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific model version.

        Parameters
        ----------
        model_name
            Registered model name.
        version
            Specific version number. If None, uses stage.
        stage
            Stage to get latest version from. Ignored if version is provided.

        Returns
        -------
        dict[str, Any] | None
            Model version info, or None if not found.
        """
        client = self._get_client()

        try:
            if version:
                v = client.get_model_version(model_name, str(version))
            elif stage:
                # Use search_model_versions instead of deprecated get_latest_versions
                versions = list(client.search_model_versions(f"name='{model_name}'", max_results=100))
                versions = [v for v in versions if v.current_stage == stage]
                if not versions:
                    return None
                v = max(versions, key=lambda x: int(x.version))
            else:
                # Get latest production version
                versions = list(client.search_model_versions(f"name='{model_name}'", max_results=100))
                prod_versions = [v for v in versions if v.current_stage == "Production"]
                if prod_versions:
                    v = max(prod_versions, key=lambda x: int(x.version))
                elif versions:
                    v = max(versions, key=lambda x: int(x.version))
                else:
                    return None

            return {
                "model_name": v.name,
                "version": v.version,
                "stage": v.current_stage,
                "artifact_uri": v.source,
                "run_id": v.run_id,
                "tags": v.tags,
            }

        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to get model version: %s", exc)
            return None

    def transition_stage(
        self,
        model_name: str,
        version: str | int,
        stage: Literal["Staging", "Production", "Archived"],
    ) -> dict[str, Any] | None:
        """Transition a model version to a new stage.

        Parameters
        ----------
        model_name
            Registered model name.
        version
            Version number.
        stage
            Target stage.

        Returns
        -------
        dict[str, Any] | None
            Updated model version info.
        """
        client = self._get_client()

        try:
            v = client.transition_model_version_stage(
                name=model_name,
                version=str(version),
                stage=stage,
            )
            logger.info("Transitioned %s v%s to %s", model_name, version, stage)
            return {
                "model_name": v.name,
                "version": v.version,
                "stage": v.current_stage,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to transition stage: %s", exc)
            return None

    def download_artifact(
        self,
        model_name: str,
        version: str | int | None = None,
        stage: str | None = None,
        dst_path: Path | str | None = None,
    ) -> Path | None:
        """Download model artifact to local path.

        Parameters
        ----------
        model_name
            Registered model name.
        version
            Version number.
        stage
            Stage to download from.
        dst_path
            Destination directory. Defaults to models_root.

        Returns
        -------
        Path | None
            Path to downloaded artifact, or None if failed.
        """
        import mlflow  # noqa: PLC0415

        client = self._get_client()
        version_info = self.get_model_version(model_name, version, stage)  # type: ignore[arg-type]

        if version_info is None:
            return None

        try:
            model_uri = f"models:/{model_name}/{version_info['version']}"
            dst_dir = Path(dst_path) if dst_path else self._artifact_root
            dst_dir.mkdir(parents=True, exist_ok=True)

            # Download using MLflow
            local_path = mlflow.artifacts.download_artifacts(
                artifact_uri=model_uri,
                dst_path=str(dst_dir),
            )
            return Path(local_path)

        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to download artifact: %s", exc)
            return None


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_mlflow_registry: MlflowModelRegistry | None = None


def get_mlflow_registry(
    tracking_uri: str | None = None,
    artifact_root: Path | None = None,
) -> MlflowModelRegistry:
    """Return the process-level MLflow registry singleton.

    Parameters
    ----------
    tracking_uri
        Override tracking URI.
    artifact_root
        Override artifact root path.

    Returns
    -------
    MlflowModelRegistry
        The MLflow model registry instance.
    """
    global _mlflow_registry
    if _mlflow_registry is None or tracking_uri is not None or artifact_root is not None:
        _mlflow_registry = MlflowModelRegistry(
            tracking_uri=tracking_uri,
            artifact_root=artifact_root,
        )
    return _mlflow_registry


def reset_mlflow_registry() -> None:
    """Reset the MLflow registry singleton. Use in tests for isolation."""
    global _mlflow_registry
    _mlflow_registry = None
