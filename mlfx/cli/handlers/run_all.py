"""Run-all command handler."""

from __future__ import annotations

import argparse
import json
import sys

from mlfx.workflow import StageResult
from mlfx.workflow.stages import run_batch, run_download, run_drift_then_retrain, run_pipeline_stage, run_qa

from .._workflow_summary import (
    make_skipped_stage as _make_skipped_stage,
    persist_cli_workflow as _persist_cli_workflow,
)
from ..handlers.evaluate import execute_evaluate_command
from ..handlers.train import build_training_config, execute_train_command
from ..render import console
from ..resolve import (
    resolve_batch_config,
    resolve_download_config,
    resolve_drift_config,
    resolve_pipeline_config,
    resolve_qa_config,
    resolve_serve_config,
    resolve_train_config,
)
from ..workflows import run_benchmark_stage


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
        train_stage, _ = execute_train_command(train_args)
        if _append(train_stage):
            _finish_run_all(args, stages)
            return

    if args.skip_evaluate:
        stages.append(_make_skipped_stage("evaluate", reason="Skipped by --skip-evaluate"))
    else:
        evaluate_stage, _ = execute_evaluate_command(eval_args)
        if _append(evaluate_stage):
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
        training_cfg = build_training_config(
            train_cfg,
            profile=args.profile,
            use_mlflow=False,
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
