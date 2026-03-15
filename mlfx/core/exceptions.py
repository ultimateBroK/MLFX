"""Custom exception hierarchy for MLFX.

This module defines a structured exception hierarchy that provides:
- Clear error categorization
- Consistent error handling patterns
- Actionable error messages
- Easy error catching at appropriate levels
"""

from __future__ import annotations

from typing import Any


class MLFXError(Exception):
    """Base exception for all MLFX errors.

    All custom exceptions in MLFX inherit from this class, allowing
    users to catch all MLFX-specific errors with a single except clause.
    """

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v!r}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


# =============================================================================
# Data Layer Exceptions
# =============================================================================


class DataError(MLFXError):
    """Base exception for data-related errors."""

    pass


class DataNotFoundError(DataError):
    """Raised when requested data does not exist."""

    def __init__(
        self,
        data_type: str,
        symbol: str | None = None,
        timeframe: str | None = None,
        label: str | None = None,
        path: str | None = None,
    ) -> None:
        parts = [data_type]
        if symbol:
            parts.append(f"symbol={symbol}")
        if timeframe:
            parts.append(f"tf={timeframe}")
        if label:
            parts.append(f"label={label}")
        message = f"Data not found: {' '.join(parts)}"
        details = {"data_type": data_type}
        if path:
            details["path"] = path
        super().__init__(message, details=details)


class DataValidationError(DataError):
    """Raised when data fails validation checks."""

    def __init__(self, message: str, *, column: str | None = None, row: int | None = None) -> None:
        details = {}
        if column:
            details["column"] = column
        if row is not None:
            details["row"] = row
        super().__init__(message, details=details)


class DataDownloadError(DataError):
    """Raised when data download fails."""

    def __init__(self, source: str, reason: str) -> None:
        message = f"Failed to download data from {source}: {reason}"
        super().__init__(message, details={"source": source, "reason": reason})


class DataParseError(DataError):
    """Raised when data parsing fails."""

    def __init__(self, file_path: str, reason: str) -> None:
        message = f"Failed to parse data file: {reason}"
        super().__init__(message, details={"file_path": file_path, "reason": reason})


# =============================================================================
# Model Layer Exceptions
# =============================================================================


class ModelError(MLFXError):
    """Base exception for model-related errors."""

    pass


class ModelNotFoundError(ModelError):
    """Raised when a requested model does not exist."""

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        label: str,
        backend: str | None = None,
    ) -> None:
        message = f"No model found for {symbol}/{timeframe}/{label}"
        if backend:
            message += f" (backend={backend})"
        details = {"symbol": symbol, "timeframe": timeframe, "label": label}
        if backend:
            details["backend"] = backend
        super().__init__(message, details=details)


class ModelLoadError(ModelError):
    """Raised when model loading fails."""

    def __init__(self, path: str, reason: str) -> None:
        message = f"Failed to load model: {reason}"
        super().__init__(message, details={"path": path, "reason": reason})


class ModelSaveError(ModelError):
    """Raised when model saving fails."""

    def __init__(self, path: str, reason: str) -> None:
        message = f"Failed to save model: {reason}"
        super().__init__(message, details={"path": path, "reason": reason})


class ModelInferenceError(ModelError):
    """Raised when model inference fails."""

    def __init__(self, reason: str, *, input_shape: tuple | None = None) -> None:
        message = f"Model inference failed: {reason}"
        details: dict[str, Any] = {"reason": reason}
        if input_shape:
            details["input_shape"] = input_shape
        super().__init__(message, details=details)


# =============================================================================
# Training Layer Exceptions
# =============================================================================


class TrainingError(MLFXError):
    """Base exception for training-related errors."""

    pass


class TrainingConfigError(TrainingError):
    """Raised when training configuration is invalid."""

    def __init__(self, param: str, value: Any, reason: str) -> None:
        message = f"Invalid training config: {param}={value!r} - {reason}"
        super().__init__(message, details={"param": param, "value": value, "reason": reason})


