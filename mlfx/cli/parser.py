"""Argument parser definitions for MLFX CLI."""

from __future__ import annotations

import argparse

from mlfx.training.registry import BACKEND_REGISTRY

_ALL_BACKENDS = sorted(BACKEND_REGISTRY)


def build_parser() -> argparse.ArgumentParser:
    """Build the consolidated argument parser for MLFX workflows."""
    parser = argparse.ArgumentParser(
        description="MLFX — Machine Learning for Forex. Terminal-first workflow.",
        epilog="Examples:\n"
        "  mlfx download --symbol XAUUSD --start-year 2020\n"
        "  mlfx pipeline --tf 1H\n"
        "  mlfx train --backend lstm --n-trials 20\n"
        "  mlfx train --profile research\n"
        "  mlfx benchmark --backends mlf lstm stats --n-trials 10\n"
        "  mlfx benchmark --profile benchmark_fast\n"
        "  mlfx evaluate --tp 2.0 --sl 1.0\n"
        "  mlfx evaluate --profile research\n"
        "  mlfx profiles\n"
        "  mlfx run-profile --profile research\n"
        "  mlfx run-profile --profile research --skip-benchmark\n"
        "  mlfx run-all --profile research\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--lang",
        choices=["en", "vi"],
        default="en",
        help="Display language for output (default: en)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    _add_download_parser(subparsers)
    _add_pipeline_parser(subparsers)
    _add_qa_parser(subparsers)
    _add_train_parser(subparsers)
    _add_evaluate_parser(subparsers)
    _add_serve_parser(subparsers)
    _add_batch_parser(subparsers)
    _add_drift_parser(subparsers)
    _add_drift_retrain_parser(subparsers)
    _add_models_parser(subparsers)
    _add_profiles_parser(subparsers)
    _add_run_profile_parser(subparsers)
    _add_run_all_parser(subparsers)
    _add_benchmark_parser(subparsers)
    _add_mlflow_parser(subparsers)

    return parser


def _add_download_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add download subcommand parser."""
    download = subparsers.add_parser(
        "download",
        help="Download raw tick data from Dukascopy",
        description="Download historical tick data for a symbol.",
    )
    download.add_argument("--symbol", default=None, help="Symbol to download (default: config.toml)")
    download.add_argument(
        "--asset-class",
        choices=["fx", "crypto"],
        default=None,
        help="Asset class (default: config.toml)",
    )
    download.add_argument("--start-year", type=int, default=None, help="Start year (default: config.toml)")
    download.add_argument("--start-month", type=int, default=None, help="Start month 1-12 (default: config.toml)")
    download.add_argument("--end-year", type=int, default=None, help="End year (default: current year)")
    download.add_argument("--end-month", type=int, default=None, help="End month (default: current month)")
    download.add_argument("--concurrency", type=int, default=None, help="Parallel downloads (default: config.toml)")
    download.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Force re-verify existing months (default: config.toml)",
    )
    download.add_argument(
        "--skip-current-month",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Skip checking/repairing current month (default: config.toml)",
    )


def _add_pipeline_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add pipeline subcommand parser."""
    pipeline = subparsers.add_parser(
        "pipeline",
        help="Run ETL pipeline: resample → features → labels",
        description="Execute the full data pipeline for one or more timeframes.",
    )
    pipeline.add_argument("--symbol", default=None, help="Symbol (default: config.toml)")
    pipeline.add_argument(
        "--tf",
        nargs="+",
        default=None,
        metavar="TF",
        help="Timeframe(s) to process: 1m, 5m, 15m, 30m, 1H, 2H, 4H, 1D (default: config.toml)",
    )
    pipeline.add_argument(
        "--pivot",
        default=None,
        help="Pivot type: traditional, fibonacci, woodie, classic, demark, camarilla (default: config.toml)",
    )
    pipeline.add_argument(
        "--anchor",
        default=None,
        help="Pivot anchor: daily, weekly, monthly (default: config.toml)",
    )
    pipeline.add_argument(
        "--atr-period",
        type=int,
        default=None,
        help="ATR period for label generation (default: config.toml)",
    )
    pipeline.add_argument(
        "--atr-mult",
        type=float,
        default=None,
        help="ATR multiplier for label thresholds (default: config.toml)",
    )
    pipeline.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Overwrite existing files (default: config.toml)",
    )
    pipeline.add_argument(
        "--skip-resample",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Skip tick → OHLCV resampling (default: config.toml)",
    )
    pipeline.add_argument(
        "--skip-features",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Skip feature engineering (default: config.toml)",
    )
    pipeline.add_argument(
        "--skip-labels",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Skip label generation (default: config.toml)",
    )


