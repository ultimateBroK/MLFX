"""Workflow orchestration helpers for the MLFX CLI."""

from __future__ import annotations

import argparse
import datetime
import json
import time

from rich.table import Table

from mlfx.evaluation.runner import (
    get_baseline_metrics,
    run_full_eval,
    run_model_backtest,
)
from mlfx.training.backends.base import TrainingConfig
from mlfx.training.registry import BACKEND_REGISTRY
from mlfx.training.runner import run_training

from .render import (
    console,
    print_resolved_benchmark_summary,
    print_resolved_evaluate_summary,
    print_resolved_train_summary,
)
from .resolve import (
    resolve_evaluate_command_config,
    resolve_profile_section,
    resolve_train_command_config,
)

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

    if not args.skip_train:
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
        train_cfg = resolve_train_command_config(train_args)
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
        console.print("[yellow]Step:[/] train")
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
        console.print("[yellow]Step:[/] evaluate")

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

        if results:
            console.print(f"[dim]Backtest: {source}[/]")
            if source == "Model":
                baseline = get_baseline_metrics(**eval_kw)
                if baseline is not None:
                    try:
                        model_r = float(
                            results["Net Profit (R)"]
                            .replace("R", "")
                            .replace(",", "")
                            .strip()
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
            table = Table(
                title="Kết quả Backtest",
                show_header=True,
                header_style="bold cyan",
            )
            table.add_column("Chỉ số", style="dim")
            table.add_column("Giá trị", justify="right")
            for key, value in results.items():
                table.add_row(key, value)
            console.print(table)

        summary["steps"]["evaluate"] = {
            "skipped": False,
            "config": eval_cfg,
            "source": source,
            "results": results or {},
        }

    if not args.skip_benchmark:
        console.print("[yellow]Step:[/] benchmark")
        benchmark_args = argparse.Namespace(
            profile=args.profile,
            symbol="XAUUSD",
            tf="1H",
            label="label_10",
            backends=["mlf", "sgd", "stats"],
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
        console.print_json(json.dumps(summary))


def run_benchmark(args: argparse.Namespace) -> dict[str, object]:
    """Run multiple backends on the same dataset and print a comparison table."""
    from mlfx.config.paths import DEFAULT_PATHS
    from mlfx.config.settings import load_config

    backends: list[str] = args.backends
    invalid = [backend for backend in backends if backend not in BACKEND_REGISTRY]
    if invalid:
        console.print(f"[red]Unknown backends: {invalid}. Available: {_ALL_BACKENDS}[/red]")
        return {}

    app_cfg = load_config()
    profile_data = resolve_profile_section(args.profile, "benchmark")

    symbol = args.symbol if args.symbol is not None else profile_data.get("symbol", app_cfg.train.symbol)
    tf = args.tf if args.tf is not None else profile_data.get("timeframe", app_cfg.train.timeframe)
    label = args.label if args.label is not None else profile_data.get("label_col", app_cfg.train.label_col)
    n_trials = args.n_trials if args.n_trials is not None else profile_data.get("n_trials", 5)
    n_splits = args.n_splits if args.n_splits is not None else profile_data.get("n_splits", 3)
    force = args.force if args.force is not None else profile_data.get("force", False)
    train_start = (
        args.train_start if args.train_start is not None else profile_data.get("train_start")
    )
    train_end = args.train_end if args.train_end is not None else profile_data.get("train_end")
    backends = profile_data.get("backends", backends)
    if isinstance(backends, str):
        backends = [backends]

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
                label_col=label,
                backend=backend,
                n_trials=n_trials,
                n_splits=n_splits,
                force=force,
                extra={
                    "train_start": train_start,
                    "train_end": train_end,
                    "profile": args.profile,
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

    console.print()
    table = Table(
        title=f"Benchmark Results — {symbol} {tf} {label}",
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
