"""CLI command handlers for MLFX.

This package contains individual command handlers that are dispatched
from the main CLI entrypoint.
"""

from .download import handle_download
from .pipeline import handle_pipeline
from .qa import handle_qa
from .train import handle_train
from .evaluate import handle_evaluate
from .serve import handle_serve
from .batch import handle_batch
from .drift import handle_drift, handle_drift_retrain
from .models import handle_models
from .profiles import handle_profiles
from .run_profile import handle_run_profile
from .run_all import handle_run_all
from .benchmark import handle_benchmark
from .mlflow import handle_mlflow

__all__ = [
    "handle_download",
    "handle_pipeline",
    "handle_qa",
    "handle_train",
    "handle_evaluate",
    "handle_serve",
    "handle_batch",
    "handle_drift",
    "handle_drift_retrain",
    "handle_models",
    "handle_profiles",
    "handle_run_profile",
    "handle_run_all",
    "handle_benchmark",
    "handle_mlflow",
]
