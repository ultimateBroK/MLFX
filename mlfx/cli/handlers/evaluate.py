"""Evaluate command handler."""

from __future__ import annotations

import argparse
from typing import Any

from mlfx.workflow import StageResult
from mlfx.workflow.stages import run_evaluate

from .. import render as render_cli
from .. import resolve as resolve_cli
from .._workflow_summary import (
    exit_on_stage_error as _exit_on_stage_error,
    persist_cli_workflow as _persist_cli_workflow,
)


def execute_evaluate_command(
    args: argparse.Namespace,
    *,
    render_summary: bool = True,
) -> tuple[StageResult, dict[str, Any]]:
    """Resolve and execute the evaluate command."""
    from mlfx.config.paths import DEFAULT_PATHS

    eval_cfg = resolve_cli.resolve_evaluate_command_config(args)

    if render_summary:
        render_cli.print_resolved_evaluate_summary(
            profile=getattr(args, "profile", None),
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
        return stage, eval_cfg

    results = stage.metrics.get("results") if isinstance(stage.metrics, dict) else None
    source_raw = stage.metrics.get("source") if isinstance(stage.metrics, dict) else None
    baseline = stage.metrics.get("baseline") if isinstance(stage.metrics, dict) else None
    source = {
        "labels": "Labels (baseline)",
        "labels_fallback": "Labels (no model, fallback)",
        "model": "Model",
    }.get(str(source_raw), str(source_raw) if source_raw is not None else "-")

    if results:
        render_cli.print_backtest_results(results=results, source=source, baseline=baseline)

        risk_dir = f"R{int(eval_cfg['tp'] * 10)}"
        report_mode = "labels" if source != "Model" else "model"
        reports_dir = (
            DEFAULT_PATHS.reports_dir(eval_cfg["symbol"], eval_cfg["tf"])
            / eval_cfg["label"]
            / report_mode
            / risk_dir
        )
        render_cli.console.print(f"\n{render_cli.t('chart_path', path=reports_dir)}")

    return stage, eval_cfg


def handle_evaluate(args: argparse.Namespace) -> None:
    """Handle the evaluate command."""
    stage, _ = execute_evaluate_command(args)
    _persist_cli_workflow("evaluate", [stage], params=vars(args))
    _exit_on_stage_error(stage)
