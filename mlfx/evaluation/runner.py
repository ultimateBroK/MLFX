"""Evaluation runner with centralized path resolution."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import polars as pl

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths
from mlfx.training.data import load_labelled_dataset

from .backtest import compute_metrics, map_ordinal_to_signal, simulate_trades
from .reporting import generate_full_report

logger = logging.getLogger(__name__)


def get_baseline_metrics(
    symbol: str,
    tf: str,
    label_col: str,
    initial_capital: float = 10000.0,
    risk_pct: float = 1.0,
    commission: float = 0.1,
    tp_r: float = 1.5,
    sl_r: float = 1.0,
    slippage: float = 0.0,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> dict[str, float] | None:
    """Run backtest on labels and return raw metrics (no report). For baseline comparison."""
    df = load_labelled_dataset(symbol, tf, paths=paths)
    if df is None or df.is_empty() or label_col not in df.columns:
        return None
    df_mapped = df.with_columns(map_ordinal_to_signal(pl.col(label_col)).alias("_bt_signal"))
    trades = simulate_trades(
        df_mapped,
        signal_col="_bt_signal",
        tp_r=tp_r,
        sl_r=sl_r,
        commission=commission,
        slippage=slippage,
    )
    return compute_metrics(trades, initial_capital=initial_capital, risk_pct=risk_pct)


def run_full_eval(
    symbol: str,
    tf: str,
    label_col: str,
    initial_capital: float = 10000.0,
    risk_pct: float = 1.0,
    commission: float = 0.1,
    tp_r: float = 1.5,
    sl_r: float = 1.0,
    slippage: float = 0.0,
    out_dir: str | Path | None = None,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> dict[str, str]:
    """Run backtest on all labeled parquet files for one symbol/timeframe."""
    df = load_labelled_dataset(symbol, tf, paths=paths)
    if df is None or df.is_empty():
        logger.error("No labeled data found for %s %s", symbol, tf)
        return {}

    return run_dataset_eval(
        df,
        symbol=symbol,
        tf=tf,
        label_col=label_col,
        initial_capital=initial_capital,
        risk_pct=risk_pct,
        commission=commission,
        tp_r=tp_r,
        sl_r=sl_r,
        slippage=slippage,
        out_dir=out_dir,
        paths=paths,
    )


def run_dataset_eval(
    df: pl.DataFrame,
    *,
    symbol: str,
    tf: str,
    label_col: str,
    initial_capital: float = 10000.0,
    risk_pct: float = 1.0,
    commission: float = 0.1,
    tp_r: float = 1.5,
    sl_r: float = 1.0,
    slippage: float = 0.0,
    out_dir: str | Path | None = None,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> dict[str, str]:
    """Run backtest/report generation for a provided labelled dataset.

    Maps ordinal labels (-2,-1,0,1,2) to signals: 2,1→LONG; -1,-2→SHORT; 0→skip.
    """
    if df.is_empty():
        logger.error("Dataset is empty for %s %s", symbol, tf)
        return {}

    df_mapped = df.with_columns(
        map_ordinal_to_signal(pl.col(label_col)).alias("_bt_signal")
    )
    trades = simulate_trades(
        df_mapped,
        signal_col="_bt_signal",
        tp_r=tp_r,
        sl_r=sl_r,
        commission=commission,
        slippage=slippage,
    )
    metrics = compute_metrics(
        trades,
        initial_capital=initial_capital,
        risk_pct=risk_pct,
    )

    report_dir = (Path(out_dir) / symbol / tf) if out_dir is not None else paths.reports_dir(symbol, tf)
    out_name = f"{label_col}_R{int(tp_r * 10)}"
    generate_full_report(symbol, tf, df, trades, out_name, report_dir)

    return {
        "Total Trades": f"{metrics['total_trades']}",
        "Win Rate (%)": f"{metrics['win_rate']:.2f}%",
        "Profit Factor": f"{metrics['profit_factor']:.2f}",
        "Net Profit (R)": f"{metrics['total_r']:.2f}R",
        "Net Profit ($)": f"${metrics['net_profit_dollar']:.2f}",
        "Sharpe Ratio": f"{metrics['sharpe_ratio']:.2f}",
        "Sortino Ratio": f"{metrics['sortino_ratio']:.2f}",
        "Calmar Ratio": f"{metrics['calmar_ratio']:.2f}",
        "Final Capital ($)": f"${metrics['final_capital']:.2f}",
    }


def run_model_backtest(
    symbol: str,
    tf: str,
    label_col: str,
    initial_capital: float = 10000.0,
    risk_pct: float = 1.0,
    commission: float = 0.1,
    tp_r: float = 1.5,
    sl_r: float = 1.0,
    slippage: float = 0.0,
    out_dir: str | Path | None = None,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> dict[str, str] | None:
    """Run backtest on model predictions (not labels).

    Loads the best registered model, predicts on the dataset, then backtests.
    Returns None if no model is registered or inference fails.
    """
    df = load_labelled_dataset(symbol, tf, paths=paths)
    if df is None or df.is_empty():
        logger.error("No labeled data found for %s %s", symbol, tf)
        return None

    from mlfx.serving.core import resolve_and_predict

    result = resolve_and_predict(symbol, tf, label_col, df)
    if result is None:
        logger.warning("No registered model for %s/%s/%s — run train first", symbol, tf, label_col)
        return None

    predictions: np.ndarray
    predictions, _, _ = result
    df = df.with_columns(pl.Series("prediction", predictions.tolist(), dtype=pl.Int8))
    df = df.with_columns(map_ordinal_to_signal(pl.col("prediction")).alias("_bt_signal"))

    trades = simulate_trades(
        df,
        signal_col="_bt_signal",
        tp_r=tp_r,
        sl_r=sl_r,
        commission=commission,
        slippage=slippage,
    )
    metrics = compute_metrics(
        trades,
        initial_capital=initial_capital,
        risk_pct=risk_pct,
    )

    report_dir = (Path(out_dir) / symbol / tf) if out_dir else paths.reports_dir(symbol, tf)
    out_name = f"model_{label_col}_R{int(tp_r * 10)}"
    generate_full_report(symbol, tf, df, trades, out_name, report_dir)

    return {
        "Total Trades": f"{metrics['total_trades']}",
        "Win Rate (%)": f"{metrics['win_rate']:.2f}%",
        "Profit Factor": f"{metrics['profit_factor']:.2f}",
        "Net Profit (R)": f"{metrics['total_r']:.2f}R",
        "Net Profit ($)": f"${metrics['net_profit_dollar']:.2f}",
        "Sharpe Ratio": f"{metrics['sharpe_ratio']:.2f}",
        "Sortino Ratio": f"{metrics['sortino_ratio']:.2f}",
        "Calmar Ratio": f"{metrics['calmar_ratio']:.2f}",
        "Final Capital ($)": f"${metrics['final_capital']:.2f}",
    }
