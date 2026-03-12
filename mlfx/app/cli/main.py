"""Consolidated CLI entrypoint for core MLFX workflows."""

from __future__ import annotations

import argparse
import logging
import sys

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

from .render import (
    console,
    print_backtest_results,
    print_profiles_summary,
    print_resolved_evaluate_summary,
    print_resolved_train_summary,
)
from .resolve import (
    resolve_evaluate_config,
    resolve_train_config,
)
from .workflows import run_benchmark, run_profile_command

_resolve_profile_section = None

_ALL_BACKENDS = sorted(BACKEND_REGISTRY)


def build_parser() -> argparse.ArgumentParser:
    """Build the consolidated argument parser for MLFX workflows."""
    parser = argparse.ArgumentParser(
        description="MLFX — Machine Learning for Forex. Terminal-first workflow.",
        epilog="Examples:\n"
        "  mlfx download --symbol XAUUSD --start-year 2020\n"
        "  mlfx pipeline --tf 1H\n"
        "  mlfx train --backend bilstm --n-trials 20\n"
        "  mlfx train --profile research\n"
        "  mlfx benchmark --backends mlf bilstm lstm --n-trials 10\n"
        "  mlfx benchmark --profile benchmark_fast\n"
        "  mlfx evaluate --tp 2.0 --sl 1.0\n"
        "  mlfx evaluate --profile research\n"
        "  mlfx profiles\n"
        "  mlfx run-profile --profile research\n"
        "  mlfx run-profile --profile research --skip-benchmark\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    download = subparsers.add_parser(
        "download",
        help="Download raw tick data from Dukascopy",
        description="Download historical tick data for a symbol.",
    )
    download.add_argument("--symbol", default="XAUUSD", help="Symbol to download (default: XAUUSD)")
    download.add_argument(
        "--asset-class",
        choices=["fx", "crypto"],
        default="fx",
        help="Asset class (default: fx)",
    )
    download.add_argument("--start-year", type=int, default=2015, help="Start year (default: 2015)")
    download.add_argument("--start-month", type=int, default=1, help="Start month 1-12 (default: 1)")
    download.add_argument("--end-year", type=int, default=None, help="End year (default: current year)")
    download.add_argument("--end-month", type=int, default=None, help="End month (default: current month)")
    download.add_argument("--concurrency", type=int, default=20, help="Parallel downloads (default: 20)")
    download.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Force re-verify existing months",
    )
    download.add_argument(
        "--skip-current-month",
        action="store_true",
        help="Skip checking/repairing current month",
    )

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
    pipeline.add_argument(
        "--pivot",
        default="traditional",
        help="Pivot type: traditional, fibonacci, woodie, classic, demark, camarilla (default: traditional)",
    )
    pipeline.add_argument(
        "--anchor",
        default="daily",
        help="Pivot anchor: daily, weekly, monthly (default: daily)",
    )
    pipeline.add_argument(
        "--atr-period",
        type=int,
        default=14,
        help="ATR period for label generation (default: 14)",
    )
    pipeline.add_argument(
        "--atr-mult",
        type=float,
        default=0.5,
        help="ATR multiplier for label thresholds (default: 0.5)",
    )
    pipeline.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Overwrite existing files",
    )
    pipeline.add_argument(
        "--skip-resample",
        action="store_true",
        help="Skip tick → OHLCV resampling",
    )
    pipeline.add_argument("--skip-features", action="store_true", help="Skip feature engineering")
    pipeline.add_argument("--skip-labels", action="store_true", help="Skip label generation")

    qa = subparsers.add_parser(
        "qa",
        help="Audit raw downloaded tick data",
        description="Run quality checks on downloaded raw tick data.",
    )
    qa.add_argument("--symbol", default="XAUUSD", help="Symbol to audit (default: XAUUSD)")
    qa.add_argument(
        "--asset-class",
        choices=["fx", "crypto"],
        default="fx",
        help="Asset class (default: fx)",
    )

    train = subparsers.add_parser(
        "train",
        help="Train a single model backend",
        description="Train one backend with Optuna HPO and CV.",
    )
    train.add_argument("--symbol", default="XAUUSD", help="Symbol (default: XAUUSD)")
    train.add_argument("--tf", default="1H", help="Timeframe (default: 1H)")
    train.add_argument(
        "--label",
        default="label_10",
        help="Label column: label_5, label_10, label_20 (default: label_10)",
    )
    train.add_argument(
        "--backend",
        default="mlf",
        choices=_ALL_BACKENDS,
        metavar="BACKEND",
        help=f"Model backend. Options: {', '.join(_ALL_BACKENDS)} (default: mlf)",
    )
    train.add_argument("--n-trials", type=int, default=None, help="Optuna trials for HPO")
    train.add_argument("--n-splits", type=int, default=None, help="TimeSeriesSplit folds")
    train.add_argument(
        "--train-start",
        default=None,
        help="Inclusive training start date in compact format YYYYMMDD, e.g. 20240101",
    )
    train.add_argument(
        "--train-end",
        default=None,
        help="Inclusive training end date in compact format YYYYMMDD, e.g. 20241231",
    )
    train.add_argument(
        "--profile",
        default=None,
        help="Load train defaults from a named profile in config.toml",
    )
    train.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Force retrain (overwrite saved model)",
    )

    evaluate = subparsers.add_parser(
        "evaluate",
        help="Run walk-forward backtest",
        description="Backtest a trained model or baseline labels.",
    )
    evaluate.add_argument("--symbol", default=None, help="Symbol")
    evaluate.add_argument("--tf", default=None, help="Timeframe")
    evaluate.add_argument("--label", default=None, help="Label column")
    evaluate.add_argument("--capital", type=float, default=None, help="Initial capital in USD")
    evaluate.add_argument("--risk", type=float, default=None, help="Risk per trade %")
    evaluate.add_argument("--commission", type=float, default=None, help="Commission in pips")
    evaluate.add_argument("--tp", type=float, default=None, help="Take-profit in R multiples")
    evaluate.add_argument("--sl", type=float, default=None, help="Stop-loss in R multiples")
    evaluate.add_argument("--slippage", type=float, default=None, help="Slippage in pips")
    evaluate.add_argument(
        "--eval-start",
        default=None,
        help="Inclusive evaluation start date in compact format YYYYMMDD, e.g. 20240101",
    )
    evaluate.add_argument(
        "--eval-end",
        default=None,
        help="Inclusive evaluation end date in compact format YYYYMMDD, e.g. 20241231",
    )
    evaluate.add_argument(
        "--profile",
        default=None,
        help="Load evaluation defaults from a named profile in config.toml",
    )
    evaluate.add_argument(
        "--use-labels",
        action=argparse.BooleanOptionalAction,
        default=None,
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
    drift.add_argument(
        "--threshold-ks",
        type=float,
        default=0.1,
        help="Kolmogorov-Smirnov threshold (default: 0.1)",
    )
    drift.add_argument(
        "--threshold-psi",
        type=float,
        default=0.2,
        help="Population Stability Index threshold (default: 0.2)",
    )

    models = subparsers.add_parser(
        "models",
        help="List registered model versions",
        description="Show all models in the registry with optional filtering.",
    )
    models.add_argument("--symbol", default=None, help="Filter by symbol")
    models.add_argument("--tf", default=None, help="Filter by timeframe")
    models.add_argument("--backend", default=None, help="Filter by backend")

    profiles = subparsers.add_parser(
        "profiles",
        help="List available workflow profiles",
        description="Show workflow profiles from config.toml and which commands they support.",
    )
    profiles.add_argument(
        "--profile",
        default=None,
        help="Show only one profile in detailed form",
    )

    run_profile = subparsers.add_parser(
        "run-profile",
        help="Run train then evaluate from one workflow profile",
        description="Resolve one profile and orchestrate train followed by evaluate using that profile's sections.",
    )
    run_profile.add_argument(
        "--profile",
        required=True,
        help="Workflow profile name to execute",
    )
    run_profile.add_argument(
        "--skip-train",
        action="store_true",
        help="Skip the training step and run only evaluation from the profile",
    )
    run_profile.add_argument(
        "--skip-evaluate",
        action="store_true",
        help="Skip the evaluation step and run only training from the profile",
    )
    run_profile.add_argument(
        "--skip-benchmark",
        action="store_true",
        help="Skip the benchmark step even if the profile defines one",
    )
    run_profile.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary of the run-profile orchestration result",
    )

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
    benchmark.add_argument("--n-trials", type=int, default=None, help="Optuna trials per backend")
    benchmark.add_argument("--n-splits", type=int, default=None, help="CV folds")
    benchmark.add_argument(
        "--train-start",
        default=None,
        help="Inclusive training start date in compact format YYYYMMDD, e.g. 20240101",
    )
    benchmark.add_argument(
        "--train-end",
        default=None,
        help="Inclusive training end date in compact format YYYYMMDD, e.g. 20241231",
    )
    benchmark.add_argument(
        "--profile",
        default=None,
        help="Load benchmark defaults from a named profile in config.toml",
    )
    benchmark.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Force retrain all backends",
    )

    return parser


