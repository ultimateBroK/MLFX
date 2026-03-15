"""Evaluate command handler."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

from mlfx.workflow import StageResult
from mlfx.workflow.stages import run_evaluate

from ..render import (
    console,
    print_backtest_results,
    print_resolved_evaluate_summary,
    t,
)
from ..resolve import resolve_evaluate_config

logger = logging.getLogger(__name__)


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
    from mlfx.workflow import WorkflowResult, persist_workflow_result
    result = WorkflowResult(
        workflow=workflow,
        stages=stages,
        status=_derive_workflow_status(stages),  # type: ignore[arg-type]
        params=params or {},
    )
    summary_path = persist_workflow_result(result)
    console.print(f"Workflow summary: {summary_path}")


def _exit_on_stage_error(stage: StageResult) -> None:
    if stage.status == "error":
        if stage.error:
            logging.getLogger(__name__).error("%s failed: %s", stage.stage, stage.error)
        sys.exit(1)


def handle_evaluate(args: argparse.Namespace) -> None:
    """Handle the evaluate command."""
    from mlfx.config.paths import DEFAULT_PATHS

    eval_cfg = resolve_evaluate_config(args)

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
        _persist_cli_workflow("evaluate", [stage], params=vars(args))
        _exit_on_stage_error(stage)
        return

    results = stage.metrics.get("results") if isinstance(stage.metrics, dict) else None
    source_raw = stage.metrics.get("source") if isinstance(stage.metrics, dict) else None
    baseline = stage.metrics.get("baseline") if isinstance(stage.metrics, dict) else None
    source = {
        "labels": "Labels (baseline)",
        "labels_fallback": "Labels (no model, fallback)",
        "model": "Model",
    }.get(str(source_raw), str(source_raw) if source_raw is not None else "-")

    if results:
        print_backtest_results(results=results, source=source, baseline=baseline)

        risk_dir = f"R{int(eval_cfg['tp'] * 10)}"
        report_mode = "labels" if source != "Model" else "model"
        reports_dir = (
            DEFAULT_PATHS.reports_dir(eval_cfg["symbol"], eval_cfg["tf"])
            / eval_cfg["label"]
            / report_mode
            / risk_dir
        )
        console.print(f"\n{t('chart_path', path=reports_dir)}")

    _persist_cli_workflow("evaluate", [stage], params=vars(args))
    _exit_on_stage_error(stage)
