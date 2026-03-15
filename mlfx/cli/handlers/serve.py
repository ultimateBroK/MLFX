"""Serve command handler."""

from __future__ import annotations

import argparse
import logging

from ..render import console
from ..resolve import resolve_serve_config

logger = logging.getLogger(__name__)


def handle_serve(args: argparse.Namespace) -> None:
    """Handle the serve command."""
    serve_cfg = resolve_serve_config(args)
    try:
        import uvicorn  # type: ignore[import-not-found]  # noqa: PLC0415
    except ImportError:
        logging.getLogger(__name__).error(
            "uvicorn not installed. Run: pip install fastapi uvicorn"
        )
        return
    uvicorn.run(
        "mlfx.serving.api:app",
        host=serve_cfg["host"],
        port=serve_cfg["port"],
        reload=serve_cfg["reload"],
    )
