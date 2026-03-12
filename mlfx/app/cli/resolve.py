"""CLI configuration resolution helpers for MLFX."""

from __future__ import annotations

import argparse
import tomllib
from typing import Any

from mlfx.config.paths import DEFAULT_PATHS
from mlfx.config.settings import load_config


def resolve_profile_section(profile_name: str | None, section: str) -> dict[str, Any]:
    """Load a command-specific profile section from ``config.toml``.

    Parameters
    ----------
    profile_name:
        Name of the workflow profile. If ``None``, returns an empty mapping.
    section:
        Profile subsection to resolve, e.g. ``"train"``, ``"evaluate"``,
        or ``"benchmark"``.

    Returns
    -------
    dict[str, Any]
        Raw section mapping for the requested profile subsection.

    Raises
    ------
    ValueError
        If the config file is missing, the profile does not exist, the section
        is missing, or the section is not a TOML object.
    """
    if not profile_name:
        return {}

    config_path = DEFAULT_PATHS.config_file
    if not config_path.exists():
        raise ValueError(
            f"Profile '{profile_name}' not found because config.toml does not exist."
        )

    with config_path.open("rb") as handle:
        data = tomllib.load(handle)

    profiles = data.get("profiles", {})
    profile = profiles.get(profile_name)
    if profile is None:
        available = ", ".join(sorted(profiles)) or "none"
        raise ValueError(
            f"Unknown profile '{profile_name}'. Available profiles: {available}"
        )

    section_data = profile.get(section)
    if section_data is None:
        raise ValueError(
            f"Profile '{profile_name}' does not define a '{section}' section."
        )

    if not isinstance(section_data, dict):
        raise ValueError(
            f"Profile '{profile_name}.{section}' must be a TOML table/object."
        )

    return section_data


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
    app_cfg = load_config()
    profile_data = resolve_profile_section(args.profile, "train")

    symbol = pick_value(args.symbol, profile_data, "symbol", app_cfg.train.symbol)
    tf = pick_value(args.tf, profile_data, "timeframe", app_cfg.train.timeframe)
    label = pick_value(args.label, profile_data, "label_col", app_cfg.train.label_col)
    backend = pick_value(args.backend, profile_data, "backend", app_cfg.train.backend)
    n_trials = pick_value(args.n_trials, profile_data, "n_trials", app_cfg.train.n_trials)
    n_splits = pick_value(args.n_splits, profile_data, "n_splits", app_cfg.train.n_splits)
    force = pick_value(args.force, profile_data, "force", True)
    train_start = pick_value(args.train_start, profile_data, "train_start", None)
    train_end = pick_value(args.train_end, profile_data, "train_end", None)

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
    app_cfg = load_config()
    profile_data = resolve_profile_section(args.profile, "evaluate")

    symbol = pick_value(args.symbol, profile_data, "symbol", app_cfg.backtest.symbol)
    tf = pick_value(args.tf, profile_data, "timeframe", app_cfg.backtest.timeframe)
    label = pick_value(args.label, profile_data, "label_col", app_cfg.backtest.label_col)
    capital = pick_value(
        args.capital,
        profile_data,
        "initial_capital",
        app_cfg.backtest.initial_capital,
    )
    risk = pick_value(args.risk, profile_data, "risk_pct", app_cfg.backtest.risk_pct)
    commission = pick_value(
        args.commission,
        profile_data,
        "commission",
        app_cfg.backtest.commission,
    )
    tp = pick_value(args.tp, profile_data, "tp_r", app_cfg.backtest.tp_r)
    sl = pick_value(args.sl, profile_data, "sl_r", app_cfg.backtest.sl_r)
    slippage = pick_value(args.slippage, profile_data, "slippage", 0.0)
    eval_start = pick_value(args.eval_start, profile_data, "eval_start", None)
    eval_end = pick_value(args.eval_end, profile_data, "eval_end", None)
    use_labels = pick_value(args.use_labels, profile_data, "use_labels", False)

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
    app_cfg = load_config()
    profile_data = resolve_profile_section(args.profile, "benchmark")

    symbol = pick_value(args.symbol, profile_data, "symbol", app_cfg.train.symbol)
    tf = pick_value(args.tf, profile_data, "timeframe", app_cfg.train.timeframe)
    label = pick_value(args.label, profile_data, "label_col", app_cfg.train.label_col)
    n_trials = pick_value(args.n_trials, profile_data, "n_trials", 5)
    n_splits = pick_value(args.n_splits, profile_data, "n_splits", 3)
    force = pick_value(args.force, profile_data, "force", False)
    train_start = pick_value(args.train_start, profile_data, "train_start", None)
    train_end = pick_value(args.train_end, profile_data, "train_end", None)

    backends = profile_data.get("backends", args.backends)
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
