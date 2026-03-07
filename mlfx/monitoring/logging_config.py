"""Structured JSON logging setup.

Call :func:`configure_logging` once at application start-up (e.g. in
``mlfx/app/cli.py``) to redirect all Python logging to structured JSON lines.

Each log record emits a JSON object with at minimum:
    ``timestamp``, ``level``, ``logger``, ``message``

Extra context fields (symbol, tf, backend, run_id, …) can be injected via
:func:`add_context` which returns a context-manager.

Usage::

    from mlfx.monitoring.logging_config import configure_logging, add_context

    configure_logging(level="INFO")

    with add_context(symbol="XAUUSD", tf="1H"):
        logger.info("Feature pipeline started")
        # → {"timestamp": "...", "level": "INFO", "logger": "...",
        #    "message": "Feature pipeline started",
        #    "symbol": "XAUUSD", "tf": "1H"}
"""

from __future__ import annotations

import json
import logging
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Generator

_context: ContextVar[dict[str, Any]] = ContextVar("_log_ctx", default={})


class _JsonFormatter(logging.Formatter):
    """Convert a log record to a single-line JSON string."""

    def format(self, record: logging.LogRecord) -> str:
        ctx = _context.get({})
        payload: dict[str, Any] = {
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        payload.update(ctx)
        return json.dumps(payload, default=str)


def configure_logging(
    level: str | int = "INFO",
    *,
    stream: Any = None,
) -> None:
    """Replace the root-logger handler with a JSON formatter.

    Parameters
    ----------
    level:
        Logging level string (``"DEBUG"``, ``"INFO"``, etc.) or int.
    stream:
        Target stream.  Defaults to ``sys.stdout``.
    """
    root = logging.getLogger()
    root.setLevel(level)

    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)


@contextmanager
def add_context(**kwargs: Any) -> Generator[None, None, None]:
    """Temporarily add key-value pairs to every log record in this context.

    Values persist for the duration of the ``with`` block and are cleaned up
    automatically.
    """
    existing = dict(_context.get({}))
    token = _context.set({**existing, **kwargs})
    try:
        yield
    finally:
        _context.reset(token)
