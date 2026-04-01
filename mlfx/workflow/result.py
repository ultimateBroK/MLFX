"""Short alias module for workflow result contracts and persistence."""

from .results import StageResult, StageStatus, WorkflowResult, persist_workflow_result

__all__ = [
    "StageResult",
    "StageStatus",
    "WorkflowResult",
    "persist_workflow_result",
]