def _print_profiles_summary(profile_name: str | None) -> None:
    """Load workflow profiles from config and render them."""
    import tomllib

    from mlfx.config.paths import DEFAULT_PATHS

    config_path = DEFAULT_PATHS.config_file
    if not config_path.exists():
        console.print("[yellow]config.toml not found — no workflow profiles available.[/yellow]")
        return

    with config_path.open("rb") as handle:
        data = tomllib.load(handle)

    profiles = data.get("profiles", {})
    print_profiles_summary(profile_name, profiles)


def _run_train_command(args: argparse.Namespace) -> None:
    """Resolve and execute the train command."""
    train_cfg = _resolve_train_command_config(args)

    print_resolved_train_summary(
        profile=args.profile,
        symbol=train_cfg["symbol"],
        tf=train_cfg["tf"],
        label=train_cfg["label"],
        backend=train_cfg["backend"],
        n_trials=train_cfg["n_trials"],
        n_splits=train_cfg["n_splits"],
        train_start=train_cfg["train_start"],
        train_end=train_cfg["train_end"],
        force=train_cfg["force"],
    )

    cfg = TrainingConfig(
        symbol=train_cfg["symbol"],
        tf=train_cfg["tf"],
        label_col=train_cfg["label"],
        backend=train_cfg["backend"],
        n_trials=train_cfg["n_trials"],
        n_splits=train_cfg["n_splits"],
        force=train_cfg["force"],
        extra={
            "train_start": train_cfg["train_start"],
            "train_end": train_cfg["train_end"],
            "profile": args.profile,
        },
    )
    run_training(cfg)


