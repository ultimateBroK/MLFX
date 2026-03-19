"""CLI configuration resolution helpers for MLFX."""

from __future__ import annotations

import argparse
from typing import Any

from mlfx.config.schema import AppConfig
from mlfx.config.settings import load_config


def resolve_profile_section(
    cfg: AppConfig,
    profile_name: str | None,
    section: str,
) -> dict[str, Any]:
    """Resolve a command-specific profile section from validated config."""
    if not profile_name:
        return {}

    profile = cfg.profiles.get(profile_name)
    if profile is None:
        available = ", ".join(sorted(cfg.profiles)) or "none"
        raise ValueError(f"Unknown profile '{profile_name}'. Available profiles: {available}")

    section_obj = getattr(profile, section, None)
    if section_obj is None:
        raise ValueError(f"Profile '{profile_name}' does not define a '{section}' section.")

    return section_obj.model_dump(exclude_none=True)


def pick_value(
    cli_value: Any,
    profile_data: dict[str, Any],
    profile_key: str,
    fallback: Any,
) -> Any:
    """Resolve a value with precedence CLI > profile > fallback."""
    if cli_value is not None:
        return cli_value
    if profile_key in profile_data:
        return profile_data[profile_key]
    return fallback


def _ensure_list(value: Any) -> list[Any]:
    """Normalize a scalar-or-list input into a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def resolve_download_config(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve effective download configuration from CLI and defaults."""
    return resolve_download_config_from_settings(args, load_config())


def resolve_download_config_from_settings(
    args: argparse.Namespace,
    cfg: AppConfig,
) -> dict[str, Any]:
    """Resolve effective download configuration from CLI and validated settings."""
    return {
        "symbol": pick_value(args.symbol, {}, "symbol", cfg.download.symbol),
        "asset_class": pick_value(args.asset_class, {}, "asset_class", cfg.download.asset_class),
        "start_year": pick_value(args.start_year, {}, "start_year", cfg.download.start_year),
        "start_month": pick_value(args.start_month, {}, "start_month", cfg.download.start_month),
        "end_year": pick_value(args.end_year, {}, "end_year", cfg.download.end_year),
        "end_month": pick_value(args.end_month, {}, "end_month", cfg.download.end_month),
        "concurrency": pick_value(args.concurrency, {}, "concurrency", cfg.download.concurrency),
        "force": pick_value(args.force, {}, "force", cfg.download.force),
        "skip_current_month": pick_value(
            args.skip_current_month,
            {},
            "skip_current_month",
            cfg.download.skip_current_month,
        ),
    }


