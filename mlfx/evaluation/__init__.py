"""Evaluation and reporting orchestration."""

from .backtest import compute_metrics, map_ordinal_to_signal, simulate_trades
from .reporting import generate_full_report
from .runner import (
    get_baseline_metrics,
    run_dataset_eval,
    run_full_eval,
    run_model_backtest,
)

__all__ = [
    "compute_metrics",
    "generate_full_report",
    "get_baseline_metrics",
    "map_ordinal_to_signal",
    "run_dataset_eval",
    "run_full_eval",
    "run_model_backtest",
    "simulate_trades",
]
