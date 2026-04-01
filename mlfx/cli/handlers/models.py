"""Models command handler."""

from __future__ import annotations

import argparse
import logging

from ..render import console

logger = logging.getLogger(__name__)


def handle_models(args: argparse.Namespace) -> None:
    """Handle the models command."""
    from mlfx.registry.models import get_registry  # noqa: PLC0415

    with console.status("[bold green]Fetching models..."):
        reg = get_registry()
        entries = reg.list_models(
            symbol=args.symbol,
            tf=args.tf,
            backend=args.backend,
        )

    if not entries:
        console.print("[yellow]No models found in the registry.[/yellow]")
        return

    from rich.table import Table  # type: ignore[import-not-found]

    table = Table(title="Registered Model Versions", show_header=True, header_style="bold magenta")

    keys: list[str] = []
    for entry in entries:
        for key in entry.keys():
            if key not in keys:
                keys.append(key)

    std_columns = ["symbol", "tf", "backend", "run_id", "accuracy"]
    ordered_keys = [key for key in std_columns if key in keys] + [
        key for key in keys if key not in std_columns
    ]

    for key in ordered_keys:
        table.add_column(str(key))

    for entry in entries:
        row = [str(entry.get(key, "")) for key in ordered_keys]
        table.add_row(*row)

    console.print(table)
