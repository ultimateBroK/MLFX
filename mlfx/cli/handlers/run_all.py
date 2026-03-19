"""Run-all command handler."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

from mlfx.training.backends.base import TrainingConfig
from mlfx.workflow import StageResult
from mlfx.workflow.results import StageStatus
from mlfx.workflow.stages import run_batch, run_download, run_drift_then_retrain, run_pipeline_stage, run_qa
from mlfx.workflow.orchestration import run_benchmark_stage

from ..render import console
from ..resolve import (
    resolve_batch_config,
    resolve_download_config,
    resolve_drift_config,
    resolve_evaluate_config,
    resolve_pipeline_config,
    resolve_qa_config,
    resolve_serve_config,
    resolve_train_config,
)
from ..workflows import run_benchmark_stage

logger = logging.getLogger(__name__)


def _derive_workflow_status(stages: list[StageResult]) -> StageStatus:
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
        status=_derive_workflow_status(stages),
        params=params or {},
    )
    summary_path = persist_workflow_result(result)
    console.print(f"Workflow summary: {summary_path}")


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


def _run_train_command(args: argparse.Namespace) -> StageResult:
    """Resolve and execute the train command."""
    from ..render import print_resolved_train_summary
    from mlfx.workflow.stages import run_train

    train_cfg = resolve_train_config(args)

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

    use_mlflow = getattr(args, "mlflow", False)
    if use_mlflow:
        from mlfx.config.mlflow import MLflowConfig
        config = MLflowConfig()
        config.setup_mlflow()
        console.print(f"MLflow tracking enabled: {config.tracking_uri}")

    cfg = TrainingConfig(
        symbol=train_cfg["symbol"],
        tf=train_cfg["tf"],
        label=train_cfg["label"],
        backend=train_cfg["backend"],
        n_trials=train_cfg["n_trials"],
        n_splits=train_cfg["n_splits"],
        force=train_cfg["force"],
        extra={
            "cv_method": train_cfg["cv_method"],
            "embargo_pct": train_cfg["embargo_pct"],
            "train_start": train_cfg["train_start"],
            "train_end": train_cfg["train_end"],
            "profile": args.profile,
            "use_mlflow": use_mlflow,
        },
    )
    return run_train(cfg)


def _run_evaluate_command(args: argparse.Namespace) -> StageResult:
    """Resolve and execute the evaluate command."""
    from mlfx.config.paths import DEFAULT_PATHS
    from mlfx.workflow.stages import run_evaluate
    from ..render import print_backtest_results, print_resolved_evaluate_summary, t

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
    console.print(f"\n{t('chart_path', path=reports_dir)}")
    return stage


def handle_run_all(args: argparse.Namespace) -> None:
    """Handle the run-all command."""
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
        symbol=args.symbol,
        tf=args.tf,
        label=args.label,
        backend=None,
        n_trials=None,
        n_splits=None,
        cv_method=None,
        embargo_pct=None,
        train_start=None,
        train_end=None,
        force=None,
    )
    eval_args = argparse.Namespace(
        profile=args.profile,
        symbol=args.symbol,
        tf=args.tf,
        label=args.label,
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
        symbol=args.symbol,
        tf=args.tf,
        label=args.label,
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
        download_cfg = resolve_download_config(
            argparse.Namespace(
                symbol=args.symbol,
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
            _finish_run_all(args, stages)
            return

    if args.skip_qa:
        stages.append(_make_skipped_stage("qa", reason="Skipped by --skip-qa"))
    else:
        qa_cfg = resolve_qa_config(
            argparse.Namespace(symbol=args.symbol, asset_class=None)
        )
        if _append(run_qa(**qa_cfg)):
            _finish_run_all(args, stages)
            return

    if args.skip_pipeline:
        stages.append(_make_skipped_stage("pipeline", reason="Skipped by --skip-pipeline"))
    else:
        pipeline_cfg = resolve_pipeline_config(
            argparse.Namespace(
                symbol=args.symbol,
                tf=args.tf,
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
            _finish_run_all(args, stages)
            return

    if args.skip_train:
        stages.append(_make_skipped_stage("train", reason="Skipped by --skip-train"))
    else:
        if _append(_run_train_command(train_args)):
            _finish_run_all(args, stages)
            return

    if args.skip_evaluate:
        stages.append(_make_skipped_stage("evaluate", reason="Skipped by --skip-evaluate"))
    else:
        if _append(_run_evaluate_command(eval_args)):
            _finish_run_all(args, stages)
            return

    if args.skip_benchmark:
        stages.append(_make_skipped_stage("benchmark", reason="Skipped by --skip-benchmark"))
    else:
        if _append(run_benchmark_stage(benchmark_args)):
            _finish_run_all(args, stages)
            return

    if args.skip_serve:
        stages.append(_make_skipped_stage("serve", reason="Skipped by --skip-serve"))
    else:
        serve_cfg = resolve_serve_config(
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
        batch_cfg = resolve_batch_config(
            argparse.Namespace(symbol=None, tf=None, label=None)
        )
        if _append(run_batch(**batch_cfg)):
            _finish_run_all(args, stages)
            return

    if args.skip_drift_retrain:
        stages.append(_make_skipped_stage("drift", reason="Skipped by --skip-drift-retrain"))
        stages.append(_make_skipped_stage("retrain", reason="Skipped by --skip-drift-retrain"))
    else:
        drift_cfg = resolve_drift_config(
            argparse.Namespace(
                symbol=None,
                tf=None,
                label=None,
                threshold_ks=None,
                threshold_psi=None,
                min_samples=None,
            )
        )
        train_cfg = resolve_train_config(train_args)
        training_cfg = TrainingConfig(
            symbol=train_cfg["symbol"],
            tf=train_cfg["tf"],
            label=train_cfg["label"],
            backend=train_cfg["backend"],
            n_trials=train_cfg["n_trials"],
            n_splits=train_cfg["n_splits"],
            force=train_cfg["force"],
            extra={
                "cv_method": train_cfg["cv_method"],
                "embargo_pct": train_cfg["embargo_pct"],
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
                _finish_run_all(args, stages)
                return

    _finish_run_all(args, stages)


def _finish_run_all(args: argparse.Namespace, stages: list[StageResult]) -> None:
    """Persist workflow and handle exit for run-all."""
    if args.json:
        console.print_json(json.dumps({"stages": [stage.to_dict() for stage in stages]}))

    _persist_cli_workflow("run-all", stages, params=vars(args))
    if any(stage.status == "error" for stage in stages):
        sys.exit(1)
