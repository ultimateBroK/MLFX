"""Shared stage/workflow result contracts and persistence helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths

StageStatus = Literal["ok", "error", "skipped"]


@dataclass(slots=True)
class StageResult:
    """Canonical result payload returned by stage entrypoints."""

    stage: str
    status: StageStatus
    metrics: dict[str, Any] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    symbol: str | None = None
    tf: str | None = None
    label: str | None = None
    error: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    ended_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema"] = "mlfx.stage_result.v1"
        return payload


@dataclass(slots=True)
class WorkflowResult:
    """Canonical result payload for multi-stage workflows."""

    workflow: str
    stages: list[StageResult]
    invocation_id: str = field(default_factory=lambda: uuid4().hex[:12])
    status: StageStatus = "ok"
    params: dict[str, Any] = field(default_factory=dict)
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    ended_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "mlfx.workflow_result.v1",
            "workflow": self.workflow,
            "invocation_id": self.invocation_id,
            "status": self.status,
            "params": self.params,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "elapsed_seconds": self.elapsed_seconds,
            "stages": [stage.to_dict() for stage in self.stages],
        }


def persist_workflow_result(
    result: WorkflowResult,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> Path:
    """Persist one workflow invocation summary under outputs/runs/workflows/."""

    out_dir = paths.runs_root / "workflows"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{stamp}_{result.workflow}_{result.invocation_id}.json"
    out_path.write_text(json.dumps(result.to_dict(), indent=2, default=str))
    return out_path
