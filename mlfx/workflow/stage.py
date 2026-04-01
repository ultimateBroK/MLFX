"""Short alias module for stage entrypoints.

Existing code should continue importing from mlfx.workflow.stages. This alias
provides a concise path for newer internal code.
"""

from .stages import (
    run_batch,
    run_download,
    run_drift,
    run_drift_then_retrain,
    run_evaluate,
    run_pipeline_stage,
    run_qa,
    run_train,
)

__all__ = [
    "run_batch",
    "run_download",
    "run_drift",
    "run_drift_then_retrain",
    "run_evaluate",
    "run_pipeline_stage",
    "run_qa",
    "run_train",
]
