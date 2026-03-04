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


def main():
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
        "--outdir",
        type=str,
        default="reports",
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
        "Running trade simulation (Signal: %s, TP: %.1fR, SL: %.1fR)",
        args.label,
        args.tp,
        args.sl,
    )
    trades = simulate_trades(df, signal_col=args.label, tp_r=args.tp, sl_r=args.sl)

    # In ra metrics
    metrics = compute_metrics(trades)
    logger.info("--- BACKTEST RESULTS ---")
    logger.info("Total Trades : %d", metrics["total_trades"])
    logger.info("Win Rate     : %.2f%%", metrics["win_rate"])
    logger.info("Profit Factor: %.2f", metrics["profit_factor"])
    logger.info("Max Drawdown : %.2f R", metrics["max_drawdown_r"])
    logger.info("Net Profit   : %.2f R", metrics["total_r"])
    logger.info("------------------------")

    # Generate Visuals
    out_dir = Path(args.outdir)
    logger.info("Generating visual reports...")
    out_name = f"{args.label}_R{int(args.tp * 10)}"  # e.g. label_10_R15
    generate_full_report(args.symbol, args.tf, df, trades, out_name, out_dir)


if __name__ == "__main__":
    main()