def _add_qa_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add QA subcommand parser."""
    qa = subparsers.add_parser(
        "qa",
        help="Audit raw downloaded tick data",
        description="Run quality checks on downloaded raw tick data.",
    )
    qa.add_argument("--symbol", default=None, help="Symbol to audit (default: config.toml)")
    qa.add_argument(
        "--asset-class",
        choices=["fx", "crypto"],
        default=None,
        help="Asset class (default: config.toml)",
    )


def _add_train_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add train subcommand parser."""
    train = subparsers.add_parser(
        "train",
        help="Train a single model backend",
        description="Train one backend with Optuna HPO and CV.",
    )
    train.add_argument("--symbol", default=None, help="Symbol (default: config.toml)")
    train.add_argument("--tf", default=None, help="Timeframe (default: config.toml)")
    train.add_argument(
        "--label",
        default=None,
        help="Label column: label_5, label_10, label_20 (default: config.toml)",
    )
    train.add_argument(
        "--backend",
        default=None,
        choices=_ALL_BACKENDS,
        metavar="BACKEND",
        help=f"Model backend. Options: {', '.join(_ALL_BACKENDS)} (default: config.toml)",
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
    train.add_argument(
        "--mlflow",
        action="store_true",
        default=False,
        help="Enable MLflow experiment tracking and model registry",
    )


def _add_evaluate_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add evaluate subcommand parser."""
    evaluate = subparsers.add_parser(
        "evaluate",
        help="Run walk-forward backtest",
        description="Backtest a trained model or baseline labels.",
    )
    evaluate.add_argument("--symbol", default=None, help="Symbol")
    evaluate.add_argument("--tf", default=None, help="Timeframe")
    evaluate.add_argument("--label", default=None, help="Label column")
    evaluate.add_argument("--capital", type=float, default=None, help="Initial capital in USD")
    evaluate.add_argument("--risk", type=float, default=None, help="Risk per trade %%")
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


def _add_serve_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add serve subcommand parser."""
    serve = subparsers.add_parser(
        "serve",
        help="Start FastAPI inference server",
        description="Launch the real-time prediction API.",
    )
    serve.add_argument("--host", default=None, help="Bind address (default: config.toml)")
    serve.add_argument("--port", type=int, default=None, help="Port (default: config.toml)")
    serve.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable auto-reload (default: config.toml)",
    )


def _add_batch_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add batch-predict subcommand parser."""
    batch = subparsers.add_parser(
        "batch-predict",
        help="Run batch inference",
        description="Generate predictions for all bars and save to disk.",
    )
    batch.add_argument("--symbol", default=None, help="Symbol (default: config.toml)")
    batch.add_argument("--tf", default=None, help="Timeframe (default: config.toml)")
    batch.add_argument("--label", default=None, help="Label column (default: config.toml)")


def _add_drift_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add drift subcommand parser."""
    drift = subparsers.add_parser(
        "drift",
        help="Detect feature drift",
        description="Compare current features against training reference using KS/PSI tests.",
    )
    drift.add_argument("--symbol", default=None, help="Symbol (default: config.toml)")
    drift.add_argument("--tf", default=None, help="Timeframe (default: config.toml)")
    drift.add_argument("--label", default=None, help="Label column (default: config.toml)")
    drift.add_argument(
        "--threshold-ks",
        type=float,
        default=None,
        help="Kolmogorov-Smirnov threshold (default: config.toml)",
    )
    drift.add_argument(
        "--threshold-psi",
        type=float,
        default=None,
        help="Population Stability Index threshold (default: config.toml)",
    )
    drift.add_argument(
        "--min-samples",
        type=int,
        default=None,
        help="Minimum live samples per feature for drift tests (default: config.toml)",
    )


