"""Workflow orchestration helpers for the MLFX CLI."""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import time

from mlfx.evaluation.runner import (
    get_baseline_metrics,
    run_full_eval,
    run_model_backtest,
)
from mlfx.workflow.results import StageResult
from mlfx.training.backends.base import TrainingConfig
from mlfx.training.registry import BACKEND_REGISTRY
from mlfx.training.runner import run_training

from .render import (
    console,
    print_resolved_benchmark_summary,
    print_resolved_evaluate_summary,
    print_resolved_train_summary,
    t,
)
from .resolve import (
    resolve_benchmark_config,
    resolve_evaluate_command_config,
    resolve_train_command_config,
)

logger = logging.getLogger(__name__)

_ALL_BACKENDS = sorted(BACKEND_REGISTRY)


def run_profile_command(args: argparse.Namespace) -> None:
    """Orchestrate train, evaluate, and optional benchmark using one workflow profile."""
    if args.skip_train and args.skip_evaluate and args.skip_benchmark:
        raise ValueError(
            "run-profile cannot skip train, evaluate, and benchmark at the same time"
        )

    summary: dict[str, object] = {
        "profile": args.profile,
        "steps": {
            "train": {"skipped": bool(args.skip_train)},
            "evaluate": {"skipped": bool(args.skip_evaluate)},
            "benchmark": {"skipped": bool(args.skip_benchmark)},
        },
    }

    console.rule(f"[bold cyan]MLFX Run Profile — {args.profile}[/]")

    # Resolve train config upfront to get backend for evaluation
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
        force=args.force,
    )
    train_cfg = resolve_train_command_config(train_args)

    if not args.skip_train:
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
        console.rule(f"[bold yellow]{t('step_train')}[/]")
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
        train_metrics = run_training(cfg)
        summary["steps"]["train"] = {
            "skipped": False,
            "config": train_cfg,
            "metrics": train_metrics,
        }

    if not args.skip_evaluate:
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
        eval_cfg = resolve_evaluate_command_config(eval_args)
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
        console.rule(f"[bold yellow]{t('step_evaluate')}[/]")

        # Use the same backend as defined in the profile's train section
        eval_backend = train_cfg["backend"]

        eval_kw = dict(
            symbol=eval_cfg["symbol"],
            tf=eval_cfg["tf"],
            label=eval_cfg["label"],
            initial_capital=eval_cfg["capital"],
            risk_pct=eval_cfg["risk"],
            commission=eval_cfg["commission"],
            tp_r=eval_cfg["tp"],
            sl_r=eval_cfg["sl"],
            slippage=eval_cfg["slippage"],
            train_start=eval_cfg["eval_start"],
            train_end=eval_cfg["eval_end"],
            backend=eval_backend,
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

        if results:
            # Use the shared print_backtest_results function for consistency
            from .render import print_backtest_results
            baseline = None
            if source == "Model":
                # Filter out backend param not accepted by get_baseline_metrics
                baseline_kw = {k: v for k, v in eval_kw.items() if k != "backend"}
                baseline = get_baseline_metrics(**baseline_kw)
            print_backtest_results(results=results, source=source, baseline=baseline)

        summary["steps"]["evaluate"] = {
            "skipped": False,
            "config": eval_cfg,
            "source": source,
            "results": results or {},
        }

    if not args.skip_benchmark:
        console.rule(f"[bold yellow]{t('step_benchmark')}[/]")
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
        benchmark_result = run_benchmark(benchmark_args)
        summary["steps"]["benchmark"] = {
            "skipped": False,
            "result": benchmark_result,
        }

    if args.json:
        # Save JSON summary to file instead of stdout
        from datetime import datetime
        from mlfx.config.paths import DEFAULT_PATHS

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_name = args.profile or "default"
        json_filename = f"{timestamp}_{profile_name}_summary.json"
        json_path = DEFAULT_PATHS.runs_root / json_filename
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(summary, indent=2, default=str))
        console.print(f"[dim]JSON summary saved to: {json_path}[/]")


def run_benchmark(args: argparse.Namespace) -> dict[str, object]:
    """Run multiple backends on the same dataset and print a comparison table."""
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
        console.print(f"[dim]MLflow tracking enabled: {config.tracking_uri}[/]")

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
    from .render import print_benchmark_results_table
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
    console.print(f"\n[dim]Report saved → {report_path}[/]")

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
