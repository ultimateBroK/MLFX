"""Pydantic-based configuration schemas for ML_FX.

All sections of config.toml are validated here.  ``AppConfig`` is the single
root model returned by ``load_config()``.  ``ServingSettings`` reads optional
environment-variable overrides for deployment-specific paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Section schemas
# ---------------------------------------------------------------------------

ValidSymbol = Annotated[str, Field(min_length=1)]
ValidTimeframe = Literal["1m", "5m", "15m", "30m", "1H", "2H", "4H", "1D"]


class DownloadConfig(BaseModel):
    """Configuration for the data-download stage."""

    symbol: ValidSymbol = "XAUUSD"
    asset_class: Literal["fx", "crypto"] = "fx"
    start_year: int = Field(default=2015, ge=2000, le=2100)
    start_month: int = Field(default=1, ge=1, le=12)
    concurrency: int = Field(default=20, ge=1, le=100)


class PipelineConfig(BaseModel):
    """Configuration for the OHLCV resampling stage."""

    symbol: ValidSymbol = "XAUUSD"
    timeframe: ValidTimeframe = "1H"
    pivot_type: Literal[
        "traditional", "fibonacci", "woodie", "camarilla", "demark"
    ] = "traditional"
    pivot_anchor: Literal["daily", "weekly", "monthly"] = "daily"
    atr_period: int = Field(default=14, ge=2, le=100)
    atr_mult: float = Field(default=0.5, gt=0)


class FeatureConfig(BaseModel):
    """Hyper-parameters for the feature-engineering stage."""

    rsi_period: int = Field(default=14, ge=2, le=100)
    atr_period: int = Field(default=14, ge=2, le=100)
    ema_periods: list[int] = Field(default=[20, 50, 200])
    macd_fast: int = Field(default=12, ge=2)
    macd_slow: int = Field(default=26, ge=2)
    macd_signal: int = Field(default=9, ge=2)
    avg_range_n: int = Field(default=5, ge=1)


class TrainConfig(BaseModel):
    """Configuration for model-training runs."""

    symbol: ValidSymbol = "XAUUSD"
    timeframe: ValidTimeframe = "1H"
    label_col: str = Field(default="label_10", min_length=1)
    backend: Literal[
        "mlf", "lstm", "bilstm", "transformer", "cnn_lstm", "sgd", "stats", "neuralforecast"
    ] = "mlf"
    n_trials: int = Field(default=30, ge=1)
    n_splits: int = Field(default=5, ge=2)
    random_seed: int = Field(default=42, ge=0)


class BacktestConfig(BaseModel):
    """Configuration for the backtesting stage."""

    symbol: ValidSymbol = "XAUUSD"
    timeframe: ValidTimeframe = "1H"
    label_col: str = Field(default="label_10", min_length=1)
    tp_r: float = Field(default=1.5, gt=0)
    sl_r: float = Field(default=1.0, gt=0)
    initial_capital: float = Field(default=10_000.0, gt=0)
    risk_pct: float = Field(default=1.0, gt=0)
    commission: float = Field(default=0.1, ge=0)


# ---------------------------------------------------------------------------
# Root config model
# ---------------------------------------------------------------------------


class AppConfig(BaseModel):
    """Root configuration object returned by ``load_config()``."""

    download: DownloadConfig = Field(default_factory=DownloadConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    features: FeatureConfig = Field(default_factory=FeatureConfig)
    train: TrainConfig = Field(default_factory=TrainConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)


# ---------------------------------------------------------------------------
# Deployment settings (environment-variable overrides)
# ---------------------------------------------------------------------------


class ServingSettings(BaseSettings):
    """Optional environment-variable overrides for deployment-specific paths.

    All variables are prefixed with ``MLFX_``.  Example::

        MLFX_DATA_ROOT=/mnt/data MLFX_LOG_LEVEL=DEBUG uvicorn mlfx.serving.api:app
    """

    model_config = SettingsConfigDict(env_prefix="MLFX_", case_sensitive=False)

    data_root: Path | None = None
    outputs_root: Path | None = None
    log_level: str = "INFO"
    max_cache_size: int = 32
