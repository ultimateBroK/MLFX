"""Training helpers, backend registry, and high-level orchestration."""

from .config import BackendRunner, TrainingConfig, TrainResult
from .data import build_model_output_path, load_labelled_dataset
from .feature_selection import DEFAULT_FEATURE_BLACKLIST, select_numeric_feature_columns
from .artifacts import save_pickle_artifact, save_torch_artifact, write_metrics_json
from .registry import BACKEND_REGISTRY, get_backend_runner
from .runner import run_training

__all__ = [
    "BACKEND_REGISTRY",
    "BackendRunner",
    "DEFAULT_FEATURE_BLACKLIST",
    "TrainResult",
    "TrainingConfig",
    "build_model_output_path",
    "get_backend_runner",
    "load_labelled_dataset",
    "run_training",
    "save_pickle_artifact",
    "save_torch_artifact",
    "select_numeric_feature_columns",
    "write_metrics_json",
]
