"""Evaluation and reporting orchestration."""

from .backtest import compute_metrics, simulate_trades
from .reporting import generate_full_report
from .runner import load_labelled_dataset, run_dataset_eval, run_full_eval

__all__ = [
    "compute_metrics",
    "generate_full_report",
    "load_labelled_dataset",
    "run_dataset_eval",
    "run_full_eval",
    "simulate_trades",
]
