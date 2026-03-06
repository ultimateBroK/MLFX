"""
eval/run_eval.py
================
CLI entrypoint to run backtest simulation and generate reports
on a given labeled/predicted parquet dataset.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import polars as pl
from backtest import simulate_trades, compute_metrics  # local import
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from viz.charts import generate_full_report


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


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
    out_dir: str | Path = "outputs/reports",
) -> dict:
    """
    Run backtest on all available labeled data for a specific symbol/tf.
    """
    data_dir = Path("data/labels") / symbol / tf
    if not data_dir.exists():
        logger.error("Labels directory not found: %s. Run Pipeline first.", data_dir)
        return {}

    parquet_files = sorted(data_dir.glob("*.parquet"))
    if not parquet_files:
        logger.error("No labeled parquet files found in %s", data_dir)
        return {}

    logger.info("Loading %d labeled files from %s...", len(parquet_files), data_dir)
    frames = []
    for f in parquet_files:
        try:
            df = pl.read_parquet(f)
            frames.append(df)
        except Exception as e:
            logger.warning("Failed to load %s: %s", f, e)

    if not frames:
        return {}

    df = pl.concat(frames).sort("timestamp")

    logger.info("Total loaded rows: %d", len(df))
    logger.info(
        "Simulation config: Signal=%s TP=%.1fR SL=%.1fR Risk=%.1f%% Comm=%.2f",
        label_col,
        tp_r,
        sl_r,
        risk_pct,
        commission,
    )
    trades = simulate_trades(
        df, signal_col=label_col, tp_r=tp_r, sl_r=sl_r, commission=commission, slippage=slippage
    )

    metrics = compute_metrics(
        trades, initial_capital=initial_capital, risk_pct=risk_pct
    )

    logger.info("--- BACKTEST RESULTS ---")
    logger.info("Total Trades : %d", metrics["total_trades"])
    logger.info("Win Rate     : %.2f%%", metrics.get("win_rate", 0))
    logger.info("Profit Factor: %.2f", metrics.get("profit_factor", 0))
    logger.info("Max Drawdown : %.2f R", metrics.get("max_drawdown_r", 0))
    logger.info("Net Profit(R): %.2f R", metrics.get("total_r", 0))
    logger.info("Net Profit($): $%.2f", metrics.get("net_profit_dollar", 0))
    logger.info("Sharpe Ratio : %.2f", metrics.get("sharpe_ratio", 0))
    logger.info("Sortino Ratio: %.2f", metrics.get("sortino_ratio", 0))
    logger.info("Calmar Ratio : %.2f", metrics.get("calmar_ratio", 0))
    logger.info("Final Capital: $%.2f", metrics.get("final_capital", initial_capital))
    logger.info("------------------------")

    # Generate Visuals
    out_dir_path = Path(out_dir)
    logger.info("Generating visual reports...")
    out_name = f"{label_col}_R{int(tp_r * 10)}"
    try:
        generate_full_report(symbol, tf, df, trades, out_name, out_dir_path)
    except Exception as e:
        logger.error("Failed to generate report: %s", e)

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


def main():
    """Main execution point for evaluating the strategy by running a backtest on a specific dataset and creating a visual report."""
    parser = argparse.ArgumentParser(
        description="Run Full Walk-forward Backtest and Generate Reports"
    )
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to the labeled Parquet file (e.g. data/labels/XAUUSD/1H/2026-02.parquet)",
    )
    parser.add_argument(
        "--symbol", type=str, default="XAUUSD", help="Symbol name (for plot titles)"
    )
    parser.add_argument(
        "--tf", type=str, default="1H", help="Timeframe (for plot titles)"
    )
    parser.add_argument(
        "--label", type=str, default="label_10", help="Label column to use for signals"
    )
    parser.add_argument(
        "--tp", type=float, default=1.5, help="Take Profit R-multiple (default 1.5)"
    )
    parser.add_argument(
        "--sl", type=float, default=1.0, help="Stop Loss R-multiple (default 1.0)"
    )
    parser.add_argument(
        "--slippage", type=float, default=0.0, help="Slippage in price units (default 0.0)"
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="outputs/reports",
        help="Output directory for the generated charts",
    )

    args = parser.parse_args()
    data_path = Path(args.data)

    if not data_path.exists():
        logger.error("Dataset not found: %s", data_path)
        sys.exit(1)

    logger.info("Loading dataset: %s", data_path)
    df = pl.read_parquet(data_path)

    if df.is_empty():
        logger.error("Dataset is empty.")
        sys.exit(1)

    logger.info(
        "Running trade simulation (Signal: %s, TP: %.1fR, SL: %.1fR, Slippage: %.2f)",
        args.label,
        args.tp,
        args.sl,
        args.slippage,
    )
    trades = simulate_trades(df, signal_col=args.label, tp_r=args.tp, sl_r=args.sl, slippage=args.slippage)

    # Print metrics
    metrics = compute_metrics(trades)
    logger.info("--- BACKTEST RESULTS ---")
    logger.info("Total Trades : %d", metrics["total_trades"])
    logger.info("Win Rate     : %.2f%%", metrics["win_rate"])
    logger.info("Profit Factor: %.2f", metrics["profit_factor"])
    logger.info("Max Drawdown : %.2f R", metrics["max_drawdown_r"])
    logger.info("Net Profit   : %.2f R", metrics["total_r"])
    logger.info("Sharpe Ratio : %.2f", metrics["sharpe_ratio"])
    logger.info("Sortino Ratio: %.2f", metrics["sortino_ratio"])
    logger.info("Calmar Ratio : %.2f", metrics["calmar_ratio"])
    logger.info("------------------------")

    # Generate Visuals
    out_dir = Path(args.outdir)
    logger.info("Generating visual reports...")
    out_name = f"{args.label}_R{int(args.tp * 10)}"  # e.g. label_10_R15
    generate_full_report(args.symbol, args.tf, df, trades, out_name, out_dir)


if __name__ == "__main__":
    main()
