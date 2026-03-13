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


def resolve_train_config(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve effective train configuration from CLI, profile, and defaults."""
    return resolve_train_config_from_settings(args, load_config())


def resolve_train_config_from_settings(args: argparse.Namespace, cfg: AppConfig) -> dict[str, Any]:
    """Resolve effective train configuration from CLI, profile, and validated settings."""
    profile_data = resolve_profile_section(cfg, args.profile, "train")

    symbol = pick_value(args.symbol, profile_data, "symbol", cfg.train.symbol)
    tf = pick_value(args.tf, profile_data, "tf", cfg.train.tf)
    label = pick_value(args.label, profile_data, "label", cfg.train.label)
    backend = pick_value(args.backend, profile_data, "backend", cfg.train.backend)
    n_trials = pick_value(args.n_trials, profile_data, "n_trials", cfg.train.n_trials)
    n_splits = pick_value(args.n_splits, profile_data, "n_splits", cfg.train.n_splits)
    force = pick_value(args.force, profile_data, "force", cfg.train.force)
    train_start = pick_value(args.train_start, profile_data, "train_start", cfg.train.train_start)
    train_end = pick_value(args.train_end, profile_data, "train_end", cfg.train.train_end)

    return {
        "symbol": symbol,
        "tf": tf,
        "label": label,
        "backend": backend,
        "n_trials": n_trials,
        "n_splits": n_splits,
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