def resolve_pipeline_config(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve effective pipeline configuration from CLI and defaults."""
    return resolve_pipeline_config_from_settings(args, load_config())


def resolve_pipeline_config_from_settings(
    args: argparse.Namespace,
    cfg: AppConfig,
) -> dict[str, Any]:
    """Resolve effective pipeline configuration from CLI and validated settings."""
    raw_tf = pick_value(args.tf, {}, "tf", list(cfg.pipeline.tf))
    tf = _ensure_list(raw_tf)
    return {
        "symbol": pick_value(args.symbol, {}, "symbol", cfg.pipeline.symbol),
        "tf": tf,
        "pivot_type": pick_value(args.pivot, {}, "pivot", cfg.pipeline.pivot_type),
        "pivot_anchor": pick_value(args.anchor, {}, "anchor", cfg.pipeline.pivot_anchor),
        "atr_period": pick_value(args.atr_period, {}, "atr_period", cfg.features.atr_period),
        "atr_mult": pick_value(args.atr_mult, {}, "atr_mult", cfg.pipeline.atr_mult),
        "force": pick_value(args.force, {}, "force", cfg.pipeline.force),
        "skip_resample": pick_value(args.skip_resample, {}, "skip_resample", cfg.pipeline.skip_resample),
        "skip_features": pick_value(args.skip_features, {}, "skip_features", cfg.pipeline.skip_features),
        "skip_labels": pick_value(args.skip_labels, {}, "skip_labels", cfg.pipeline.skip_labels),
    }


def resolve_qa_config(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve effective QA configuration from CLI and defaults."""
    return resolve_qa_config_from_settings(args, load_config())


def resolve_qa_config_from_settings(args: argparse.Namespace, cfg: AppConfig) -> dict[str, Any]:
    """Resolve effective QA configuration from CLI and validated settings."""
    return {
        "symbol": pick_value(args.symbol, {}, "symbol", cfg.qa.symbol),
        "asset_class": pick_value(args.asset_class, {}, "asset_class", cfg.qa.asset_class),
    }


def resolve_serve_config(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve effective serving configuration from CLI and defaults."""
    return resolve_serve_config_from_settings(args, load_config())


def resolve_serve_config_from_settings(
    args: argparse.Namespace,
    cfg: AppConfig,
) -> dict[str, Any]:
    """Resolve effective serving configuration from CLI and validated settings."""
    return {
        "host": pick_value(args.host, {}, "host", cfg.serve.host),
        "port": pick_value(args.port, {}, "port", cfg.serve.port),
        "reload": pick_value(args.reload, {}, "reload", cfg.serve.reload),
    }


def resolve_batch_config(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve effective batch prediction configuration from CLI and defaults."""
    return resolve_batch_config_from_settings(args, load_config())


def resolve_batch_config_from_settings(
    args: argparse.Namespace,
    cfg: AppConfig,
) -> dict[str, Any]:
    """Resolve effective batch prediction configuration from CLI and validated settings."""
    return {
        "symbol": pick_value(args.symbol, {}, "symbol", cfg.batch_predict.symbol),
        "tf": pick_value(args.tf, {}, "tf", cfg.batch_predict.tf),
        "label": pick_value(args.label, {}, "label", cfg.batch_predict.label),
    }


def resolve_drift_config(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve effective drift configuration from CLI and defaults."""
    return resolve_drift_config_from_settings(args, load_config())


def resolve_drift_config_from_settings(
    args: argparse.Namespace,
    cfg: AppConfig,
) -> dict[str, Any]:
    """Resolve effective drift configuration from CLI and validated settings."""
    return {
        "symbol": pick_value(args.symbol, {}, "symbol", cfg.drift.symbol),
        "tf": pick_value(args.tf, {}, "tf", cfg.drift.tf),
        "label": pick_value(args.label, {}, "label", cfg.drift.label),
        "threshold_ks": pick_value(args.threshold_ks, {}, "threshold_ks", cfg.drift.threshold_ks),
        "threshold_psi": pick_value(args.threshold_psi, {}, "threshold_psi", cfg.drift.threshold_psi),
        "min_samples": pick_value(args.min_samples, {}, "min_samples", cfg.drift.min_samples),
    }


def resolve_train_config(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve effective train configuration from CLI, profile, and defaults."""
    return resolve_train_config_from_settings(args, load_config())


def resolve_train_config_from_settings(args: argparse.Namespace, cfg: AppConfig) -> dict[str, Any]:
    """Resolve effective train configuration from CLI, profile, and validated settings."""
    profile_data = resolve_profile_section(cfg, getattr(args, "profile", None), "train")

    symbol = pick_value(getattr(args, "symbol", None), profile_data, "symbol", cfg.train.symbol)
    tf = pick_value(getattr(args, "tf", None), profile_data, "tf", cfg.train.tf)
    label = pick_value(getattr(args, "label", None), profile_data, "label", cfg.train.label)
    backend = pick_value(getattr(args, "backend", None), profile_data, "backend", cfg.train.backend)
    n_trials = pick_value(getattr(args, "n_trials", None), profile_data, "n_trials", cfg.train.n_trials)
    n_splits = pick_value(getattr(args, "n_splits", None), profile_data, "n_splits", cfg.train.n_splits)
    cv_method = pick_value(
        getattr(args, "cv_method", None),
        profile_data,
        "cv_method",
        getattr(cfg.train, "cv_method", "purged_timeseries"),
    )
    embargo_pct = pick_value(
        getattr(args, "embargo_pct", None),
        profile_data,
        "embargo_pct",
        getattr(cfg.train, "embargo_pct", 0.01),
    )
    force = pick_value(getattr(args, "force", None), profile_data, "force", cfg.train.force)
    train_start = pick_value(getattr(args, "train_start", None), profile_data, "train_start", cfg.train.train_start)
    train_end = pick_value(getattr(args, "train_end", None), profile_data, "train_end", cfg.train.train_end)

    return {
        "symbol": symbol,
        "tf": tf,
        "label": label,
        "backend": backend,
        "n_trials": n_trials,
        "n_splits": n_splits,
        "cv_method": cv_method,
        "embargo_pct": embargo_pct,
        "force": force,
        "train_start": train_start,
        "train_end": train_end,
    }


def resolve_train_command_config(args: argparse.Namespace) -> dict[str, Any]:
    """Backward-compatible alias for CLI train config resolution."""
    return resolve_train_config(args)


def resolve_evaluate_config(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve effective evaluate configuration from CLI, profile, and defaults."""
    return resolve_evaluate_config_from_settings(args, load_config())


def resolve_evaluate_config_from_settings(args: argparse.Namespace, cfg: AppConfig) -> dict[str, Any]:
    """Resolve effective evaluate configuration from CLI, profile, and validated settings."""
    profile_data = resolve_profile_section(cfg, args.profile, "evaluate")

    symbol = pick_value(args.symbol, profile_data, "symbol", cfg.backtest.symbol)
    tf = pick_value(args.tf, profile_data, "tf", cfg.backtest.tf)
    label = pick_value(args.label, profile_data, "label", cfg.backtest.label)
    capital = pick_value(args.capital, profile_data, "initial_capital", cfg.backtest.initial_capital)
    risk = pick_value(args.risk, profile_data, "risk_pct", cfg.backtest.risk_pct)
    commission = pick_value(args.commission, profile_data, "commission", cfg.backtest.commission)
    tp = pick_value(args.tp, profile_data, "tp_r", cfg.backtest.tp_r)
    sl = pick_value(args.sl, profile_data, "sl_r", cfg.backtest.sl_r)
    slippage = pick_value(args.slippage, profile_data, "slippage", cfg.backtest.slippage)
    eval_start = pick_value(args.eval_start, profile_data, "eval_start", cfg.backtest.eval_start)
    eval_end = pick_value(args.eval_end, profile_data, "eval_end", cfg.backtest.eval_end)
    use_labels = pick_value(args.use_labels, profile_data, "use_labels", cfg.backtest.use_labels)

    return {
        "symbol": symbol,
        "tf": tf,
        "label": label,
        "capital": capital,
        "risk": risk,
        "commission": commission,
        "tp": tp,
        "sl": sl,
        "slippage": slippage,
        "eval_start": eval_start,
        "eval_end": eval_end,
        "use_labels": use_labels,
    }


def resolve_evaluate_command_config(args: argparse.Namespace) -> dict[str, Any]:
    """Backward-compatible alias for CLI evaluate config resolution."""
    return resolve_evaluate_config(args)


def resolve_benchmark_config(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve effective benchmark configuration from CLI, profile, and defaults."""
    return resolve_benchmark_config_from_settings(args, load_config())


def resolve_benchmark_config_from_settings(args: argparse.Namespace, cfg: AppConfig) -> dict[str, Any]:
    """Resolve effective benchmark configuration from CLI, profile, and validated settings."""
    profile_data = resolve_profile_section(cfg, args.profile, "benchmark")

    symbol = pick_value(args.symbol, profile_data, "symbol", cfg.benchmark.symbol)
    tf = pick_value(args.tf, profile_data, "tf", cfg.benchmark.tf)
    label = pick_value(args.label, profile_data, "label", cfg.benchmark.label)
    n_trials = pick_value(args.n_trials, profile_data, "n_trials", cfg.benchmark.n_trials)
    n_splits = pick_value(args.n_splits, profile_data, "n_splits", cfg.benchmark.n_splits)
    force = pick_value(args.force, profile_data, "force", cfg.benchmark.force)
    train_start = pick_value(args.train_start, profile_data, "train_start", cfg.benchmark.train_start)
    train_end = pick_value(args.train_end, profile_data, "train_end", cfg.benchmark.train_end)

    backends = pick_value(args.backends, profile_data, "backends", list(cfg.benchmark.backends))
    if isinstance(backends, str):
        backends = [backends]

    return {
        "profile": args.profile,
        "symbol": symbol,
        "tf": tf,
        "label": label,
        "backends": backends,
        "n_trials": n_trials,
        "n_splits": n_splits,
        "force": force,
        "train_start": train_start,
        "train_end": train_end,
    }


def resolve_benchmark_command_config(args: argparse.Namespace) -> dict[str, Any]:
    """Backward-compatible alias for CLI benchmark config resolution."""
    return resolve_benchmark_config(args)
