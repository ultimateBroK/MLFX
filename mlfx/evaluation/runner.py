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


def _log_eval_to_mlflow(
    symbol: str,
    tf: str,
    label: str,
    metrics: dict[str, float],
    report_dir: Path,
    eval_type: str = "labels",
    backend: str | None = None,
) -> None:
    """Log evaluation results to MLflow if available."""
    try:
        import mlflow  # noqa: PLC0415

        from mlfx.config.mlflow import get_mlflow_config

        config = get_mlflow_config()
        if not config.is_mlflow_available():
            return

        config.setup_mlflow()

        # Set experiment for this evaluation
        experiment_name = config.experiment_name(
            symbol=symbol, tf=tf, label=label, backend=backend
        )
        mlflow.set_experiment(f"{experiment_name}/evaluation")

        # Start evaluation run
        run_name = f"eval_{eval_type}_{symbol}_{tf}_{label}"
        with mlflow.start_run(run_name=run_name):
            # Log params
            mlflow.log_params({
                "symbol": symbol,
                "tf": tf,
                "label": label,
                "eval_type": eval_type,
                "backend": backend or "none",
            })

            # Log metrics
            mlflow.log_metrics(metrics)

            # Log report directory as artifacts
            if report_dir.exists():
                for artifact in report_dir.iterdir():
                    if artifact.is_file():
                        mlflow.log_artifact(str(artifact), artifact_path="reports")

        logger.debug("Logged evaluation to MLflow: %s", run_name)

    except ImportError:
        logger.debug("MLflow not installed; skipping evaluation logging.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to log evaluation to MLflow: %s", exc)


def get_baseline_metrics(
    symbol: str,
    tf: str,
    label: str,
    initial_capital: float = 10000.0,
    risk_pct: float = 1.0,
    commission: float = 0.1,
    tp_r: float = 1.5,
    sl_r: float = 1.0,
    slippage: float = 0.0,
    train_start: str | None = None,
    train_end: str | None = None,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> dict[str, float] | None:
    """Run backtest on labels and return raw metrics (no report). For baseline comparison."""
    df = load_labelled_dataset(
        symbol,
        tf,
        paths=paths,
        train_start=train_start,
        train_end=train_end,
    )
    if df is None or df.is_empty() or label not in df.columns:
        return None
    df_mapped = df.with_columns(map_ordinal_to_signal(pl.col(label)).alias("_bt_signal"))
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
    label: str,
    initial_capital: float = 10000.0,
    risk_pct: float = 1.0,
    commission: float = 0.1,
    tp_r: float = 1.5,
    sl_r: float = 1.0,
    slippage: float = 0.0,
    out_dir: str | Path | None = None,
    train_start: str | None = None,
    train_end: str | None = None,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> dict[str, str]:
    """Run backtest on all labeled parquet files for one symbol/timeframe."""
    df = load_labelled_dataset(
        symbol,
        tf,
        paths=paths,
        train_start=train_start,
        train_end=train_end,
    )
    if df is None or df.is_empty():
        logger.error("No labeled data found for %s %s", symbol, tf)
        return {}

    return run_dataset_eval(
        df,
        symbol=symbol,
        tf=tf,
        label=label,
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
    label: str,
    initial_capital: float = 10000.0,
    risk_pct: float = 1.0,
    commission: float = 0.1,
    tp_r: float = 1.5,
    sl_r: float = 1.0,
    slippage: float = 0.0,
    out_dir: str | Path | None = None,
    paths: ProjectPaths = DEFAULT_PATHS,
    log_to_mlflow: bool = True,
) -> dict[str, str]:
    """Run backtest/report generation for a provided labelled dataset.

    Maps ordinal labels (-2,-1,0,1,2) to signals: 2,1→LONG; -1,-2→SHORT; 0→skip.
    """
    if df.is_empty():
        logger.error("Dataset is empty for %s %s", symbol, tf)
        return {}

    df_mapped = df.with_columns(
        map_ordinal_to_signal(pl.col(label)).alias("_bt_signal")
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

    risk_dir = f"R{int(tp_r * 10)}"
    report_dir = (
        Path(out_dir) / symbol / tf / label / "labels" / risk_dir
        if out_dir is not None
        else paths.reports_dir(symbol, tf) / label / "labels" / risk_dir
    )
    out_name = f"{label}_R{int(tp_r * 10)}"
    generate_full_report(symbol, tf, df, trades, out_name, report_dir)

    # Log to MLflow
    if log_to_mlflow:
        _log_eval_to_mlflow(
            symbol=symbol,
            tf=tf,
            label=label,
            metrics=metrics,
            report_dir=report_dir,
            eval_type="labels",
        )

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
    label: str,
    initial_capital: float = 10000.0,
    risk_pct: float = 1.0,
    commission: float = 0.1,
    tp_r: float = 1.5,
    sl_r: float = 1.0,
    slippage: float = 0.0,
    out_dir: str | Path | None = None,
    train_start: str | None = None,
    train_end: str | None = None,
    *,
    backend: str | None = None,
    paths: ProjectPaths = DEFAULT_PATHS,
    log_to_mlflow: bool = True,
) -> dict[str, str] | None:
    """Run backtest on model predictions (not labels).

    Loads the best registered model for the given backend (or any backend if None),
    predicts on the dataset, then backtests.
    Returns None if no model is registered or inference fails.
    """
    df = load_labelled_dataset(
        symbol,
        tf,
        paths=paths,
        train_start=train_start,
        train_end=train_end,
    )
    if df is None or df.is_empty():
        logger.error("No labeled data found for %s %s", symbol, tf)
        return None

    from mlfx.serving.core import resolve_and_predict

    result = resolve_and_predict(symbol, tf, label, df, backend=backend)
    if result is None:
        logger.warning("No registered model for %s/%s/%s — run train first", symbol, tf, label)
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

    risk_dir = f"R{int(tp_r * 10)}"
    report_dir = (
        Path(out_dir) / symbol / tf / label / "model" / risk_dir
        if out_dir
        else paths.reports_dir(symbol, tf) / label / "model" / risk_dir
    )
    out_name = f"model_{label}_R{int(tp_r * 10)}"
    generate_full_report(symbol, tf, df, trades, out_name, report_dir)

    # Log to MLflow
    if log_to_mlflow:
        _log_eval_to_mlflow(
            symbol=symbol,
            tf=tf,
            label=label,
            metrics=metrics,
            report_dir=report_dir,
            eval_type="model",
            backend=backend,
        )

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
