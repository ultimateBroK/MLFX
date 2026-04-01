"""Shared training utilities: reproducibility helpers."""
from __future__ import annotations

import os
import random

import numpy as np
import torch


def set_seed(seed: int) -> None:
    """Set all RNG seeds for reproducible training.

    Args:
        seed: Integer seed value to use for all RNG libraries.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