def _add_drift_retrain_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add drift-retrain subcommand parser."""
    drift_retrain = subparsers.add_parser(
        "drift-retrain",
        help="Run drift detection and retrain if drift is found",
        description="Detect drift first; if drifted features exist, retrain the selected backend.",
    )
    drift_retrain.add_argument("--symbol", default=None, help="Symbol")
    drift_retrain.add_argument("--tf", default=None, help="Timeframe")
    drift_retrain.add_argument("--label", default=None, help="Label column")
    drift_retrain.add_argument(
        "--backend",
        default=None,
        choices=_ALL_BACKENDS,
        metavar="BACKEND",
        help=f"Model backend. Options: {', '.join(_ALL_BACKENDS)}",
    )
    drift_retrain.add_argument("--n-trials", type=int, default=None, help="Optuna trials for HPO")
    drift_retrain.add_argument("--n-splits", type=int, default=None, help="TimeSeriesSplit folds")
    drift_retrain.add_argument(
        "--train-start",
        default=None,
        help="Inclusive training start date in compact format YYYYMMDD, e.g. 20240101",
    )
    drift_retrain.add_argument(
        "--train-end",
        default=None,
        help="Inclusive training end date in compact format YYYYMMDD, e.g. 20241231",
    )
    drift_retrain.add_argument(
        "--profile",
        default=None,
        help="Load train defaults from a named profile in config.toml",
    )
    drift_retrain.add_argument(
        "--force",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Force retrain if drift is detected",
    )
    drift_retrain.add_argument(
        "--threshold-ks",
        type=float,
        default=None,
        help="Kolmogorov-Smirnov threshold (default: config.toml)",
    )
    drift_retrain.add_argument(
        "--threshold-psi",
        type=float,
        default=None,
        help="Population Stability Index threshold (default: config.toml)",
    )
    drift_retrain.add_argument(
        "--min-samples",
        type=int,
        default=None,
        help="Minimum live samples per feature for drift tests (default: config.toml)",
    )


def _add_models_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add models subcommand parser."""
    models = subparsers.add_parser(
        "models",
        help="List registered model versions",
        description="Show all models in the registry with optional filtering.",
    )
    models.add_argument("--symbol", default=None, help="Filter by symbol")
    models.add_argument("--tf", default=None, help="Filter by timeframe")
    models.add_argument("--backend", default=None, help="Filter by backend")


def _add_profiles_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add profiles subcommand parser."""
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


def _add_run_profile_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add run-profile subcommand parser."""
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
    run_profile.add_argument(
        "--force",
        action="store_true",
        help="Force retraining even if a model already exists",
    )