class TrainingDataError(TrainingError):
    """Raised when training data is insufficient or invalid."""

    def __init__(self, reason: str, *, n_samples: int | None = None) -> None:
        message = f"Training data error: {reason}"
        details: dict[str, Any] = {"reason": reason}
        if n_samples is not None:
            details["n_samples"] = n_samples
        super().__init__(message, details=details)


class BackendNotFoundError(TrainingError):
    """Raised when a requested backend does not exist."""

    def __init__(self, backend: str, available: list[str]) -> None:
        message = f"Backend '{backend}' not found. Available: {', '.join(available)}"
        super().__init__(message, details={"backend": backend, "available": available})


# =============================================================================
# Pipeline Exceptions
# =============================================================================


class PipelineError(MLFXError):
    """Base exception for pipeline-related errors."""

    pass


class PipelineStageError(PipelineError):
    """Raised when a pipeline stage fails."""

    def __init__(self, stage: str, reason: str) -> None:
        message = f"Pipeline stage '{stage}' failed: {reason}"
        super().__init__(message, details={"stage": stage, "reason": reason})


class FeatureError(PipelineError):
    """Raised when feature engineering fails."""

    def __init__(self, feature: str, reason: str) -> None:
        message = f"Feature engineering error for '{feature}': {reason}"
        super().__init__(message, details={"feature": feature, "reason": reason})


# =============================================================================
# Configuration Exceptions
# =============================================================================


class ConfigError(MLFXError):
    """Base exception for configuration-related errors."""

    pass


class ConfigNotFoundError(ConfigError):
    """Raised when a configuration file does not exist."""

    def __init__(self, config_path: str) -> None:
        message = f"Configuration file not found: {config_path}"
        super().__init__(message, details={"config_path": config_path})


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        message = f"Configuration validation failed with {len(errors)} error(s)"
        super().__init__(message, details={"errors": errors})


# =============================================================================
# Registry Exceptions
# =============================================================================


class RegistryError(MLFXError):
    """Base exception for registry-related errors."""

    pass


class RegistryWriteError(RegistryError):
    """Raised when writing to the registry fails."""

    def __init__(self, key: str, reason: str) -> None:
        message = f"Failed to write to registry: {reason}"
        super().__init__(message, details={"key": key, "reason": reason})


class RegistryReadError(RegistryError):
    """Raised when reading from the registry fails."""

    def __init__(self, key: str, reason: str) -> None:
        message = f"Failed to read from registry: {reason}"
        super().__init__(message, details={"key": key, "reason": reason})


# =============================================================================
# Serving Exceptions
# =============================================================================


class ServingError(MLFXError):
    """Base exception for serving-related errors."""

    pass


class PredictionError(ServingError):
    """Raised when prediction fails."""

    def __init__(self, reason: str, *, model_id: str | None = None) -> None:
        message = f"Prediction failed: {reason}"
        details: dict[str, Any] = {"reason": reason}
        if model_id:
            details["model_id"] = model_id
        super().__init__(message, details=details)


class FeaturePreparationError(ServingError):
    """Raised when feature preparation for inference fails."""

    def __init__(self, reason: str, *, missing_features: list[str] | None = None) -> None:
        message = f"Feature preparation failed: {reason}"
        details: dict[str, Any] = {"reason": reason}
        if missing_features:
            details["missing_features"] = missing_features
        super().__init__(message, details=details)


# =============================================================================
# Monitoring Exceptions
# =============================================================================


class MonitoringError(MLFXError):
    """Base exception for monitoring-related errors."""

    pass


class DriftDetectionError(MonitoringError):
    """Raised when drift detection fails."""

    def __init__(self, reason: str, *, feature: str | None = None) -> None:
        message = f"Drift detection failed: {reason}"
        details: dict[str, Any] = {"reason": reason}
        if feature:
            details["feature"] = feature
        super().__init__(message, details=details)
