"""Drift detection command handlers."""

from __future__ import annotations

import argparse
import sys

from mlfx.workflow.stages import run_drift, run_drift_then_retrain

from .._workflow_summary import (
    exit_on_stage_error as _exit_on_stage_error,
    persist_cli_workflow as _persist_cli_workflow,
)
from ..handlers.train import build_training_config
from ..render import console
from ..resolve import resolve_drift_config, resolve_train_config


def handle_drift(args: argparse.Namespace) -> None:
    """Handle the drift command."""
    drift_cfg = resolve_drift_config(args)
    with console.status("[bold green]Detecting feature drift..."):
        stage = run_drift(**drift_cfg)
    if stage.metrics:
        console.print(stage.metrics)
    _persist_cli_workflow("drift", [stage], params=vars(args))
    _exit_on_stage_error(stage)


def handle_drift_retrain(args: argparse.Namespace) -> None:
    """Handle the drift-retrain command."""
    drift_cfg = resolve_drift_config(args)
    train_cfg = resolve_train_config(args)
    cfg = build_training_config(
        train_cfg,
        profile=args.profile,
        use_mlflow=False,
    )
    stages = list(run_drift_then_retrain(
        drift_params={
            "symbol": cfg.symbol,
            "tf": cfg.tf,
            "label": cfg.label,
            "threshold_ks": drift_cfg["threshold_ks"],
            "threshold_psi": drift_cfg["threshold_psi"],
            "min_samples": drift_cfg["min_samples"],
        },
        train_config=cfg,
    ))
    if stages:
        console.print({stage.stage: stage.status for stage in stages})
    _persist_cli_workflow("drift-retrain", stages, params=vars(args))
    if any(stage.status == "error" for stage in stages):
        sys.exit(1)
