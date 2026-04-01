"""Train command handler."""

from __future__ import annotations

import argparse
from typing import Any

from mlfx.workflow import StageResult
from mlfx.training.backends.base import TrainingConfig
from mlfx.workflow.stages import run_train

from .. import render as render_cli
from .. import resolve as resolve_cli
from .._workflow_summary import (
    exit_on_stage_error as _exit_on_stage_error,
    persist_cli_workflow as _persist_cli_workflow,
)


def build_training_config(
    train_cfg: dict[str, Any],
    *,
    profile: str | None,
    use_mlflow: bool,
) -> TrainingConfig:
    """Build the canonical training config from resolved CLI values."""
    return TrainingConfig(
        symbol=train_cfg["symbol"],
        tf=train_cfg["tf"],
        label=train_cfg["label"],
        backend=train_cfg["backend"],
        n_trials=train_cfg["n_trials"],
        n_splits=train_cfg["n_splits"],
        force=train_cfg["force"],
        extra={
            "cv_method": train_cfg.get("cv_method", "purged_timeseries"),
            "embargo_pct": train_cfg.get("embargo_pct", 0.01),
            "train_start": train_cfg["train_start"],
            "train_end": train_cfg["train_end"],
            "profile": profile,
            "use_mlflow": use_mlflow,
        },
    )


def execute_train_command(
    args: argparse.Namespace,
    *,
    render_summary: bool = True,
) -> tuple[StageResult, dict[str, Any]]:
    """Resolve and execute the train command."""
    train_cfg = resolve_cli.resolve_train_command_config(args)

    if render_summary:
        render_cli.print_resolved_train_summary(
            profile=getattr(args, "profile", None),
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
        render_cli.console.print(f"MLflow tracking enabled: {config.tracking_uri}")

    stage = run_train(
        build_training_config(
            train_cfg,
            profile=getattr(args, "profile", None),
            use_mlflow=use_mlflow,
        )
    )
    return stage, train_cfg


def handle_train(args: argparse.Namespace) -> None:
    """Handle the train command."""
    stage, _ = execute_train_command(args)
    _persist_cli_workflow("train", [stage], params=vars(args))
    _exit_on_stage_error(stage)
