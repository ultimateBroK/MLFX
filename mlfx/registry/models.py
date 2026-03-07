"""Lightweight JSON-backed model registry.

The registry file lives at ``outputs/models/registry.json`` by default.
Each entry records the backend, symbol, timeframe, label column, trained
artifact path, key metrics, and a timestamp.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from mlfx.config.paths import DEFAULT_PATHS

logger = logging.getLogger(__name__)

_REGISTRY_FILENAME = "registry.json"


class ModelRegistry:
    """Append-only model registry backed by a JSON file.

    Parameters
    ----------
    registry_path:
        Full path to the registry JSON file.
    """

    def __init__(self, registry_path: Path | None = None) -> None:
        self._path = registry_path or (DEFAULT_PATHS.models_root / _REGISTRY_FILENAME)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _load(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        try:
            return json.loads(self._path.read_text())
        except (json.JSONDecodeError, OSError):
            logger.warning("Registry file corrupt or unreadable; starting fresh.")
            return []

    def _save(self, entries: list[dict[str, Any]]) -> None:
        self._path.write_text(json.dumps(entries, indent=2, default=str))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(
        self,
        backend: str,
        symbol: str,
        tf: str,
        label_col: str,
        metrics: dict[str, Any],
        *,
        artifact_path: str | Path | None = None,
        tags: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Append a new entry to the registry and persist it.

        Parameters
        ----------
        backend, symbol, tf, label_col:
            Identifiers for the trained model.
        metrics:
            Raw metrics dict returned by the backend ``run_*`` function.
        artifact_path:
            Path to the saved model file.  Inferred from *metrics* if omitted.
        tags:
            Optional free-form metadata labels.

        Returns
        -------
        dict
            The newly created registry entry.
        """
        entry: dict[str, Any] = {
            "backend": backend,
            "symbol": symbol,
            "tf": tf,
            "label_col": label_col,
            "registered_at": time.time(),
            "metrics": {
                k: v
                for k, v in metrics.items()
                if isinstance(v, (int, float))
            },
            "feature_columns": [
                column
                for column in metrics.get("selected_features", [])
                if isinstance(column, str)
            ],
            "artifact_path": str(artifact_path or metrics.get("artifact_path", "")),
            "tags": tags or {},
        }
        entries = self._load()
        entries.append(entry)
        self._save(entries)
        logger.info(
            "Registry: registered %s  %s/%s  %s  metrics=%s",
            backend, symbol, tf, label_col,
            entry["metrics"],
        )
        return entry

    def list_models(
        self,
        *,
        symbol: str | None = None,
        tf: str | None = None,
        backend: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return all entries, optionally filtered."""
        entries = self._load()
        if symbol:
            entries = [e for e in entries if e.get("symbol") == symbol]
        if tf:
            entries = [e for e in entries if e.get("tf") == tf]
        if backend:
            entries = [e for e in entries if e.get("backend") == backend]
        return entries

    def best_model(
        self,
        *,
        symbol: str,
        tf: str,
        label_col: str | None = None,
        metric: str = "best_cv_f1_macro",
        backend: str | None = None,
    ) -> dict[str, Any] | None:
        """Return the entry with the highest value of *metric*.

        Returns ``None`` when no matching entry is found.
        """
        candidates = self.list_models(symbol=symbol, tf=tf, backend=backend)
        if label_col:
            candidates = [e for e in candidates if e.get("label_col") == label_col]
        valid = [
            e for e in candidates if metric in e.get("metrics", {})
        ]
        if not valid:
            return None
        return max(valid, key=lambda e: e["metrics"][metric])


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_registry: ModelRegistry | None = None


def get_registry(registry_path: Path | None = None) -> ModelRegistry:
    """Return the process-level registry singleton."""
    global _registry
    if _registry is None or registry_path is not None:
        _registry = ModelRegistry(registry_path)
    return _registry
