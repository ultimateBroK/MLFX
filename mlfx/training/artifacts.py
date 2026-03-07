"""Shared persistence helpers for training backends."""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import torch


def ensure_parent_dir(path: Path) -> None:
    """Create the parent directory for an artifact path."""
    path.parent.mkdir(parents=True, exist_ok=True)


def write_metrics_json(metrics: dict[str, Any], metrics_path: Path) -> None:
    """Persist metrics as JSON, creating parent directories if needed."""
    ensure_parent_dir(metrics_path)
    metrics_path.write_text(json.dumps(metrics, indent=2, default=str))


def save_pickle_artifact(payload: Any, metrics: dict[str, Any], path: Path) -> None:
    """Save a pickle artifact and its sidecar metrics JSON."""
    ensure_parent_dir(path)
    with open(path, "wb") as file_handle:
        pickle.dump(payload, file_handle)
    write_metrics_json(metrics, path.with_suffix(".metrics.json"))


def save_torch_artifact(
    payload: dict[str, Any],
    metrics: dict[str, Any],
    path: Path,
    *,
    history_key: str = "history",
) -> None:
    """Save a torch payload and a condensed metrics sidecar."""
    ensure_parent_dir(path)
    torch.save(payload, path)
    safe_metrics = {key: value for key, value in metrics.items() if key != history_key}
    if history_key in metrics:
        safe_metrics[f"{history_key}_tail"] = metrics.get(history_key, [])[-5:]
    write_metrics_json(safe_metrics, path.with_suffix(".metrics.json"))
