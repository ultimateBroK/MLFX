"""Stage entrypoints returning canonical StageResult objects."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from mlfx.config.schema import FeatureConfig, PipelineConfig
from mlfx.evaluation.runner import get_baseline_metrics, run_full_eval, run_model_backtest
from mlfx.ingestion.download import run_download_job
from mlfx.monitoring.drift import DriftDetector, save_reference
from mlfx.pipeline.qa import run_quality_audit
from mlfx.pipeline.runner import run_pipeline
from mlfx.serving.batch import run_batch_inference
from mlfx.training.backends.base import TrainingConfig
from mlfx.training.runner import run_training
from mlfx.workflow.results import StageResult, StageStatus


def _finish_stage(
    *,
    stage: str,
    started: float,
    started_at: str,
    status: StageStatus,
    metrics: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    artifacts: dict[str, str] | None = None,
    symbol: str | None = None,
    tf: str | None = None,
    label: str | None = None,
    error: str | None = None,
) -> StageResult:
    ended = perf_counter()
    ended_at = datetime.now(UTC).isoformat()
    return StageResult(
        stage=stage,
        status=status,
        metrics=metrics or {},
        params=params or {},
        artifacts=artifacts or {},
        symbol=symbol,
        tf=tf,
        label=label,
        error=error,
        started_at=started_at,
        ended_at=ended_at,
        elapsed_seconds=round(ended - started, 4),
    )


def run_download(
    *,
    symbol: str,
    asset_class: str,
    start_year: int,
    start_month: int,
    concurrency: int,
    force: bool,
    end_year: int | None = None,
    end_month: int | None = None,
    skip_current_month: bool = False,
) -> StageResult:
    started_at = datetime.now(UTC).isoformat()
    started = perf_counter()
    params = {
        "symbol": symbol,
        "asset_class": asset_class,
        "start_year": start_year,
        "start_month": start_month,
        "end_year": end_year,
        "end_month": end_month,
        "concurrency": concurrency,
        "force": force,
        "skip_current_month": skip_current_month,
    }
    try:
        ok = run_download_job(
            symbol=symbol,
            asset_class=asset_class,
            start_year=start_year,
            start_month=start_month,
            concurrency=concurrency,
            force=force,
            end_year=end_year,
            end_month=end_month,
            skip_current_month=skip_current_month,
        )
        return _finish_stage(
            stage="download",
            started=started,
            started_at=started_at,
            status="ok" if ok else "error",
            metrics={"success": bool(ok)},
            params=params,
            symbol=symbol,
        )
    except Exception as exc:  # noqa: BLE001
        return _finish_stage(
            stage="download",
            started=started,
            started_at=started_at,
            status="error",
            params=params,
            symbol=symbol,
            error=str(exc),
        )


def run_qa(*, symbol: str, asset_class: str) -> StageResult:
    started_at = datetime.now(UTC).isoformat()
    started = perf_counter()
    params = {"symbol": symbol, "asset_class": asset_class}
    try:
        result = run_quality_audit(symbol=symbol, asset_class=asset_class)
        status = "ok" if result.success else "error"
        artifacts: dict[str, str] = {}
        if result.report_path is not None:
            artifacts["report_path"] = str(result.report_path)
        return _finish_stage(
            stage="qa",
            started=started,
            started_at=started_at,
            status=status,
            metrics={"success": result.success},
            artifacts=artifacts,
            params=params,
            symbol=symbol,
            error=result.error,
        )
    except Exception as exc:  # noqa: BLE001
        return _finish_stage(
            stage="qa",
            started=started,
            started_at=started_at,
            status="error",
            params=params,
            symbol=symbol,
            error=str(exc),
        )


def run_pipeline_stage(
    *,
    symbol: str,
    tf: list[str],
    pivot_type: str,
    pivot_anchor: str,
    atr_period: int,
    atr_mult: float,
    force: bool,
    skip_resample: bool = False,
    skip_features: bool = False,
    skip_labels: bool = False,
) -> StageResult:
    started_at = datetime.now(UTC).isoformat()
    started = perf_counter()
    params = {
        "symbol": symbol,
        "tf": tf,
        "pivot_type": pivot_type,
        "pivot_anchor": pivot_anchor,
        "atr_period": atr_period,
        "atr_mult": atr_mult,
        "force": force,
        "skip_resample": skip_resample,
        "skip_features": skip_features,
        "skip_labels": skip_labels,
    }
    try:
        per_tf = run_pipeline(
            symbol=symbol,
            timeframes=tf,
            force=force,
            skip_resample=skip_resample,
            skip_features=skip_features,
            skip_labels=skip_labels,
            feature_cfg=FeatureConfig(atr_period=atr_period),
            pipeline_cfg=PipelineConfig(
                pivot_type=pivot_type,
                pivot_anchor=pivot_anchor,
                atr_mult=atr_mult,
            ),
        )

        return _finish_stage(
            stage="pipeline",
            started=started,
            started_at=started_at,
            status="ok",
            metrics={"timeframes": per_tf, "n_timeframes": len(per_tf)},
            params=params,
            symbol=symbol,
        )
    except Exception as exc:  # noqa: BLE001
        return _finish_stage(
            stage="pipeline",
            started=started,
            started_at=started_at,
            status="error",
            params=params,
            symbol=symbol,
            error=str(exc),
        )


def run_train(
    config: TrainingConfig,
    *,
    enable_tracking: bool = True,
    enable_registry: bool = True,
    save_drift_reference_after_train: bool = True,
) -> StageResult:
    started_at = datetime.now(UTC).isoformat()
    started = perf_counter()
    params = {
        "symbol": config.symbol,
        "tf": config.tf,
        "label": config.label,
        "backend": config.backend,
        "n_trials": config.n_trials,
        "n_splits": config.n_splits,
        "force": config.force,
        **config.extra,
    }
    try:
        metrics = run_training(
            config,
            enable_tracking=enable_tracking,
            enable_registry=enable_registry,
        )
        artifacts: dict[str, str] = {}
        if isinstance(metrics.get("artifact_path"), str):
            artifacts["artifact_path"] = metrics["artifact_path"]

        status = "ok" if metrics else "skipped"

        if save_drift_reference_after_train and metrics:
            from mlfx.training.data import load_labelled_dataset
            from mlfx.training.feature_selection import select_numeric_feature_columns

            df = load_labelled_dataset(
                config.symbol,
                config.tf,
                train_start=config.extra.get("train_start"),
                train_end=config.extra.get("train_end"),
            )
            if df is not None and not df.is_empty():
                selected = metrics.get("selected_features")
                feature_cols = (
                    [col for col in selected if isinstance(col, str)]
                    if isinstance(selected, list)
                    else select_numeric_feature_columns(df)
                )
                if feature_cols:
                    ref_path = save_reference(df, feature_cols, symbol=config.symbol, tf=config.tf)
                    artifacts["drift_reference_path"] = str(ref_path)

        return _finish_stage(
            stage="train",
            started=started,
            started_at=started_at,
            status=status,
            metrics=metrics,
            artifacts=artifacts,
            params=params,
            symbol=config.symbol,
            tf=config.tf,
            label=config.label,
        )
    except Exception as exc:  # noqa: BLE001
        return _finish_stage(
            stage="train",
            started=started,
            started_at=started_at,
            status="error",
            params=params,
            symbol=config.symbol,
            tf=config.tf,
            label=config.label,
            error=str(exc),
        )


def run_evaluate(
    *,
    symbol: str,
    tf: str,
    label: str,
    initial_capital: float,
    risk_pct: float,
    commission: float,
    tp_r: float,
    sl_r: float,
    slippage: float,
    eval_start: str | None = None,
    eval_end: str | None = None,
    use_labels: bool = False,
) -> StageResult:
    started_at = datetime.now(UTC).isoformat()
    started = perf_counter()
    params = {
        "symbol": symbol,
        "tf": tf,
        "label": label,
        "initial_capital": initial_capital,
        "risk_pct": risk_pct,
        "commission": commission,
        "tp_r": tp_r,
        "sl_r": sl_r,
        "slippage": slippage,
        "eval_start": eval_start,
        "eval_end": eval_end,
        "use_labels": use_labels,
    }
    try:
        kwargs = {
            "symbol": symbol,
            "tf": tf,
            "label": label,
            "initial_capital": initial_capital,
            "risk_pct": risk_pct,
            "commission": commission,
            "tp_r": tp_r,
            "sl_r": sl_r,
            "slippage": slippage,
            "train_start": eval_start,
            "train_end": eval_end,
        }
        source = "labels"
        baseline: dict[str, Any] | None = None
        if use_labels:
            results = run_full_eval(**kwargs)
            source = "labels"
        else:
            model_results = run_model_backtest(**kwargs)
            if model_results is None:
                results = run_full_eval(**kwargs)
                source = "labels_fallback"
            else:
                results = model_results
                source = "model"
                baseline = get_baseline_metrics(**kwargs)

        return _finish_stage(
            stage="evaluate",
            started=started,
            started_at=started_at,
            status="ok" if results else "skipped",
            metrics={"results": results, "source": source, "baseline": baseline},
            params=params,
            symbol=symbol,
            tf=tf,
            label=label,
        )
    except Exception as exc:  # noqa: BLE001
        return _finish_stage(
            stage="evaluate",
            started=started,
            started_at=started_at,
            status="error",
            params=params,
            symbol=symbol,
            tf=tf,
            label=label,
            error=str(exc),
        )


def run_batch(*, symbol: str, tf: str, label: str) -> StageResult:
    started_at = datetime.now(UTC).isoformat()
    started = perf_counter()
    params = {"symbol": symbol, "tf": tf, "label": label}
    try:
        metrics = run_batch_inference(symbol=symbol, tf=tf, label=label)
        artifacts: dict[str, str] = {}
        if isinstance(metrics.get("output_path"), str) and metrics["output_path"]:
            artifacts["output_path"] = metrics["output_path"]
        if isinstance(metrics.get("artifact_path"), str) and metrics["artifact_path"]:
            artifacts["artifact_path"] = metrics["artifact_path"]
        return _finish_stage(
            stage="batch",
            started=started,
            started_at=started_at,
            status="ok" if metrics.get("rows", 0) else "skipped",
            metrics=metrics,
            artifacts=artifacts,
            params=params,
            symbol=symbol,
            tf=tf,
            label=label,
        )
    except Exception as exc:  # noqa: BLE001
        return _finish_stage(
            stage="batch",
            started=started,
            started_at=started_at,
            status="error",
            params=params,
            symbol=symbol,
            tf=tf,
            label=label,
            error=str(exc),
        )


def run_drift(
    *,
    symbol: str,
    tf: str,
    label: str | None = None,
    threshold_ks: float,
    threshold_psi: float,
    min_samples: int,
) -> StageResult:
    started_at = datetime.now(UTC).isoformat()
    started = perf_counter()
    params = {
        "symbol": symbol,
        "tf": tf,
        "label": label,
        "threshold_ks": threshold_ks,
        "threshold_psi": threshold_psi,
        "min_samples": min_samples,
    }
    try:
        from mlfx.training.data import load_labelled_dataset

        df = load_labelled_dataset(symbol, tf)
        if df is None or df.is_empty():
            return _finish_stage(
                stage="drift",
                started=started,
                started_at=started_at,
                status="skipped",
                metrics={"n_rows": 0},
                params=params,
                symbol=symbol,
                tf=tf,
                label=label,
                error="No labelled dataset found",
            )

        detector = DriftDetector.load(symbol=symbol, tf=tf)
        report = detector.detect(
            df,
            threshold_ks=threshold_ks,
            threshold_psi=threshold_psi,
            min_samples=min_samples,
        )
        status = "ok"
        return _finish_stage(
            stage="drift",
            started=started,
            started_at=started_at,
            status=status,
            metrics=report,
            params=params,
            symbol=symbol,
            tf=tf,
            label=label,
        )
    except Exception as exc:  # noqa: BLE001
        return _finish_stage(
            stage="drift",
            started=started,
            started_at=started_at,
            status="error",
            params=params,
            symbol=symbol,
            tf=tf,
            label=label,
            error=str(exc),
        )


def run_drift_then_retrain(
    *,
    drift_params: dict[str, Any],
    train_config: TrainingConfig,
) -> list[StageResult]:
    """Run drift detection and train only when drift is detected."""

    drift_result = run_drift(**drift_params)
    stages = [drift_result]
    if drift_result.status != "ok":
        return stages

    n_drifted = int(drift_result.metrics.get("n_drifted", 0))
    if n_drifted <= 0:
        stages.append(
            StageResult(
                stage="retrain",
                status="skipped",
                metrics={"reason": "no_drift_detected", "n_drifted": n_drifted},
                symbol=train_config.symbol,
                tf=train_config.tf,
                label=train_config.label,
            )
        )
        return stages

    retrain_result = run_train(
        train_config,
        enable_tracking=True,
        enable_registry=True,
        save_drift_reference_after_train=True,
    )
    retrain_result.stage = "retrain"
    stages.append(retrain_result)
    return stages
