"""Consolidated CLI entrypoint for core MLFX workflows."""

from __future__ import annotations

import argparse
import logging

from mlfx.evaluation.runner import run_full_eval
from mlfx.ingestion.download import run_download_job
from mlfx.pipeline.feature_engineering import run_feature_pipeline
from mlfx.pipeline.labeling import run_label_pipeline
from mlfx.pipeline.qa_data import run_quality_audit
from mlfx.pipeline.resampling import resample_symbol_tf
from mlfx.training.config import TrainingConfig
from mlfx.training.runner import run_training

from rich.console import Console
from rich.table import Table

console = Console()


def build_parser() -> argparse.ArgumentParser:
    """Build the consolidated argument parser for download, pipeline, train, evaluate, serve, batch-predict, drift, and models."""
    parser = argparse.ArgumentParser(description="MLFX consolidated CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download", help="Download raw tick data")
    download.add_argument("--symbol", default="XAUUSD")
    download.add_argument("--asset-class", choices=["fx", "crypto"], default="fx")
    download.add_argument("--start-year", type=int, default=2015)
    download.add_argument("--start-month", type=int, default=1)
    download.add_argument("--concurrency", type=int, default=20)
    download.add_argument("--force", action=argparse.BooleanOptionalAction, default=True)

    pipeline = subparsers.add_parser("pipeline", help="Run ETL pipeline stages")
    pipeline.add_argument("--symbol", default="XAUUSD")
    pipeline.add_argument("--tf", default="1H")
    pipeline.add_argument("--pivot", default="traditional")
    pipeline.add_argument("--anchor", default="daily")
    pipeline.add_argument("--atr-period", type=int, default=14)
    pipeline.add_argument("--atr-mult", type=float, default=0.5)
    pipeline.add_argument("--force", action=argparse.BooleanOptionalAction, default=True)
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
    train.add_argument("--force", action=argparse.BooleanOptionalAction, default=True)

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

    serve = subparsers.add_parser("serve", help="Start the real-time inference API server")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true")

    batch = subparsers.add_parser("batch-predict", help="Run batch inference and write predictions")
    batch.add_argument("--symbol", default="XAUUSD")
    batch.add_argument("--tf", default="1H")
    batch.add_argument("--label", default="label_10")

    drift = subparsers.add_parser("drift", help="Detect feature drift vs training reference")
    drift.add_argument("--symbol", default="XAUUSD")
    drift.add_argument("--tf", default="1H")
    drift.add_argument("--label", default="label_10")
    drift.add_argument("--threshold-ks", type=float, default=0.1)
    drift.add_argument("--threshold-psi", type=float, default=0.2)

    models = subparsers.add_parser("models", help="List registered model versions")
    models.add_argument("--symbol", default=None)
    models.add_argument("--tf", default=None)
    models.add_argument("--backend", default=None)

    return parser


def main() -> None:
    try:
        from mlfx.monitoring.logging_config import configure_logging

        configure_logging(level="INFO")
    except Exception:
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
        cfg = TrainingConfig(
            symbol=args.symbol,
            tf=args.tf,
            label_col=args.label,
            backend=args.backend,
            n_trials=args.n_trials,
            n_splits=args.n_splits,
            force=args.force,
        )
        run_training(cfg)
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
        return

    if args.command == "serve":
        try:
            import uvicorn  # noqa: PLC0415
        except ImportError:
            logging.getLogger(__name__).error(
                "uvicorn not installed. Run: pip install fastapi uvicorn"
            )
            return
        uvicorn.run(
            "mlfx.serving.api:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
        return

    if args.command == "batch-predict":
        from mlfx.serving.batch import run_batch_inference  # noqa: PLC0415

        with console.status("[bold green]Running batch inference..."):
            result = run_batch_inference(
                symbol=args.symbol,
                tf=args.tf,
                label_col=args.label,
            )
        console.print(result)
        return

    if args.command == "drift":
        from mlfx.monitoring.drift import DriftDetector  # noqa: PLC0415
        from mlfx.training.data import load_labelled_dataset  # noqa: PLC0415

        with console.status("[bold green]Detecting feature drift..."):
            df = load_labelled_dataset(args.symbol, args.tf)
            if df is None:
                logging.getLogger(__name__).error("No data for %s %s", args.symbol, args.tf)
                return
            detector = DriftDetector.load(symbol=args.symbol, tf=args.tf)
            report = detector.detect(
                df,
                threshold_ks=args.threshold_ks,
                threshold_psi=args.threshold_psi,
            )
        console.print(report)
        return

    if args.command == "models":
        from mlfx.registry.models import get_registry  # noqa: PLC0415

        with console.status("[bold green]Fetching models..."):
            reg = get_registry()
            entries = reg.list_models(
                symbol=args.symbol,
                tf=args.tf,
                backend=args.backend,
            )
        
        if not entries:
            console.print("[yellow]No models found in the registry.[/yellow]")
            return
            
        table = Table(title="Registered Model Versions", show_header=True, header_style="bold magenta")
        
        # Determine all available keys for columns
        keys = []
        for e in entries:
            for k in e.keys():
                if k not in keys:
                    keys.append(k)
        
        # Standard columns first
        std_columns = ["symbol", "tf", "backend", "run_id", "accuracy"]
        ordered_keys = [k for k in std_columns if k in keys] + [k for k in keys if k not in std_columns]
        
        for k in ordered_keys:
            table.add_column(str(k))
            
        for e in entries:
            row = [str(e.get(k, "")) for k in ordered_keys]
            table.add_row(*row)
            
        console.print(table)
        return
