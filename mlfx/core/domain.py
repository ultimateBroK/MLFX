"""Core domain models for MLFX.

This module defines the core domain entities and value objects used throughout
the MLFX system. These models provide type safety, validation, and a clear
contract for data exchange between modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class Timeframe(Enum):
    """Supported timeframe values for OHLCV data."""

    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1H"
    H4 = "4H"
    D1 = "1D"
    W1 = "1W"

    @classmethod
    def from_string(cls, value: str) -> "Timeframe":
        """Parse a timeframe string into a Timeframe enum."""
        normalized = value.upper().replace("-", "")
        mapping = {
            "1M": cls.M1,
            "5M": cls.M5,
            "15M": cls.M15,
            "30M": cls.M30,
            "1H": cls.H1,
            "4H": cls.H4,
            "1D": cls.D1,
            "1W": cls.W1,
        }
        if normalized not in mapping:
            valid = list(mapping.keys())
            raise ValueError(f"Invalid timeframe '{value}'. Valid options: {valid}")
        return mapping[normalized]

    @property
    def minutes(self) -> int:
        """Return the timeframe duration in minutes."""
        mapping = {
            Timeframe.M1: 1,
            Timeframe.M5: 5,
            Timeframe.M15: 15,
            Timeframe.M30: 30,
            Timeframe.H1: 60,
            Timeframe.H4: 240,
            Timeframe.D1: 1440,
            Timeframe.W1: 10080,
        }
        return mapping[self]


@dataclass(frozen=True, slots=True)
class Symbol:
    """A trading symbol (e.g., XAUUSD, EURUSD)."""

    code: str

    def __post_init__(self) -> None:
        if not self.code or not self.code.isalnum():
            raise ValueError(f"Invalid symbol code: '{self.code}'")
        object.__setattr__(self, "code", self.code.upper())

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return f"Symbol({self.code!r})"


@dataclass(frozen=True, slots=True)
class Label:
    """A label configuration for training/evaluation."""

    name: str  # e.g., "label_10"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Label name cannot be empty")
        object.__setattr__(self, "name", self.name.lower())

    @property
    def horizon(self) -> int:
        """Extract the prediction horizon from the label name."""
        # Assumes format: label_N or label_NN
        if self.name.startswith("label_"):
            try:
                return int(self.name.split("_")[1])
            except (IndexError, ValueError):
                pass
        return 0

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class DataKey:
    """A composite key for identifying data artifacts."""

    symbol: Symbol
    timeframe: Timeframe
    label: Label | None = None

    def __str__(self) -> str:
        base = f"{self.symbol.code}/{self.timeframe.value}"
        if self.label:
            return f"{base}/{self.label.name}"
        return base

    @classmethod
    def from_parts(
        cls,
        symbol: str,
        timeframe: str,
        label: str | None = None,
    ) -> "DataKey":
        """Create a DataKey from string components."""
        return cls(
            symbol=Symbol(symbol),
            timeframe=Timeframe.from_string(timeframe),
            label=Label(label) if label else None,
        )


@dataclass(frozen=True, slots=True)
class ModelKey:
    """A composite key for identifying trained models."""

    symbol: Symbol
    timeframe: Timeframe
    label: Label
    backend: str

    def __str__(self) -> str:
        return f"{self.symbol.code}/{self.timeframe.value}/{self.label.name}/{self.backend}"

    @classmethod
    def from_parts(
        cls,
        symbol: str,
        timeframe: str,
        label: str,
        backend: str,
    ) -> "ModelKey":
        """Create a ModelKey from string components."""
        return cls(
            symbol=Symbol(symbol),
            timeframe=Timeframe.from_string(timeframe),
            label=Label(label),
            backend=backend.lower(),
        )


@dataclass(frozen=True, slots=True)
class OHLCVBar:
    """A single OHLCV bar with timestamp."""

    timestamp: int  # Unix timestamp in milliseconds
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    tick_count: int = 0

    @property
    def range(self) -> float:
        """High - Low range."""
        return self.high - self.low

    @property
    def body(self) -> float:
        """Absolute body size (|close - open|)."""
        return abs(self.close - self.open)

    @property
    def is_bullish(self) -> bool:
        """True if close > open."""
        return self.close > self.open


@dataclass
class Prediction:
    """A model prediction with confidence."""

    value: int  # Predicted class (0, 1, 2 for down/neutral/up)
    confidence: float  # Probability of predicted class
    probabilities: list[float] = field(default_factory=list)  # All class probabilities

    @property
    def direction(self) -> Literal["down", "neutral", "up"]:
        """Map prediction value to direction string."""
        mapping = {0: "down", 1: "neutral", 2: "up"}
        return mapping.get(self.value, "neutral")


@dataclass(frozen=True, slots=True)
class TrainingHyperparams:
    """Training hyperparameters configuration."""

    n_trials: int = 20
    n_splits: int = 5
    top_k_features: int = 50
    seq_len: int = 60
    epochs: int = 50
    batch_size: int = 32
    patience: int = 10
    seed: int = 42

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "n_trials": self.n_trials,
            "n_splits": self.n_splits,
            "top_k_features": self.top_k_features,
            "seq_len": self.seq_len,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "patience": self.patience,
            "seed": self.seed,
        }


@dataclass(frozen=True, slots=True)
class EvaluationConfig:
    """Configuration for backtest evaluation."""

    initial_capital: float = 10000.0
    risk_pct: float = 1.0
    commission: float = 0.0
    tp_r: float = 1.5
    sl_r: float = 1.0
    slippage: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "initial_capital": self.initial_capital,
            "risk_pct": self.risk_pct,
            "commission": self.commission,
            "tp_r": self.tp_r,
            "sl_r": self.sl_r,
            "slippage": self.slippage,
        }
