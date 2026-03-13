"""Model registry for tracking trained artifact versions.

Provides a lightweight JSON-backed registry that records every trained model
artifact together with its key metrics so you can retrieve the *best* model
for a given symbol / timeframe combination.

Usage::

    from mlfx.registry import get_registry

    reg = get_registry()
    reg.register(backend="mlf", symbol="XAUUSD", tf="1H",
                 label="label_10", metrics={"best_cv_f1_macro": 0.62})
    best = reg.best_model(symbol="XAUUSD", tf="1H", metric="best_cv_f1_macro")
"""

from .models import ModelRegistry, get_registry, reset_registry

__all__ = ["ModelRegistry", "get_registry", "reset_registry"]
