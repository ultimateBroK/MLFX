"""MLflow command handler."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys

from ..render import console

logger = logging.getLogger(__name__)


def handle_mlflow(args: argparse.Namespace) -> None:
    """Handle the mlflow command."""
    if args.mlflow_command == "ui":
        _run_mlflow_ui(args)
    elif args.mlflow_command == "migrate":
        _run_mlflow_migrate(args)


def _run_mlflow_ui(args: argparse.Namespace) -> None:
    """Launch MLflow tracking UI."""
    try:
        import mlflow  # type: ignore[import-not-found]  # noqa: PLC0415
    except ImportError:
        logging.getLogger(__name__).error(
            "MLflow not installed. Run: pixi add mlflow"
        )
        return

    from mlfx.config.mlflow import MLflowConfig

    config = MLflowConfig()
    
    # Use resolved properties which have defaults
    backend_store_uri = args.backend_store_uri or config.resolved_tracking_uri
    artifact_root = args.default_artifact_root or str(config.resolved_artifact_root)

    console.print("[bold cyan]Starting MLflow UI...[/]")
    console.print(f"Backend store: {backend_store_uri}")
    console.print(f"Artifact root: {artifact_root}")
    console.print(f"URL: http://{args.host}:{args.port}")

    cmd = [
        sys.executable,
        "-m",
        "mlflow",
        "server",
        "--backend-store-uri",
        backend_store_uri,
        "--default-artifact-root",
        artifact_root,
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--serve-artifacts",
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]MLflow UI stopped.[/]")


def _run_mlflow_migrate(args: argparse.Namespace) -> None:
    """Migrate existing artifacts to MLflow."""
    try:
        import mlflow  # type: ignore[import-not-found]  # noqa: PLC0415
    except ImportError:
        logging.getLogger(__name__).error(
            "MLflow not installed. Run: pixi add mlflow"
        )
        return

    from mlfx.config.mlflow import MLflowConfig
    from mlfx.config.paths import DEFAULT_PATHS
    from mlfx.registry import get_registry

    config = MLflowConfig()
    config.setup_mlflow()

    console.print("[bold cyan]Migrating artifacts to MLflow...[/]")

    # Get existing models from JSON registry
    json_registry = get_registry(use_mlflow=False)
    entries = json_registry.list_models(
        symbol=args.symbol,
        tf=args.tf,
        backend=args.backend,
    )

    if not entries:
        console.print("[yellow]No models found to migrate.[/yellow]")
        return

    console.print(f"Found {len(entries)} models to migrate")

    if args.dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/]")
        for entry in entries:
            console.print(
                f"  Would migrate: {entry.get('symbol')}/{entry.get('tf')}/"
                f"{entry.get('backend')} - {entry.get('run_id', 'N/A')}"
            )
        return

    # Get MLflow registry for registration
    mlflow_registry = get_registry(use_mlflow=True)
    migrated = 0
    errors = 0

    for entry in entries:
        symbol = entry.get("symbol")
        tf = entry.get("tf")
        backend = entry.get("backend")
        run_id = entry.get("run_id", "unknown")
        accuracy = entry.get("accuracy")

        try:
            with console.status(f"[bold green]Migrating {symbol}/{tf}/{backend}..."):
                # Create experiment and run
                experiment_name = config.experiment_name(symbol, tf, backend)
                mlflow.set_experiment(experiment_name)

                with mlflow.start_run(run_name=f"migrated_{run_id}") as run:
                    # Log metadata
                    mlflow.log_param("symbol", symbol)
                    mlflow.log_param("tf", tf)
                    mlflow.log_param("backend", backend)
                    mlflow.log_param("migrated_from", run_id)

                    if accuracy is not None:
                        mlflow.log_metric("accuracy", accuracy)

                    # Log model artifact
                    model_path = DEFAULT_PATHS.model_path(
                        symbol=symbol,
                        tf=tf,
                        label="label_5",  # Default label
                        backend=backend,
                    )

                    if model_path.exists():
                        mlflow.log_artifact(str(model_path), artifact_path="model")
                        artifact_uri = mlflow.get_artifact_uri("model")

                        # Register model
                        if args.register_models:
                            model_name = config.model_name(symbol, tf, backend)
                            mlflow.register_model(
                                model_uri=artifact_uri,
                                name=model_name,
                            )

                    mlflow.end_run()

            migrated += 1
            console.print(f"  [green]✓[/] Migrated: {symbol}/{tf}/{backend}")

        except Exception as exc:  # noqa: BLE001
            errors += 1
            console.print(f"  [red]✗[/] Failed: {symbol}/{tf}/{backend} - {exc}")

    console.print()
    console.print(f"[bold]Migration complete:[/] {migrated} migrated, {errors} errors")
