"""Consolidated CLI entrypoint for core MLFX workflows."""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import sys
import time

from rich.console import Console
from rich.table import Table

from mlfx.evaluation.runner import (
    get_baseline_metrics,
    run_full_eval,
    run_model_backtest,
)
from mlfx.ingestion.download import run_download_job
from mlfx.pipeline.feature_engineering import run_feature_pipeline
from mlfx.pipeline.labeling import run_label_pipeline
from mlfx.pipeline.qa_data import run_quality_audit
from mlfx.pipeline.resampling import resample_symbol_tf
from mlfx.training.backends.base import TrainingConfig
from mlfx.training.registry import BACKEND_REGISTRY
from mlfx.training.runner import run_training

console = Console()

_ALL_BACKENDS = sorted(BACKEND_REGISTRY)


def build_parser() -> argparse.ArgumentParser:
    """Build the consolidated argument parser for download, pipeline, train, evaluate, serve, batch-predict, drift, models, and benchmark."""
    parser = argparse.ArgumentParser(
        description="MLFX — Machine Learning for Forex. Terminal-first workflow.",
        epilog="Examples:\n"
               "  mlfx download --symbol XAUUSD --start-year 2020\n"
               "  mlfx pipeline --tf 1H\n"
               "  mlfx train --backend bilstm --n-trials 20\n"
               "  mlfx benchmark --backends mlf bilstm lstm --n-trials 10\n"
               "  mlfx evaluate --tp 2.0 --sl 1.0\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    download = subparsers.add_parser(
        "download",
        help="Download raw tick data from Dukascopy",
        description="Download historical tick data for a symbol.",
    )
    download.add_argument("--symbol", default="XAUUSD", help="Symbol to download (default: XAUUSD)")
    download.add_argument("--asset-class", choices=["fx", "crypto"], default="fx", help="Asset class (default: fx)")
    download.add_argument("--start-year", type=int, default=2015, help="Start year (default: 2015)")
    download.add_argument("--start-month", type=int, default=1, help="Start month 1-12 (default: 1)")
    download.add_argument("--end-year", type=int, default=None, help="End year (default: current year)")
    download.add_argument("--end-month", type=int, default=None, help="End month (default: current month)")
    download.add_argument("--concurrency", type=int, default=20, help="Parallel downloads (default: 20)")
    download.add_argument("--force", action=argparse.BooleanOptionalAction, default=True, help="Force re-verify existing months")
    download.add_argument("--skip-current-month", action="store_true", help="Skip checking/repairing current month")

    pipeline = subparsers.add_parser(
        "pipeline",
        help="Run ETL pipeline: resample → features → labels",
        description="Execute the full data pipeline for one or more timeframes.",
    )
    pipeline.add_argument("--symbol", default="XAUUSD", help="Symbol (default: XAUUSD)")
    pipeline.add_argument(
        "--tf",
        nargs="+",
        default=["1H"],
        metavar="TF",
        help="Timeframe(s) to process: 1m, 5m, 15m, 30m, 1H, 2H, 4H, 1D (default: 1H)",
    )
    pipeline.add_argument("--pivot", default="traditional", help="Pivot type: traditional, fibonacci, woodie, classic, demark, camarilla (default: traditional)")
    pipeline.add_argument("--anchor", default="daily", help="Pivot anchor: daily, weekly, monthly (default: daily)")
    pipeline.add_argument("--atr-period", type=int, default=14, help="ATR period for label generation (default: 14)")
    pipeline.add_argument("--atr-mult", type=float, default=0.5, help="ATR multiplier for label thresholds (default: 0.5)")
    pipeline.add_argument("--force", action=argparse.BooleanOptionalAction, default=True, help="Overwrite existing files")
    pipeline.add_argument("--skip-resample", action="store_true", help="Skip tick → OHLCV resampling")
    pipeline.add_argument("--skip-features", action="store_true", help="Skip feature engineering")
    pipeline.add_argument("--skip-labels", action="store_true", help="Skip label generation")

    qa = subparsers.add_parser(
        "qa",
        help="Audit raw downloaded tick data",
        description="Run quality checks on downloaded raw tick data.",
    )
    qa.add_argument("--symbol", default="XAUUSD", help="Symbol to audit (default: XAUUSD)")
    qa.add_argument("--asset-class", choices=["fx", "crypto"], default="fx", help="Asset class (default: fx)")

    train = subparsers.add_parser(
        "train",
        help="Train a single model backend",
        description="Train one backend with Optuna HPO and CV.",
    )
    train.add_argument("--symbol", default="XAUUSD", help="Symbol (default: XAUUSD)")
    train.add_argument("--tf", default="1H", help="Timeframe (default: 1H)")
    train.add_argument("--label", default="label_10", help="Label column: label_5, label_10, label_20 (default: label_10)")
    train.add_argument(
        "--backend",
        default="mlf",
        choices=_ALL_BACKENDS,
        metavar="BACKEND",
        help=f"Model backend. Options: {', '.join(_ALL_BACKENDS)} (default: mlf)",
    )
    train.add_argument("--n-trials", type=int, default=15, help="Optuna trials for HPO (default: 15)")
    train.add_argument("--n-splits", type=int, default=5, help="TimeSeriesSplit folds (default: 5)")
    train.add_argument("--train-start", default=None, help="Inclusive training start date in compact format YYYYMMDD, e.g. 20240101")
    train.add_argument("--train-end", default=None, help="Inclusive training end date in compact format YYYYMMDD, e.g. 20241231")
    train.add_argument("--force", action=argparse.BooleanOptionalAction, default=True, help="Force retrain (overwrite saved model)")

    evaluate = subparsers.add_parser(
        "evaluate",
        help="Run walk-forward backtest",
        description="Backtest a trained model or baseline labels.",
    )
    evaluate.add_argument("--symbol", default="XAUUSD", help="Symbol (default: XAUUSD)")
    evaluate.add_argument("--tf", default="1H", help="Timeframe (default: 1H)")
    evaluate.add_argument("--label", default="label_10", help="Label column (default: label_10)")
    evaluate.add_argument("--capital", type=float, default=10000.0, help="Initial capital in USD (default: 10000)")
    evaluate.add_argument("--risk", type=float, default=1.0, help="Risk per trade %% (default: 1.0)")
    evaluate.add_argument("--commission", type=float, default=0.1, help="Commission in pips (default: 0.1)")
    evaluate.add_argument("--tp", type=float, default=1.5, help="Take-profit in R multiples (default: 1.5)")
    evaluate.add_argument("--sl", type=float, default=1.0, help="Stop-loss in R multiples (default: 1.0)")
    evaluate.add_argument("--slippage", type=float, default=0.0, help="Slippage in pips (default: 0.0)")
    evaluate.add_argument("--eval-start", default=None, help="Inclusive evaluation start date in compact format YYYYMMDD, e.g. 20240101")
    evaluate.add_argument("--eval-end", default=None, help="Inclusive evaluation end date in compact format YYYYMMDD, e.g. 20241231")
    evaluate.add_argument(
        "--use-labels",
        action="store_true",
        help="Backtest labels only (baseline). Default: backtest model if trained, else labels.",
    )

    serve = subparsers.add_parser(
        "serve",
        help="Start FastAPI inference server",
        description="Launch the real-time prediction API.",
    )
    serve.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    serve.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    serve.add_argument("--reload", action="store_true", help="Enable auto-reload (dev mode)")

    batch = subparsers.add_parser(
        "batch-predict",
        help="Run batch inference",
        description="Generate predictions for all bars and save to disk.",
    )
    batch.add_argument("--symbol", default="XAUUSD", help="Symbol (default: XAUUSD)")
    batch.add_argument("--tf", default="1H", help="Timeframe (default: 1H)")
    batch.add_argument("--label", default="label_10", help="Label column (default: label_10)")

    drift = subparsers.add_parser(
        "drift",
        help="Detect feature drift",
        description="Compare current features against training reference using KS/PSI tests.",
    )
    drift.add_argument("--symbol", default="XAUUSD", help="Symbol (default: XAUUSD)")
    drift.add_argument("--tf", default="1H", help="Timeframe (default: 1H)")
    drift.add_argument("--label", default="label_10", help="Label column (default: label_10)")
    drift.add_argument("--threshold-ks", type=float, default=0.1, help="Kolmogorov-Smirnov threshold (default: 0.1)")
    drift.add_argument("--threshold-psi", type=float, default=0.2, help="Population Stability Index threshold (default: 0.2)")

    models = subparsers.add_parser(
        "models",
        help="List registered model versions",
        description="Show all models in the registry with optional filtering.",
    )
    models.add_argument("--symbol", default=None, help="Filter by symbol")
    models.add_argument("--tf", default=None, help="Filter by timeframe")
    models.add_argument("--backend", default=None, help="Filter by backend")

    benchmark = subparsers.add_parser(
        "benchmark",
        help="Compare multiple backends on same data",
        description="Run multiple backends sequentially and compare metrics in a table.",
    )
    benchmark.add_argument("--symbol", default="XAUUSD", help="Symbol (default: XAUUSD)")
    benchmark.add_argument("--tf", default="1H", help="Timeframe (default: 1H)")
    benchmark.add_argument("--label", default="label_10", help="Label column (default: label_10)")
    benchmark.add_argument(
        "--backends",
        nargs="+",
        default=["mlf", "sgd", "stats"],
        metavar="BACKEND",
        help=f"Backends to run. Default: mlf sgd stats. Available: {', '.join(_ALL_BACKENDS)}",
    )
    benchmark.add_argument("--n-trials", type=int, default=5, help="Optuna trials per backend (default: 5)")
    benchmark.add_argument("--n-splits", type=int, default=3, help="CV folds (default: 3)")
    benchmark.add_argument("--train-start", default=None, help="Inclusive training start date in compact format YYYYMMDD, e.g. 20240101")
    benchmark.add_argument("--train-end", default=None, help="Inclusive training end date in compact format YYYYMMDD, e.g. 20241231")
    benchmark.add_argument("--force", action=argparse.BooleanOptionalAction, default=False, help="Force retrain all backends")

    return parser


