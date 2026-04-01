"""Core domain models, exceptions, and repository interfaces for MLFX.

This module provides the foundational building blocks for the MLFX system:
- Domain models: Symbol, Timeframe, Label, DataKey, ModelKey, etc.
- Exceptions: 8 essential error classes for consistent error handling
- Repository: Data access patterns for clean separation of concerns

Example usage:

    from mlfx.core import (
        Symbol,
        Timeframe,
        Label,
        DataKey,
        ModelKey,
        MLFXError,
        DataError,
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
    except DataError as e:
        print(f"Data error: {e.details}")
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
    ConfigError,
    DataError,
    MLFXError,
    ModelError,
    PipelineError,
    RegistryError,
    TrainingError,
    ValidationError,
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
    # Exceptions - 8 essential classes
    "MLFXError",
    "DataError",
    "ModelError",
    "TrainingError",
    "ConfigError",
    "PipelineError",
    "RegistryError",
    "ValidationError",
    # Repository
    "DataRepository",
    "ModelRepository",
    "ParquetDataRepository",
    "FileSystemModelRepository",
    "DEFAULT_DATA_REPO",
    "DEFAULT_MODEL_REPO",
]
