"""Workflow orchestration helpers for MLFX.

This module contains high-level orchestration helpers for composite workflow
operations that are not owned by individual CLI command handlers.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import time

from mlfx.workflow.results import StageResult
from mlfx.training.backends.base import TrainingConfig
from mlfx.training.registry import BACKEND_REGISTRY
from mlfx.training.runner import run_training

logger = logging.getLogger(__name__)

_ALL_BACKENDS = sorted(BACKEND_REGISTRY)


def run_profile_command(args: argparse.Namespace) -> None:
    """Compatibility shim for the CLI-owned run-profile workflow."""
    from mlfx.cli.workflows import run_profile_command as cli_run_profile_command

    cli_run_profile_command(args)


def run_benchmark(args: argparse.Namespace) -> dict[str, object]:
    """Run multiple backends on the same dataset and print a comparison table."""
    from mlfx.cli.render import (
        console,
        print_resolved_benchmark_summary,
        print_benchmark_results_table,
    )
    from mlfx.cli.resolve import resolve_benchmark_config
    from mlfx.config.paths import DEFAULT_PATHS

    resolved = resolve_benchmark_config(args)
    symbol = resolved["symbol"]
    tf = resolved["tf"]
    label = resolved["label"]
    n_trials = resolved["n_trials"]
    n_splits = resolved["n_splits"]
    force = resolved["force"]
    train_start = resolved["train_start"]
    train_end = resolved["train_end"]
    backends = resolved["backends"]

    # Validate backends after resolution
    invalid = [backend for backend in backends if backend not in BACKEND_REGISTRY]
    if invalid:
        console.print(f"[red]Unknown backends: {invalid}. Available: {_ALL_BACKENDS}[/red]")
        return {}

    # Enable MLflow if flag is set
    use_mlflow = getattr(args, "mlflow", False)
    if use_mlflow:
        from mlfx.config.mlflow import MLflowConfig
        config = MLflowConfig()
        config.setup_mlflow()
        console.print(f"MLflow tracking enabled: {config.tracking_uri}")

    print_resolved_benchmark_summary(
        profile=args.profile,
        symbol=symbol,
        tf=tf,
        label=label,
        backends=backends,
        n_trials=n_trials,
        n_splits=n_splits,
        train_start=train_start,
        train_end=train_end,
        force=force,
    )

    console.rule(f"[bold cyan]MLFX Benchmark — {symbol} {tf} {label}[/]")
    console.print(
        f"Backends: {', '.join(backends)}  |  n_trials={n_trials}  n_splits={n_splits}\n"
    )

    results: list[dict[str, str]] = []

    for backend in backends:
        console.print(f"[yellow]Running:[/] {backend} ...", end="  ")
        t0 = time.perf_counter()
        try:
            cfg = TrainingConfig(
                symbol=symbol,
                tf=tf,
                label=label,
                backend=backend,
                n_trials=n_trials,
                n_splits=n_splits,
                force=force,
                extra={
                    "train_start": train_start,
                    "train_end": train_end,
                    "profile": args.profile,
                    "use_mlflow": use_mlflow,
                },
            )
            metrics = run_training(cfg, enable_tracking=not use_mlflow, enable_registry=not use_mlflow)
            if use_mlflow:
                # MLflow tracking handles its own metrics
                pass

            # If metrics are empty/zeros (model existed, no retrain), retrieve from registry
            if not metrics.get("best_cv_f1_macro") and not force:
                from mlfx.registry import get_registry
                registry = get_registry(use_mlflow=False)
                entry = registry.best_model(symbol=symbol, tf=tf, label=label, backend=backend)
                if entry and entry.get("metrics"):
                    metrics = {**metrics, **entry["metrics"]}
                    logger.debug("Retrieved cached metrics from registry for %s", backend)

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

    # Use the shared benchmark results table function
    print_benchmark_results_table(symbol=symbol, tf=tf, label=label, results=results)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = DEFAULT_PATHS.reports_dir(symbol, tf) / label / "benchmark"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"benchmark_{ts}.json"

    payload = {
        "profile": args.profile,
        "symbol": symbol,
        "tf": tf,
        "label": label,
        "n_trials": n_trials,
        "n_splits": n_splits,
        "train_start": train_start,
        "train_end": train_end,
        "timestamp": ts,
        "results": results,
    }
    report_path.write_text(json.dumps(payload, indent=2))
    console.print(f"\nReport saved → {report_path}")

    return {
        "profile": args.profile,
        "symbol": symbol,
        "tf": tf,
        "label": label,
        "n_trials": n_trials,
        "n_splits": n_splits,
        "train_start": train_start,
        "train_end": train_end,
        "results": results,
        "report_path": str(report_path),
    }


def run_benchmark_stage(args: argparse.Namespace) -> StageResult:
    """Run benchmark and return a canonical StageResult payload."""
    try:
        result = run_benchmark(args)
    except Exception as exc:  # noqa: BLE001
        return StageResult(
            stage="benchmark",
            status="error",
            params=vars(args),
            error=str(exc),
        )

    benchmark_ok = bool(result)
    benchmark_symbol: str | None = None
    benchmark_tf: str | None = None
    benchmark_label: str | None = None
    if isinstance(result, dict):
        symbol_value = result.get("symbol")
        tf_value = result.get("tf")
        label_value = result.get("label")
        if isinstance(symbol_value, str):
            benchmark_symbol = symbol_value
        if isinstance(tf_value, str):
            benchmark_tf = tf_value
        if isinstance(label_value, str):
            benchmark_label = label_value

    return StageResult(
        stage="benchmark",
        status="ok" if benchmark_ok else "error",
        metrics=result if isinstance(result, dict) else {},
        params=vars(args),
        symbol=benchmark_symbol,
        tf=benchmark_tf,
        label=benchmark_label,
        error=None if benchmark_ok else "Benchmark run returned no results",
    )
