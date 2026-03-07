"""Consolidated CLI entrypoint for core ML_FX workflows."""

from __future__ import annotations

import argparse
import logging

from mlfx.evaluation.runner import run_full_eval
from mlfx.ingestion.download import run_download_job
from mlfx.pipeline.feature_engineering import run_feature_pipeline
from mlfx.pipeline.labeling import run_label_pipeline
from mlfx.pipeline.qa_data import run_quality_audit
from mlfx.pipeline.resampling import resample_symbol_tf
from mlfx.training.registry import get_backend_runner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ML_FX consolidated CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download", help="Download raw tick data")
    download.add_argument("--symbol", default="XAUUSD")
    download.add_argument("--asset-class", choices=["fx", "crypto"], default="fx")
    download.add_argument("--start-year", type=int, default=2015)
    download.add_argument("--start-month", type=int, default=1)
    download.add_argument("--concurrency", type=int, default=20)
    download.add_argument("--force", action="store_true")

    pipeline = subparsers.add_parser("pipeline", help="Run ETL pipeline stages")
    pipeline.add_argument("--symbol", default="XAUUSD")
    pipeline.add_argument("--tf", default="1H")
    pipeline.add_argument("--pivot", default="traditional")
    pipeline.add_argument("--anchor", default="daily")
    pipeline.add_argument("--atr-period", type=int, default=14)
    pipeline.add_argument("--atr-mult", type=float, default=0.5)
    pipeline.add_argument("--force", action="store_true")
    pipeline.add_argument("--skip-resample", action="store_true")
    pipeline.add_argument("--skip-features", action="store_true")
    pipeline.add_argument("--skip-labels", action="store_true")

    qa = subparsers.add_parser("qa", help="Audit raw downloaded tick data")
    qa.add_argument("--symbol", default="XAUUSD")
    qa.add_argument("--asset-class", choices=["fx", "crypto"], default="fx")

    train = subparsers.add_parser("train", help="Train one model backend")
    train.add_argument("--symbol", default="XAUUSD")
    train.add_argument("--tf", default="1H")
    train.add_argument("--label", default="label_10")
    train.add_argument("--backend", default="mlf")
    train.add_argument("--n-trials", type=int, default=15)
    train.add_argument("--n-splits", type=int, default=5)
    train.add_argument("--force", action="store_true")

    evaluate = subparsers.add_parser("evaluate", help="Run full symbol backtest")
    evaluate.add_argument("--symbol", default="XAUUSD")
    evaluate.add_argument("--tf", default="1H")
    evaluate.add_argument("--label", default="label_10")
    evaluate.add_argument("--capital", type=float, default=10000.0)
    evaluate.add_argument("--risk", type=float, default=1.0)
    evaluate.add_argument("--commission", type=float, default=0.1)
    evaluate.add_argument("--tp", type=float, default=1.5)
    evaluate.add_argument("--sl", type=float, default=1.0)
    evaluate.add_argument("--slippage", type=float, default=0.0)

    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "download":
        run_download_job(
            symbol=args.symbol,
            asset_class=args.asset_class,
            start_year=args.start_year,
            start_month=args.start_month,
            concurrency=args.concurrency,
            force=args.force,
        )
        return

    if args.command == "pipeline":
        if not args.skip_resample:
            resample_symbol_tf(symbol=args.symbol, tf=args.tf, force=args.force)
        if not args.skip_features:
            run_feature_pipeline(
                symbol=args.symbol,
                tf=args.tf,
                pivot_type=args.pivot,
                pivot_anchor=args.anchor,
                force=args.force,
            )
        if not args.skip_labels:
            run_label_pipeline(
                symbol=args.symbol,
                tf=args.tf,
                atr_period=args.atr_period,
                atr_mult=args.atr_mult,
                force=args.force,
            )
        return

    if args.command == "train":
        runner = get_backend_runner(args.backend)
        runner_kwargs = {
            "symbol": args.symbol,
            "tf": args.tf,
            "label_col": args.label,
            "force": args.force,
        }
        if args.backend == "mlf":
            runner_kwargs["n_trials"] = args.n_trials
            runner_kwargs["n_splits"] = args.n_splits
        elif args.backend == "stats":
            runner_kwargs["n_splits"] = args.n_splits
        elif args.backend == "neuralforecast":
            runner_kwargs["n_windows"] = args.n_splits
        runner(**runner_kwargs)
        return

    if args.command == "qa":
        run_quality_audit(
            symbol=args.symbol,
            asset_class=args.asset_class,
        )
        return

    if args.command == "evaluate":
        run_full_eval(
            symbol=args.symbol,
            tf=args.tf,
            label_col=args.label,
            initial_capital=args.capital,
            risk_pct=args.risk,
            commission=args.commission,
            tp_r=args.tp,
            sl_r=args.sl,
            slippage=args.slippage,
        )
