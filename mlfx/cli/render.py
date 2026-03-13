"""Rendering helpers for the MLFX CLI."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


def _fmt_range(start: str | None, end: str | None) -> str:
    """Format an inclusive date window for terminal display."""
    if start and end:
        return f"{start} → {end}"
    if start:
        return f"{start} → ..."
    if end:
        return f"... → {end}"
    return "-"


def _fmt_symbol_tf(*sections: Mapping[str, Any]) -> str:
    """Format symbol/timeframe summary across one or more config sections."""
    symbol = "-"
    timeframe = "-"
    for section in sections:
        if not section:
            continue
        symbol = str(section.get("symbol") or symbol)
        timeframe = str(section.get("tf") or timeframe)
    return f"{symbol}/{timeframe}" if symbol != "-" or timeframe != "-" else "-"


def _fmt_backends(train_cfg: Mapping[str, Any], benchmark_cfg: Mapping[str, Any]) -> str:
    """Format backend display for profile summary tables."""
    benchmark_backends = benchmark_cfg.get("backends")
    if isinstance(benchmark_backends, Sequence) and not isinstance(benchmark_backends, str):
        values = [str(item) for item in benchmark_backends if item is not None]
        if values:
            return ", ".join(values)
    backend_value = train_cfg.get("backend")
    return str(backend_value) if backend_value is not None else "-"


def print_profiles_summary(profile_name: str | None, profiles: Mapping[str, Any]) -> None:
    """Render either a profile overview table or one detailed profile view."""
    if not isinstance(profiles, Mapping) or not profiles:
        console.print("[yellow]No workflow profiles found in config.toml.[/yellow]")
        return

    if profile_name is not None:
        profile = profiles.get(profile_name)
        if not isinstance(profile, Mapping):
            available = ", ".join(sorted(str(name) for name in profiles)) or "none"
            console.print(
                f"[red]Unknown profile '{profile_name}'. Available profiles: {available}[/red]"
            )
            return
        print_profile_detail(profile_name, profile)
        console.print("[dim]Tip: remove --profile to see the overview table.[/]")
        return

    table = Table(title="Available Workflow Profiles", show_header=True, header_style="bold cyan")
    table.add_column("Profile", style="bold")
    table.add_column("Train", justify="center")
    table.add_column("Evaluate", justify="center")
    table.add_column("Benchmark", justify="center")
    table.add_column("Symbol/TF", justify="left")
    table.add_column("Train Window", justify="left")
    table.add_column("Eval Window", justify="left")
    table.add_column("Backend(s)", justify="left")

    for current_profile_name in sorted(str(name) for name in profiles):
        profile = profiles.get(current_profile_name, {})
        if not isinstance(profile, Mapping):
            continue

        train_cfg = profile.get("train") if isinstance(profile.get("train"), Mapping) else {}
        eval_cfg = profile.get("evaluate") if isinstance(profile.get("evaluate"), Mapping) else {}
        benchmark_cfg = (
            profile.get("benchmark") if isinstance(profile.get("benchmark"), Mapping) else {}
        )

        symbol_tf = _fmt_symbol_tf(train_cfg, eval_cfg, benchmark_cfg)
        train_window = _fmt_range(
            train_cfg.get("train_start"),
            train_cfg.get("train_end"),
        )
        eval_window = _fmt_range(
            eval_cfg.get("eval_start"),
            eval_cfg.get("eval_end"),
        )
        backend_value = _fmt_backends(train_cfg, benchmark_cfg)

        table.add_row(
            current_profile_name,
            "✓" if train_cfg else "-",
            "✓" if eval_cfg else "-",
            "✓" if benchmark_cfg else "-",
            symbol_tf,
            train_window,
            eval_window,
            backend_value,
        )

    console.print(table)
    console.print("[dim]Use with: mlfx train|evaluate|benchmark --profile <name>[/]")
    console.print("[dim]For one profile only: mlfx profiles --profile <name>[/]")


def print_profile_detail(name: str, profile: Mapping[str, Any]) -> None:
    """Render one workflow profile in detailed form."""
    train_cfg = profile.get("train") if isinstance(profile.get("train"), Mapping) else {}
    eval_cfg = profile.get("evaluate") if isinstance(profile.get("evaluate"), Mapping) else {}
    benchmark_cfg = profile.get("benchmark") if isinstance(profile.get("benchmark"), Mapping) else {}

    detail = Table(
        title=f"Workflow Profile: {name}",
        show_header=True,
        header_style="bold cyan",
    )
    detail.add_column("Section", style="bold")
    detail.add_column("Details")

    train_details = (
        f"symbol/tf={_fmt_symbol_tf(train_cfg)} | "
        f"label={train_cfg.get('label', '-')} | "
        f"backend={train_cfg.get('backend', '-')} | "
        f"window={_fmt_range(train_cfg.get('train_start'), train_cfg.get('train_end'))} | "
        f"trials={train_cfg.get('n_trials', '-')} | "
        f"splits={train_cfg.get('n_splits', '-')}"
        if train_cfg
        else "-"
    )
    eval_details = (
        f"symbol/tf={_fmt_symbol_tf(eval_cfg)} | "
        f"label={eval_cfg.get('label', '-')} | "
        f"window={_fmt_range(eval_cfg.get('eval_start'), eval_cfg.get('eval_end'))} | "
        f"tp/sl={eval_cfg.get('tp_r', '-')}/{eval_cfg.get('sl_r', '-')} | "
        f"capital={eval_cfg.get('initial_capital', '-')} | "
        f"risk={eval_cfg.get('risk_pct', '-')} | "
        f"commission={eval_cfg.get('commission', '-')} | "
        f"slippage={eval_cfg.get('slippage', '-')}"
        if eval_cfg
        else "-"
    )
    benchmark_details = (
        f"symbol/tf={_fmt_symbol_tf(benchmark_cfg)} | "
        f"label={benchmark_cfg.get('label', '-')} | "
        f"backends={_fmt_backends({}, benchmark_cfg)} | "
        f"window={_fmt_range(benchmark_cfg.get('train_start'), benchmark_cfg.get('train_end'))} | "
        f"trials={benchmark_cfg.get('n_trials', '-')} | "
        f"splits={benchmark_cfg.get('n_splits', '-')}"
        if benchmark_cfg
        else "-"
    )

    detail.add_row("Train", train_details)
    detail.add_row("Evaluate", eval_details)
    detail.add_row("Benchmark", benchmark_details)
    console.print(detail)


def print_resolved_train_summary(
    *,
    profile: str | None,
    symbol: str,
    tf: str,
    label: str,
    backend: str,
    n_trials: int,
    n_splits: int,
    train_start: str | None,
    train_end: str | None,
    force: bool,
) -> None:
    """Render the fully resolved train configuration."""
    table = Table(title="Resolved Train Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="dim")
    table.add_column("Value", justify="right")
    table.add_row("Profile", profile or "(none)")
    table.add_row("Symbol", symbol)
    table.add_row("Timeframe", tf)
    table.add_row("Label", label)
    table.add_row("Backend", backend)
    table.add_row("Train Start", train_start or "(full dataset)")
    table.add_row("Train End", train_end or "(full dataset)")
    table.add_row("Optuna Trials", str(n_trials))
    table.add_row("CV Splits", str(n_splits))
    table.add_row("Force Retrain", str(force))
    console.print(table)
    console.print()


def print_resolved_evaluate_summary(
    *,
    profile: str | None,
    symbol: str,
    tf: str,
    label: str,
    capital: float,
    risk: float,
    commission: float,
    tp: float,
    sl: float,
    slippage: float,
    eval_start: str | None,
    eval_end: str | None,
    use_labels: bool,
) -> None:
    """Render the fully resolved evaluation configuration."""
    table = Table(
        title="Resolved Evaluate Configuration",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Setting", style="dim")
    table.add_column("Value", justify="right")
    table.add_row("Profile", profile or "(none)")
    table.add_row("Symbol", symbol)
    table.add_row("Timeframe", tf)
    table.add_row("Label", label)
    table.add_row("Mode", "labels" if use_labels else "model -> labels fallback")
    table.add_row("Eval Start", eval_start or "(full dataset)")
    table.add_row("Eval End", eval_end or "(full dataset)")
    table.add_row("Initial Capital", f"{capital}")
    table.add_row("Risk %", f"{risk}")
    table.add_row("Commission", f"{commission}")
    table.add_row("TP (R)", f"{tp}")
    table.add_row("SL (R)", f"{sl}")
    table.add_row("Slippage", f"{slippage}")
    console.print(table)
    console.print()


def print_resolved_benchmark_summary(
    *,
    profile: str | None,
    symbol: str,
    tf: str,
    label: str,
    backends: Sequence[str],
    n_trials: int,
    n_splits: int,
    train_start: str | None,
    train_end: str | None,
    force: bool,
) -> None:
    """Render the fully resolved benchmark configuration."""
    table = Table(
        title="Resolved Benchmark Configuration",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Setting", style="dim")
    table.add_column("Value", justify="right")
    table.add_row("Profile", profile or "(none)")
    table.add_row("Symbol", symbol)
    table.add_row("Timeframe", tf)
    table.add_row("Label", label)
    table.add_row("Backends", ", ".join(backends))
    table.add_row("Train Start", train_start or "(full dataset)")
    table.add_row("Train End", train_end or "(full dataset)")
    table.add_row("Optuna Trials", str(n_trials))
    table.add_row("CV Splits", str(n_splits))
    table.add_row("Force Retrain", str(force))
    console.print(table)
    console.print()


def print_backtest_results(
    *,
    results: Mapping[str, Any],
    source: str,
    baseline: Mapping[str, Any] | None = None,
) -> None:
    """Render backtest results and optional model-vs-label comparison."""
    console.print(f"[dim]Backtest: {source}[/]")

    if source == "Model" and baseline is not None:
        try:
            model_r = float(
                str(results["Net Profit (R)"]).replace("R", "").replace(",", "").strip()
            )
            base_r = float(baseline["total_r"])
            diff = model_r - base_r
            if diff > 0:
                diff_str = f"model tốt hơn +{diff:.1f}R"
            elif diff < 0:
                diff_str = f"labels tốt hơn {-diff:.1f}R"
            else:
                diff_str = "bằng nhau"
            console.print(
                f"[dim]So với labels: model {model_r:+.1f}R vs labels {base_r:+.1f}R → {diff_str}[/]"
            )
        except (ValueError, KeyError, TypeError):
            pass

    table = Table(title="Kết quả Backtest", show_header=True, header_style="bold cyan")
    table.add_column("Chỉ số", style="dim")
    table.add_column("Giá trị", justify="right")
    for key, value in results.items():
        table.add_row(str(key), str(value))
    console.print(table)


def print_benchmark_progress_header(
    *,
    symbol: str,
    tf: str,
    label: str,
    backends: Sequence[str],
    n_trials: int,
    n_splits: int,
) -> None:
    """Render the benchmark section header before backend execution."""
    console.rule(f"[bold cyan]MLFX Benchmark — {symbol} {tf} {label}[/]")
    console.print(f"Backends: {', '.join(backends)}  |  n_trials={n_trials}  n_splits={n_splits}\n")


def print_benchmark_results_table(
    *,
    symbol: str,
    tf: str,
    label: str,
    results: Sequence[Mapping[str, Any]],
) -> None:
    """Render the final benchmark comparison table."""
    console.print()
    table = Table(
        title=f"Benchmark Results — {symbol} {tf} {label}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Backend", style="bold")
    table.add_column("CV F1 (macro)", justify="right")
    table.add_column("Train F1", justify="right")
    table.add_column("Accuracy", justify="right")
    table.add_column("Time (s)", justify="right")
    table.add_column("Status")

    for row in results:
        status = str(row.get("status", ""))
        status_style = "green" if status == "OK" else "red"
        table.add_row(
            str(row.get("backend", "-")),
            str(row.get("cv_f1_macro", "-")),
            str(row.get("train_f1", "-")),
            str(row.get("accuracy", "-")),
            str(row.get("elapsed_s", "-")),
            f"[{status_style}]{status}[/]",
        )
    console.print(table)
