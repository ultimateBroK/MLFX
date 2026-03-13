"""Consolidated CLI entrypoint for core MLFX workflows."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

from mlfx.training.backends.base import TrainingConfig
from mlfx.training.registry import BACKEND_REGISTRY
from mlfx.workflow import StageResult, WorkflowResult, persist_workflow_result
from mlfx.workflow.stages import (
    run_batch,
    run_download,
    run_drift,
    run_drift_then_retrain,
    run_evaluate,
    run_pipeline_stage,
    run_qa,
    run_train,
)

from .render import (
    console,
    print_backtest_results,
    print_profiles_summary,
    print_resolved_evaluate_summary,
    print_resolved_train_summary,
)
from .resolve import (
    resolve_batch_config,
    resolve_download_config,
    resolve_drift_config,
    resolve_evaluate_config,
    resolve_pipeline_config,
    resolve_qa_config,
    resolve_serve_config,
    resolve_train_config,
)
from .workflows import run_benchmark, run_benchmark_stage, run_profile_command

_resolve_profile_section = None

_ALL_BACKENDS = sorted(BACKEND_REGISTRY)


def _derive_workflow_status(stages: list[StageResult]) -> str:
    if any(stage.status == "error" for stage in stages):
        return "error"
    if stages and all(stage.status == "skipped" for stage in stages):
        return "skipped"
    return "ok"


def _persist_cli_workflow(
    workflow: str,
    stages: list[StageResult],
    *,
    params: dict[str, Any] | None = None,
) -> None:
    result = WorkflowResult(
        workflow=workflow,
        stages=stages,
        status=_derive_workflow_status(stages),  # type: ignore[arg-type]
        params=params or {},
    )
    summary_path = persist_workflow_result(result)
    console.print(f"[dim]Workflow summary: {summary_path}[/]")


def _exit_on_stage_error(stage: StageResult) -> None:
    if stage.status == "error":
        if stage.error:
            logging.getLogger(__name__).error("%s failed: %s", stage.stage, stage.error)
        sys.exit(1)


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
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

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
    serve.add_argument("--host", default=None, help="Bind address (default: config.toml)")
    serve.add_argument("--port", type=int, default=None, help="Port (default: config.toml)")
    serve.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable auto-reload (default: config.toml)",
    )

    batch = subparsers.add_parser(
        "batch-predict",
        help="Run batch inference",
        description="Generate predictions for all bars and save to disk.",
    )
    batch.add_argument("--symbol", default=None, help="Symbol (default: config.toml)")
    batch.add_argument("--tf", default=None, help="Timeframe (default: config.toml)")
    batch.add_argument("--label", default=None, help="Label column (default: config.toml)")

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

    return parser


def _print_profiles_summary(profile_name: str | None) -> None:
    """Load workflow profiles from config and render them."""
    from mlfx.config.settings import load_config

    try:
        config = load_config()
    except FileNotFoundError:
        console.print("[yellow]config.toml not found — no workflow profiles available.[/yellow]")
        return

    profiles = {
        name: profile.model_dump(exclude_none=True)
        for name, profile in config.profiles.items()
    }
    print_profiles_summary(profile_name, profiles)


def _run_train_command(args: argparse.Namespace) -> StageResult:
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
        label=train_cfg["label"],
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
    return run_train(cfg)


def _run_evaluate_command(args: argparse.Namespace) -> StageResult:
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

    stage = run_evaluate(
        symbol=eval_cfg["symbol"],
        tf=eval_cfg["tf"],
        label=eval_cfg["label"],
        initial_capital=eval_cfg["capital"],
        risk_pct=eval_cfg["risk"],
        commission=eval_cfg["commission"],
        tp_r=eval_cfg["tp"],
        sl_r=eval_cfg["sl"],
        slippage=eval_cfg["slippage"],
        eval_start=eval_cfg["eval_start"],
        eval_end=eval_cfg["eval_end"],
        use_labels=eval_cfg["use_labels"],
    )

    if stage.status == "error":
        return stage

    results = stage.metrics.get("results") if isinstance(stage.metrics, dict) else None
    source_raw = stage.metrics.get("source") if isinstance(stage.metrics, dict) else None
    baseline = stage.metrics.get("baseline") if isinstance(stage.metrics, dict) else None
    source = {
        "labels": "Labels (baseline)",
        "labels_fallback": "Labels (no model, fallback)",
        "model": "Model",
    }.get(str(source_raw), str(source_raw) if source_raw is not None else "-")

    if not results:
        return stage

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
    return stage


def _make_skipped_stage(
    stage: str,
    *,
    reason: str,
    params: dict[str, Any] | None = None,
) -> StageResult:
    """Create a canonical skipped stage result payload."""
    return StageResult(
        stage=stage,
        status="skipped",
        metrics={"reason": reason},
        params=params or {},
    )


def _run_all_command(args: argparse.Namespace) -> list[StageResult]:
    """Execute the full hobby-workflow sequence with optional skips."""
    skip_flags = [
        args.skip_download,
        args.skip_qa,
        args.skip_pipeline,
        args.skip_train,
        args.skip_evaluate,
        args.skip_benchmark,
        args.skip_serve,
        args.skip_batch,
        args.skip_drift_retrain,
    ]
    if all(skip_flags):
        raise ValueError("run-all cannot skip all stages at the same time")

    stages: list[StageResult] = []

    def _append(stage: StageResult) -> bool:
        stages.append(stage)
        return (stage.status == "error") and (not args.continue_on_error)

    train_args = argparse.Namespace(
        profile=args.profile,
        symbol=None,
        tf=None,
        label=None,
        backend=None,
        n_trials=None,
        n_splits=None,
        train_start=None,
        train_end=None,
        force=None,
    )
    eval_args = argparse.Namespace(
        profile=args.profile,
        symbol=None,
        tf=None,
        label=None,
        capital=None,
        risk=None,
        commission=None,
        tp=None,
        sl=None,
        slippage=None,
        eval_start=None,
        eval_end=None,
        use_labels=None,
    )
    benchmark_args = argparse.Namespace(
        profile=args.profile,
        symbol=None,
        tf=None,
        label=None,
        backends=None,
        n_trials=None,
        n_splits=None,
        train_start=None,
        train_end=None,
        force=None,
    )

    if args.skip_download:
        stages.append(_make_skipped_stage("download", reason="Skipped by --skip-download"))
    else:
        download_cfg = _resolve_download_command_config(
            argparse.Namespace(
                symbol=None,
                asset_class=None,
                start_year=None,
                start_month=None,
                end_year=None,
                end_month=None,
                concurrency=None,
                force=None,
                skip_current_month=None,
            )
        )
        if _append(run_download(**download_cfg)):
            return stages

    if args.skip_qa:
        stages.append(_make_skipped_stage("qa", reason="Skipped by --skip-qa"))
    else:
        qa_cfg = _resolve_qa_command_config(
            argparse.Namespace(symbol=None, asset_class=None)
        )
        if _append(run_qa(**qa_cfg)):
            return stages

    if args.skip_pipeline:
        stages.append(_make_skipped_stage("pipeline", reason="Skipped by --skip-pipeline"))
    else:
        pipeline_cfg = _resolve_pipeline_command_config(
            argparse.Namespace(
                symbol=None,
                tf=None,
                pivot=None,
                anchor=None,
                atr_period=None,
                atr_mult=None,
                force=None,
                skip_resample=None,
                skip_features=None,
                skip_labels=None,
            )
        )
        if _append(run_pipeline_stage(**pipeline_cfg)):
            return stages

    if args.skip_train:
        stages.append(_make_skipped_stage("train", reason="Skipped by --skip-train"))
    else:
        if _append(_run_train_command(train_args)):
            return stages

    if args.skip_evaluate:
        stages.append(_make_skipped_stage("evaluate", reason="Skipped by --skip-evaluate"))
    else:
        if _append(_run_evaluate_command(eval_args)):
            return stages

    if args.skip_benchmark:
        stages.append(_make_skipped_stage("benchmark", reason="Skipped by --skip-benchmark"))
    else:
        if _append(_run_benchmark_stage(benchmark_args)):
            return stages

    if args.skip_serve:
        stages.append(_make_skipped_stage("serve", reason="Skipped by --skip-serve"))
    else:
        serve_cfg = _resolve_serve_command_config(
            argparse.Namespace(host=None, port=None, reload=None)
        )
        stages.append(
            _make_skipped_stage(
                "serve",
                reason="Realtime API is long-running; start separately with `mlfx serve`.",
                params=serve_cfg,
            )
        )

    if args.skip_batch:
        stages.append(_make_skipped_stage("batch", reason="Skipped by --skip-batch"))
    else:
        batch_cfg = _resolve_batch_command_config(
            argparse.Namespace(symbol=None, tf=None, label=None)
        )
        if _append(run_batch(**batch_cfg)):
            return stages

    if args.skip_drift_retrain:
        stages.append(_make_skipped_stage("drift", reason="Skipped by --skip-drift-retrain"))
        stages.append(_make_skipped_stage("retrain", reason="Skipped by --skip-drift-retrain"))
    else:
        drift_cfg = _resolve_drift_command_config(
            argparse.Namespace(
                symbol=None,
                tf=None,
                label=None,
                threshold_ks=None,
                threshold_psi=None,
                min_samples=None,
            )
        )
        train_cfg = _resolve_train_command_config(train_args)
        training_cfg = TrainingConfig(
            symbol=train_cfg["symbol"],
            tf=train_cfg["tf"],
            label=train_cfg["label"],
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
        for drift_stage in run_drift_then_retrain(
            drift_params={
                "symbol": drift_cfg["symbol"],
                "tf": drift_cfg["tf"],
                "label": drift_cfg["label"],
                "threshold_ks": drift_cfg["threshold_ks"],
                "threshold_psi": drift_cfg["threshold_psi"],
                "min_samples": drift_cfg["min_samples"],
            },
            train_config=training_cfg,
        ):
            if _append(drift_stage):
                return stages

    if args.json:
        console.print_json(json.dumps({"stages": [stage.to_dict() for stage in stages]}))

    return stages


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
        download_cfg = _resolve_download_command_config(args)
        stage = run_download(**download_cfg)
        _persist_cli_workflow("download", [stage], params=vars(args))
        _exit_on_stage_error(stage)
        return

    if args.command == "pipeline":
        pipeline_cfg = _resolve_pipeline_command_config(args)
        stage = run_pipeline_stage(**pipeline_cfg)
        _persist_cli_workflow("pipeline", [stage], params=vars(args))
        _exit_on_stage_error(stage)
        return

    if args.command == "train":
        stage = _run_train_command(args)
        _persist_cli_workflow("train", [stage], params=vars(args))
        _exit_on_stage_error(stage)
        return

    if args.command == "qa":
        qa_cfg = _resolve_qa_command_config(args)
        stage = run_qa(**qa_cfg)
        _persist_cli_workflow("qa", [stage], params=vars(args))
        _exit_on_stage_error(stage)
        return

    if args.command == "evaluate":
        stage = _run_evaluate_command(args)
        _persist_cli_workflow("evaluate", [stage], params=vars(args))
        _exit_on_stage_error(stage)
        return

    if args.command == "serve":
        serve_cfg = _resolve_serve_command_config(args)
        try:
            import uvicorn  # type: ignore[import-not-found]  # noqa: PLC0415
        except ImportError:
            logging.getLogger(__name__).error(
                "uvicorn not installed. Run: pip install fastapi uvicorn"
            )
            return
        uvicorn.run(
            "mlfx.serving.api:app",
            host=serve_cfg["host"],
            port=serve_cfg["port"],
            reload=serve_cfg["reload"],
        )
        return

    if args.command == "batch-predict":
        batch_cfg = _resolve_batch_command_config(args)
        with console.status("[bold green]Running batch inference..."):
            stage = run_batch(**batch_cfg)
        if stage.metrics:
            console.print(stage.metrics)
        _persist_cli_workflow("batch-predict", [stage], params=vars(args))
        _exit_on_stage_error(stage)
        return

    if args.command == "drift":
        drift_cfg = _resolve_drift_command_config(args)
        with console.status("[bold green]Detecting feature drift..."):
            stage = run_drift(**drift_cfg)
        if stage.metrics:
            console.print(stage.metrics)
        _persist_cli_workflow("drift", [stage], params=vars(args))
        _exit_on_stage_error(stage)
        return

    if args.command == "drift-retrain":
        drift_cfg = _resolve_drift_command_config(args)
        train_cfg = _resolve_train_command_config(args)
        cfg = TrainingConfig(
            symbol=train_cfg["symbol"],
            tf=train_cfg["tf"],
            label=train_cfg["label"],
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
        stages = run_drift_then_retrain(
            drift_params={
                "symbol": cfg.symbol,
                "tf": cfg.tf,
                "label": cfg.label,
                "threshold_ks": drift_cfg["threshold_ks"],
                "threshold_psi": drift_cfg["threshold_psi"],
                "min_samples": drift_cfg["min_samples"],
            },
            train_config=cfg,
        )
        if stages:
            console.print({stage.stage: stage.status for stage in stages})
        _persist_cli_workflow("drift-retrain", stages, params=vars(args))
        if any(stage.status == "error" for stage in stages):
            sys.exit(1)
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

        from rich.table import Table  # type: ignore[import-not-found]

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
        try:
            _run_profile_command(args)
            stage = StageResult(
                stage="run-profile",
                status="ok",
                params=vars(args),
            )
        except Exception as exc:  # noqa: BLE001
            stage = StageResult(
                stage="run-profile",
                status="error",
                params=vars(args),
                error=str(exc),
            )
        _persist_cli_workflow("run-profile", [stage], params=vars(args))
        _exit_on_stage_error(stage)
        return

    if args.command == "benchmark":
        stage = _run_benchmark_stage(args)
        _persist_cli_workflow("benchmark", [stage], params=vars(args))
        _exit_on_stage_error(stage)
        return

    if args.command == "run-all":
        try:
            stages = _run_all_command(args)
        except Exception as exc:  # noqa: BLE001
            stages = [
                StageResult(
                    stage="run-all",
                    status="error",
                    params=vars(args),
                    error=str(exc),
                )
            ]
        _persist_cli_workflow("run-all", stages, params=vars(args))
        if any(stage.status == "error" for stage in stages):
            sys.exit(1)
        return


_resolve_train_command_config = resolve_train_config
_resolve_evaluate_command_config = resolve_evaluate_config
_resolve_download_command_config = resolve_download_config
_resolve_pipeline_command_config = resolve_pipeline_config
_resolve_qa_command_config = resolve_qa_config
_resolve_serve_command_config = resolve_serve_config
_resolve_batch_command_config = resolve_batch_config
_resolve_drift_command_config = resolve_drift_config
_print_resolved_train_summary = print_resolved_train_summary
_print_resolved_evaluate_summary = print_resolved_evaluate_summary
_run_profile_command = run_profile_command
_run_benchmark = run_benchmark
_run_benchmark_stage = run_benchmark_stage
