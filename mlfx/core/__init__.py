"""Core domain models, exceptions, and repository interfaces for MLFX.

This module provides the foundational building blocks for the MLFX system:
- Domain models: Symbol, Timeframe, Label, DataKey, ModelKey, etc.
- Exceptions: Structured error hierarchy for consistent error handling
- Repository: Data access patterns for clean separation of concerns

Example usage:

    from mlfx.core import (
        Symbol,
        Timeframe,
        Label,
        DataKey,
        ModelKey,
        MLFXError,
        DataNotFoundError,
        ParquetDataRepository,
        FileSystemModelRepository,
    )

    # Create domain objects
    symbol = Symbol("XAUUSD")
    tf = Timeframe.from_string("1H")
    label = Label("label_10")
    key = DataKey(symbol, tf, label)

    # Use repositories
    data_repo = ParquetDataRepository()
    df = data_repo.load_features("XAUUSD", "1H")

    # Handle errors
    try:
        ...
    except DataNotFoundError as e:
        print(f"Data not found: {e.details}")
"""

from __future__ import annotations

from .domain import (
    DataKey,
    EvaluationConfig,
    Label,
    ModelKey,
    OHLCVBar,
    Prediction,
    Symbol,
    Timeframe,
    TrainingHyperparams,
)
from .exceptions import (
    BackendNotFoundError,
    ConfigError,
    ConfigNotFoundError,
    ConfigValidationError,
    DataDownloadError,
    DataError,
    DataNotFoundError,
    DataParseError,
    DataValidationError,
    DriftDetectionError,
    FeatureError,
    FeaturePreparationError,
    MLFXError,
    ModelError,
    ModelInferenceError,
    ModelLoadError,
    ModelNotFoundError,
    ModelSaveError,
    MonitoringError,
    PipelineError,
    PipelineStageError,
    PredictionError,
    RegistryError,
    RegistryReadError,
    RegistryWriteError,
    ServingError,
    TrainingConfigError,
    TrainingDataError,
    TrainingError,
)
from .repository import (
    DEFAULT_DATA_REPO,
    DEFAULT_MODEL_REPO,
    DataRepository,
    FileSystemModelRepository,
    ModelRepository,
    ParquetDataRepository,
)

__all__ = [
    # Domain models
    "DataKey",
    "EvaluationConfig",
    "Label",
    "ModelKey",
    "OHLCVBar",
    "Prediction",
    "Symbol",
    "Timeframe",
    "TrainingHyperparams",
    # Exceptions - Base
    "MLFXError",
    # Exceptions - Data
    "DataError",
    "DataNotFoundError",
    "DataValidationError",
    "DataDownloadError",
    "DataParseError",
    # Exceptions - Model
    "ModelError",
    "ModelNotFoundError",
    "ModelLoadError",
    "ModelSaveError",
    "ModelInferenceError",
    # Exceptions - Training
    "TrainingError",
    "TrainingConfigError",
    "TrainingDataError",
    "BackendNotFoundError",
    # Exceptions - Pipeline
    "PipelineError",
    "PipelineStageError",
    "FeatureError",
    # Exceptions - Config
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    # Exceptions - Registry
    "RegistryError",
    "RegistryWriteError",
    "RegistryReadError",
    # Exceptions - Serving
    "ServingError",
    "PredictionError",
    "FeaturePreparationError",
    # Exceptions - Monitoring
    "MonitoringError",
    "DriftDetectionError",
    # Repository
    "DataRepository",
    "ModelRepository",
    "ParquetDataRepository",
    "FileSystemModelRepository",
    "DEFAULT_DATA_REPO",
    "DEFAULT_MODEL_REPO",
]
