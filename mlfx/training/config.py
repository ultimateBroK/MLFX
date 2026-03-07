"""Public re-export of training configuration types.

Consumers should import from here rather than from the internal
``backends.base`` sub-module.
"""

from mlfx.training.backends.base import BackendRunner, TrainingConfig, TrainResult

__all__ = ["BackendRunner", "TrainingConfig", "TrainResult"]
