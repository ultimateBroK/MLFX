"""Workflow orchestration helpers for the MLFX CLI."""

from __future__ import annotations

import argparse
import json

from mlfx.workflow import orchestration as workflow_orchestration


def run_profile_command(args: argparse.Namespace) -> None:
    """Orchestrate train, evaluate, and optional benchmark using one workflow profile."""
    from mlfx.cli.handlers.evaluate import execute_evaluate_command
    from mlfx.cli.handlers.train import execute_train_command
    from mlfx.cli.render import console, t

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

    train_args = argparse.Namespace(
        profile=args.profile,
        symbol=None,
        tf=None,
        label=None,
        backend=None,
        n_trials=None,
        n_splits=None,
        cv_method=None,
        embargo_pct=None,
        train_start=None,
        train_end=None,
        force=args.force,
        mlflow=False,
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

    if not args.skip_train:
        console.rule(f"[bold yellow]{t('step_train')}[/]")
        train_stage, train_cfg = execute_train_command(train_args)
        if train_stage.status == "error":
            raise RuntimeError(train_stage.error or "train failed")
        summary["steps"]["train"] = {
            "skipped": False,
            "config": train_cfg,
            "metrics": dict(train_stage.metrics),
        }

    if not args.skip_evaluate:
        console.rule(f"[bold yellow]{t('step_evaluate')}[/]")
        eval_stage, eval_cfg = execute_evaluate_command(eval_args)
        if eval_stage.status == "error":
            raise RuntimeError(eval_stage.error or "evaluate failed")

        results = (
            eval_stage.metrics.get("results")
            if isinstance(eval_stage.metrics, dict)
            else None
        )
        source_raw = (
            eval_stage.metrics.get("source")
            if isinstance(eval_stage.metrics, dict)
            else None
        )
        source = {
            "labels": "Labels (baseline)",
            "labels_fallback": "Labels (no model, fallback)",
            "model": "Model",
        }.get(str(source_raw), str(source_raw) if source_raw is not None else "-")

        summary["steps"]["evaluate"] = {
            "skipped": False,
            "config": eval_cfg,
            "source": source,
            "results": results or {},
        }

    if not args.skip_benchmark:
        console.rule(f"[bold yellow]{t('step_benchmark')}[/]")
        benchmark_result = workflow_orchestration.run_benchmark(benchmark_args)
        summary["steps"]["benchmark"] = {
            "skipped": False,
            "result": benchmark_result,
        }

    if args.json:
        from datetime import datetime

        from mlfx.config.paths import DEFAULT_PATHS

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_name = args.profile or "default"
        json_filename = f"{timestamp}_{profile_name}_summary.json"
        json_path = DEFAULT_PATHS.runs_root / json_filename
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(summary, indent=2, default=str))
        console.print(f"JSON summary saved to: {json_path}")


run_benchmark = workflow_orchestration.run_benchmark
run_benchmark_stage = workflow_orchestration.run_benchmark_stage

__all__ = [
    "run_benchmark",
    "run_benchmark_stage",
    "run_profile_command",
]
