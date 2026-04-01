"""Custom exception hierarchy for MLFX.

This module defines a focused exception hierarchy with 8 essential classes:
- MLFXError: Base for all MLFX errors
- DataError: Data loading, validation, parsing, download issues
- ModelError: Model lifecycle (load, save, inference, not found)
- TrainingError: Training configuration, data, backend issues
- ConfigError: Configuration loading and validation
- PipelineError: Pipeline stages and feature engineering
- RegistryError: Model registry operations
- ValidationError: Input/data validation failures
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


class DataError(MLFXError):
    """Raised for data-related errors (loading, validation, parsing, download)."""

    def __init__(
        self,
        message: str,
        *,
        data_type: str | None = None,
        symbol: str | None = None,
        path: str | None = None,
        reason: str | None = None,
        **kwargs: Any,
    ) -> None:
        details: dict[str, Any] = kwargs
        if data_type:
            details["data_type"] = data_type
        if symbol:
            details["symbol"] = symbol
        if path:
            details["path"] = path
        if reason:
            details["reason"] = reason
        super().__init__(message, details=details)


class ModelError(MLFXError):
    """Raised for model lifecycle errors (load, save, inference, not found)."""

    def __init__(
        self,
        message: str,
        *,
        model_id: str | None = None,
        path: str | None = None,
        reason: str | None = None,
        **kwargs: Any,
    ) -> None:
        details: dict[str, Any] = kwargs
        if model_id:
            details["model_id"] = model_id
        if path:
            details["path"] = path
        if reason:
            details["reason"] = reason
        super().__init__(message, details=details)


class TrainingError(MLFXError):
    """Raised for training-related errors (config, data, backend)."""

    def __init__(
        self,
        message: str,
        *,
        backend: str | None = None,
        param: str | None = None,
        reason: str | None = None,
        **kwargs: Any,
    ) -> None:
        details: dict[str, Any] = kwargs
        if backend:
            details["backend"] = backend
        if param:
            details["param"] = param
        if reason:
            details["reason"] = reason
        super().__init__(message, details=details)


class ConfigError(MLFXError):
    """Raised for configuration errors (loading, validation, not found)."""

    def __init__(
        self,
        message: str,
        *,
        config_path: str | None = None,
        errors: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        details: dict[str, Any] = kwargs
        if config_path:
            details["config_path"] = config_path
        if errors:
            details["errors"] = errors
        super().__init__(message, details=details)


class PipelineError(MLFXError):
    """Raised for pipeline stage and feature engineering errors."""

    def __init__(
        self,
        message: str,
        *,
        stage: str | None = None,
        feature: str | None = None,
        **kwargs: Any,
    ) -> None:
        details: dict[str, Any] = kwargs
        if stage:
            details["stage"] = stage
        if feature:
            details["feature"] = feature
        super().__init__(message, details=details)


class RegistryError(MLFXError):
    """Raised for model registry read/write errors."""

    def __init__(
        self,
        message: str,
        *,
        key: str | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        details: dict[str, Any] = kwargs
        if key:
            details["key"] = key
        if operation:
            details["operation"] = operation
        super().__init__(message, details=details)


class ValidationError(MLFXError):
    """Raised when input/data validation fails."""

    def __init__(
        self,
        message: str,
        *,
        column: str | None = None,
        row: int | None = None,
        missing: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        details: dict[str, Any] = kwargs
        if column:
            details["column"] = column
        if row is not None:
            details["row"] = row
        if missing:
            details["missing"] = missing
        super().__init__(message, details=details)