def main() -> None:
    """Parse CLI args and dispatch to the appropriate workflow (download, pipeline, train, qa, evaluate, serve, batch-predict, drift, models)."""
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
            end_year=args.end_year,
            end_month=args.end_month,
            skip_current_month=args.skip_current_month,
        )
        return

    if args.command == "pipeline":
        for tf in args.tf:
            if not args.skip_resample:
                resample_symbol_tf(symbol=args.symbol, tf=tf, force=args.force)
            if not args.skip_features:
                run_feature_pipeline(
                    symbol=args.symbol,
                    tf=tf,
                    pivot_type=args.pivot,
                    pivot_anchor=args.anchor,
                    force=args.force,
                )
            if not args.skip_labels:
                run_label_pipeline(
                    symbol=args.symbol,
                    tf=tf,
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
            extra={
                "train_start": args.train_start,
                "train_end": args.train_end,
            },
        )
        run_training(cfg)
        return

    if args.command == "qa":
        result = run_quality_audit(
            symbol=args.symbol,
            asset_class=args.asset_class,
        )
        if not result.success:
            sys.exit(1)
        return

    if args.command == "evaluate":
        from mlfx.config.paths import DEFAULT_PATHS

        eval_kw = dict(
            symbol=args.symbol,
            tf=args.tf,
            label_col=args.label,
            initial_capital=args.capital,
            risk_pct=args.risk,
            commission=args.commission,
            tp_r=args.tp,
            sl_r=args.sl,
            slippage=args.slippage,
            train_start=args.eval_start,
            train_end=args.eval_end,
        )
        if args.use_labels:
            results = run_full_eval(**eval_kw)
            source = "Labels (baseline)"
        else:
            results = run_model_backtest(**eval_kw)
            if results is not None:
                source = "Model"
            else:
                results = run_full_eval(**eval_kw)
                source = "Labels (no model, fallback)"
        if results:
            console.print(f"[dim]Backtest: {source}[/]")
            if source == "Model":
                baseline = get_baseline_metrics(**eval_kw)
                if baseline is not None:
                    try:
                        model_r = float(
                            results["Net Profit (R)"].replace("R", "").replace(",", "").strip()
                        )
                        base_r = baseline["total_r"]
                        diff = model_r - base_r
                        if diff > 0:
                            diff_str = f"model tốt hơn +{diff:.1f}R"
                        elif diff < 0:
                            diff_str = f"labels tốt hơn {-diff:.1f}R"
                        else:
                            diff_str = "bằng nhau"
                        console.print(
                            f"[dim]So với labels: model {model_r:+.1f}R vs labels {base_r:+.1f}R → {diff_str}[/]"
                        )
                    except (ValueError, KeyError):
                        pass
            table = Table(title="Kết quả Backtest", show_header=True, header_style="bold cyan")
            table.add_column("Chỉ số", style="dim")
            table.add_column("Giá trị", justify="right")
            for k, v in results.items():
                table.add_row(k, v)
            console.print(table)
            risk_dir = f"R{int(args.tp * 10)}"
            report_mode = "labels" if source != "Model" else "model"
            reports_dir = (
                DEFAULT_PATHS.reports_dir(args.symbol, args.tf)
                / args.label
                / report_mode
                / risk_dir
            )
            console.print(f"\n[dim]Biểu đồ: {reports_dir}/[/]")
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

        keys = []
        for e in entries:
            for k in e.keys():
                if k not in keys:
                    keys.append(k)

        std_columns = ["symbol", "tf", "backend", "run_id", "accuracy"]
        ordered_keys = [k for k in std_columns if k in keys] + [k for k in keys if k not in std_columns]

        for k in ordered_keys:
            table.add_column(str(k))

        for e in entries:
            row = [str(e.get(k, "")) for k in ordered_keys]
            table.add_row(*row)

        console.print(table)
        return

    if args.command == "benchmark":
        _run_benchmark(args)
        return