def _add_run_all_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add run-all subcommand parser."""
    run_all = subparsers.add_parser(
        "run-all",
        help="Run the full end-to-end workflow",
        description=(
            "Run workflow sequence: download -> qa -> pipeline -> train -> evaluate -> "
            "benchmark -> serve placeholder -> batch-predict -> drift + retrain"
        ),
    )
    run_all.add_argument(
        "--profile",
        default=None,
        help="Use one workflow profile for train/evaluate/benchmark defaults",
    )
    run_all.add_argument("--symbol", default=None, help="Symbol override (e.g., XAUUSD)")
    run_all.add_argument("--tf", default=None, help="Timeframe override (e.g., 1H, 4H)")
    run_all.add_argument("--label", default=None, help="Label column override")
    run_all.add_argument("--skip-download", action="store_true", help="Skip download stage")
    run_all.add_argument("--skip-qa", action="store_true", help="Skip QA stage")
    run_all.add_argument("--skip-pipeline", action="store_true", help="Skip pipeline stage")
    run_all.add_argument("--skip-train", action="store_true", help="Skip train stage")
    run_all.add_argument("--skip-evaluate", action="store_true", help="Skip evaluate stage")
    run_all.add_argument("--skip-benchmark", action="store_true", help="Skip benchmark stage")
    run_all.add_argument("--skip-serve", action="store_true", help="Skip serve placeholder stage")
    run_all.add_argument("--skip-batch", action="store_true", help="Skip batch prediction stage")
    run_all.add_argument(
        "--skip-drift-retrain",
        action="store_true",
        help="Skip drift detection and retraining stages",
    )
    run_all.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue remaining stages after an error",
    )
    run_all.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary of run-all stage outputs",
    )


def _add_benchmark_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add benchmark subcommand parser."""
    benchmark = subparsers.add_parser(
        "benchmark",
        help="Compare multiple backends on same data",
        description="Run multiple backends sequentially and compare metrics in a table.",
    )
    benchmark.add_argument("--symbol", default=None, help="Symbol (default: config.toml)")
    benchmark.add_argument("--tf", default=None, help="Timeframe (default: config.toml)")
    benchmark.add_argument("--label", default=None, help="Label column (default: config.toml)")
    benchmark.add_argument(
        "--backends",
        nargs="+",
        default=None,
        metavar="BACKEND",
        help=f"Backends to run. Default: config.toml. Available: {', '.join(_ALL_BACKENDS)}",
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
    benchmark.add_argument(
        "--mlflow",
        action="store_true",
        default=False,
        help="Enable MLflow experiment tracking for benchmark runs",
    )


def _add_mlflow_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add mlflow subcommand parser."""
    mlflow = subparsers.add_parser(
        "mlflow",
        help="MLflow integration commands",
        description="Manage MLflow tracking server and migrate artifacts.",
    )
    mlflow_subparsers = mlflow.add_subparsers(
        dest="mlflow_command",
        required=True,
        help="MLflow subcommands",
    )

    mlflow_ui = mlflow_subparsers.add_parser(
        "ui",
        help="Launch MLflow tracking UI",
        description="Start the MLflow tracking server with web UI.",
    )
    mlflow_ui.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the UI server (default: 127.0.0.1)",
    )
    mlflow_ui.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for the UI server (default: 5000)",
    )
    mlflow_ui.add_argument(
        "--backend-store-uri",
        default=None,
        help="URI for MLflow backend store (default: from config)",
    )
    mlflow_ui.add_argument(
        "--default-artifact-root",
        default=None,
        help="Default artifact root path (default: from config)",
    )

    mlflow_migrate = mlflow_subparsers.add_parser(
        "migrate",
        help="Migrate existing artifacts to MLflow",
        description="Migrate existing model artifacts and run metadata to MLflow.",
    )
    mlflow_migrate.add_argument(
        "--symbol",
        default=None,
        help="Migrate only models for this symbol (default: all)",
    )
    mlflow_migrate.add_argument(
        "--tf",
        default=None,
        help="Migrate only models for this timeframe (default: all)",
    )
    mlflow_migrate.add_argument(
        "--backend",
        default=None,
        choices=_ALL_BACKENDS,
        metavar="BACKEND",
        help=f"Migrate only models for this backend. Options: {', '.join(_ALL_BACKENDS)} (default: all)",
    )
    mlflow_migrate.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview migration without making changes",
    )
    mlflow_migrate.add_argument(
        "--register-models",
        action="store_true",
        default=True,
        help="Register migrated models in MLflow Model Registry (default: True)",
    )