def _run_evaluate_command(args: argparse.Namespace) -> None:
    """Resolve and execute the evaluate command."""
    from mlfx.config.paths import DEFAULT_PATHS

    eval_cfg = _resolve_evaluate_command_config(args)

    print_resolved_evaluate_summary(
        profile=args.profile,
        symbol=eval_cfg["symbol"],
        tf=eval_cfg["tf"],
        label=eval_cfg["label"],
        capital=eval_cfg["capital"],
        risk=eval_cfg["risk"],
        commission=eval_cfg["commission"],
        tp=eval_cfg["tp"],
        sl=eval_cfg["sl"],
        slippage=eval_cfg["slippage"],
        eval_start=eval_cfg["eval_start"],
        eval_end=eval_cfg["eval_end"],
        use_labels=eval_cfg["use_labels"],
    )

    eval_kw = dict(
        symbol=eval_cfg["symbol"],
        tf=eval_cfg["tf"],
        label_col=eval_cfg["label"],
        initial_capital=eval_cfg["capital"],
        risk_pct=eval_cfg["risk"],
        commission=eval_cfg["commission"],
        tp_r=eval_cfg["tp"],
        sl_r=eval_cfg["sl"],
        slippage=eval_cfg["slippage"],
        train_start=eval_cfg["eval_start"],
        train_end=eval_cfg["eval_end"],
    )

    if eval_cfg["use_labels"]:
        results = run_full_eval(**eval_kw)
        source = "Labels (baseline)"
    else:
        results = run_model_backtest(**eval_kw)
        if results is not None:
            source = "Model"
        else:
            results = run_full_eval(**eval_kw)
            source = "Labels (no model, fallback)"

    if not results:
        return

    baseline = get_baseline_metrics(**eval_kw) if source == "Model" else None
    print_backtest_results(results=results, source=source, baseline=baseline)

    risk_dir = f"R{int(eval_cfg['tp'] * 10)}"
    report_mode = "labels" if source != "Model" else "model"
    reports_dir = (
        DEFAULT_PATHS.reports_dir(eval_cfg["symbol"], eval_cfg["tf"])
        / eval_cfg["label"]
        / report_mode
        / risk_dir
    )
    console.print(f"\n[dim]Biểu đồ: {reports_dir}/[/]")


def main() -> None:
    """Parse CLI args and dispatch to the appropriate workflow."""
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
        _run_train_command(args)
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
        _run_evaluate_command(args)
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

        from rich.table import Table

        table = Table(title="Registered Model Versions", show_header=True, header_style="bold magenta")

        keys: list[str] = []
        for entry in entries:
            for key in entry.keys():
                if key not in keys:
                    keys.append(key)

        std_columns = ["symbol", "tf", "backend", "run_id", "accuracy"]
        ordered_keys = [key for key in std_columns if key in keys] + [
            key for key in keys if key not in std_columns
        ]

        for key in ordered_keys:
            table.add_column(str(key))

        for entry in entries:
            row = [str(entry.get(key, "")) for key in ordered_keys]
            table.add_row(*row)

        console.print(table)
        return

    if args.command == "profiles":
        _print_profiles_summary(args.profile)
        return

    if args.command == "run-profile":
        _run_profile_command(args)
        return

    if args.command == "benchmark":
        _run_benchmark(args)
        return


_resolve_train_command_config = resolve_train_config
_resolve_evaluate_command_config = resolve_evaluate_config
_print_resolved_train_summary = print_resolved_train_summary
_print_resolved_evaluate_summary = print_resolved_evaluate_summary
_run_profile_command = run_profile_command
_run_benchmark = run_benchmark