def _run_benchmark(args: argparse.Namespace) -> None:
    """Run multiple backends on the same dataset and print a comparison table."""
    from mlfx.config.paths import DEFAULT_PATHS  # noqa: PLC0415

    backends: list[str] = args.backends
    invalid = [b for b in backends if b not in BACKEND_REGISTRY]
    if invalid:
        console.print(f"[red]Unknown backends: {invalid}. Available: {_ALL_BACKENDS}[/red]")
        return

    console.rule(f"[bold cyan]MLFX Benchmark — {args.symbol} {args.tf} {args.label}[/]")
    console.print(f"Backends: {', '.join(backends)}  |  n_trials={args.n_trials}  n_splits={args.n_splits}\n")

    results: list[dict] = []

    for backend in backends:
        console.print(f"[yellow]Running:[/] {backend} ...", end="  ")
        t0 = time.perf_counter()
        try:
            cfg = TrainingConfig(
                symbol=args.symbol,
                tf=args.tf,
                label_col=args.label,
                backend=backend,
                n_trials=args.n_trials,
                n_splits=args.n_splits,
                force=args.force,
                extra={
                    "train_start": args.train_start,
                    "train_end": args.train_end,
                },
            )
            metrics = run_training(cfg, enable_tracking=False, enable_registry=False)
            elapsed = time.perf_counter() - t0
            row = {
                "backend": backend,
                "cv_f1_macro": f"{metrics.get('best_cv_f1_macro', metrics.get('cv_f1_macro', 0.0)):.4f}",
                "train_f1": f"{metrics.get('f1_macro_train', 0.0):.4f}",
                "accuracy": f"{metrics.get('accuracy', 0.0):.4f}",
                "elapsed_s": f"{elapsed:.1f}",
                "status": "OK",
            }
            console.print(f"[green]OK[/] ({elapsed:.1f}s)")
        except Exception as exc:  # noqa: BLE001
            elapsed = time.perf_counter() - t0
            row = {
                "backend": backend,
                "cv_f1_macro": "-",
                "train_f1": "-",
                "accuracy": "-",
                "elapsed_s": f"{elapsed:.1f}",
                "status": f"ERROR: {exc}",
            }
            console.print(f"[red]ERROR[/] — {exc}")
        results.append(row)

    # Print comparison table
    console.print()
    table = Table(
        title=f"Benchmark Results — {args.symbol} {args.tf} {args.label}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Backend", style="bold")
    table.add_column("CV F1 (macro)", justify="right")
    table.add_column("Train F1", justify="right")
    table.add_column("Accuracy", justify="right")
    table.add_column("Time (s)", justify="right")
    table.add_column("Status")

    for row in results:
        status_style = "green" if row["status"] == "OK" else "red"
        table.add_row(
            row["backend"],
            row["cv_f1_macro"],
            row["train_f1"],
            row["accuracy"],
            row["elapsed_s"],
            f"[{status_style}]{row['status']}[/]",
        )
    console.print(table)

    # Save JSON report
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = DEFAULT_PATHS.reports_dir(args.symbol, args.tf) / args.label / "benchmark"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"benchmark_{ts}.json"
    payload = {
        "symbol": args.symbol,
        "tf": args.tf,
        "label": args.label,
        "n_trials": args.n_trials,
        "n_splits": args.n_splits,
        "train_start": args.train_start,
        "train_end": args.train_end,
        "timestamp": ts,
        "results": results,
    }
    report_path.write_text(json.dumps(payload, indent=2))
    console.print(f"\n[dim]Report saved → {report_path}[/]")
