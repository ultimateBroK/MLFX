"""
models/neural_forecast.py
=========================
Nixtla NeuralForecast (N-HiTS + N-BEATS) for XAUUSD direction prediction.

Uses the Nixtla `neuralforecast` library — part of the Nixtla ecosystem —
with N-HiTS as the primary model and N-BEATS as the secondary.

Approach:
    - Label column is remapped to {0, 1, 2, 3, 4} (continuous target y).
    - NHiTS / NBEATS are trained to forecast h=1 step ahead.
    - Predictions are rounded & clipped to integer classes for F1 evaluation.
    - Walk-forward cross-validation via neuralforecast's built-in method.

Output: outputs/models/{symbol}/{tf}/neural_forecast_{label_col}.pkl
        outputs/models/{symbol}/{tf}/neural_forecast_{label_col}.metrics.json
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path

import numpy as np
import polars as pl
from neuralforecast import NeuralForecast
from neuralforecast.models import NBEATS, NHITS
from sklearn.metrics import f1_score

logger = logging.getLogger(__name__)

LABELS_DIR = Path("data/labels")
SAVED_DIR = Path("outputs/models")

# Timeframe → Pandas frequency string
_TF_FREQ: dict[str, str] = {
    "1m":  "1min",
    "5m":  "5min",
    "15m": "15min",
    "30m": "30min",
    "1H":  "h",
    "2H":  "2h",
    "4H":  "4h",
    "1D":  "D",
}


def prepare_nixtla_df(df: pl.DataFrame, label_col: str) -> pl.DataFrame:
    """Format Polars DataFrame for Nixtla NeuralForecast (unique_id, ds, y)."""
    subset = df.select(["timestamp", label_col]).drop_nulls()
    return subset.with_columns(
        [
            pl.lit("XAUUSD").alias("unique_id"),
            pl.col("timestamp").alias("ds"),
            # Map {-2,-1,0,1,2} → {0,1,2,3,4} as float regression target
            (pl.col(label_col) + 2).cast(pl.Float64).alias("y"),
        ]
    ).select(["unique_id", "ds", "y"])


def train_neural_forecast(
    df_nixtla: pl.DataFrame,
    n_windows: int = 5,
    freq: str = "h",
    input_size: int = 48,
    max_steps: int = 200,
) -> tuple[NeuralForecast, dict]:
    """
    Train NHiTS + NBEATS with walk-forward cross-validation.

    Args:
        df_nixtla:   DataFrame in (unique_id, ds, y) format.
        n_windows:   Number of CV windows for neuralforecast cross_validation().
        freq:        Pandas frequency string matching the data timeframe.
        input_size:  Number of lagged steps fed into the model.
        max_steps:   Maximum gradient-descent steps per model.

    Returns:
        Fitted NeuralForecast object and metrics dict.
    """
    models = [
        NHITS(
            h=1,
            input_size=input_size,
            max_steps=max_steps,
            scaler_type="standard",
            early_stop_patience_steps=-1,
        ),
        NBEATS(
            h=1,
            input_size=input_size,
            max_steps=max_steps,
            stack_types=["identity", "identity"],
            scaler_type="standard",
            early_stop_patience_steps=-1,
        ),
    ]

    nf = NeuralForecast(models=models, freq=freq)
    df_pd = df_nixtla.to_pandas()

    # Walk-forward CV: step_size = ~10% of total rows
    step_size = max(1, len(df_pd) // (n_windows * 10))
    logger.info(
        "NeuralForecast CV: n_windows=%d  step_size=%d  input_size=%d  max_steps=%d",
        n_windows,
        step_size,
        input_size,
        max_steps,
    )

    cv_df = nf.cross_validation(df_pd, n_windows=n_windows, step_size=step_size)

    # Compute F1 macro per model column
    y_true = np.clip(np.round(cv_df["y"].to_numpy()).astype(int), 0, 4)
    scores: dict[str, float] = {}
    for col in ["NHITS", "NBEATS"]:
        if col in cv_df.columns:
            y_pred = np.clip(np.round(cv_df[col].to_numpy()).astype(int), 0, 4)
            scores[col] = float(
                f1_score(y_true, y_pred, average="macro", zero_division=0)
            )

    logger.info("NeuralForecast CV F1: %s", scores)

    # Fit final model on all data
    nf.fit(df_pd)

    metrics = {
        "cv_f1_macro": scores,
        "n_samples": len(df_pd),
        "model_type": "NeuralForecast_NHiTS_NBEATS",
        "input_size": input_size,
        "max_steps": max_steps,
        "n_windows": n_windows,
    }
    return nf, metrics


def save_model(nf: NeuralForecast, metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(nf, f)
    metrics_path = path.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2, default=str))
    logger.info("✓ NeuralForecast model saved → %s", path)


def run_neural_forecast(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label_col: str = "label_10",
    n_windows: int = 5,
    input_size: int = 48,
    max_steps: int = 200,
    force: bool = False,
) -> dict:
    """
    Entry point: load labels → train NeuralForecast → save model.

    Args:
        symbol:     Trading pair (default "XAUUSD").
        tf:         Timeframe key (default "1H").
        label_col:  Label column to train on (default "label_10").
        n_windows:  Walk-forward CV windows.
        input_size: Lagged context steps for NHiTS/NBEATS.
        max_steps:  Training gradient steps per model.
        force:      Overwrite existing model.

    Returns:
        Metrics dict or empty dict if skipped/no data.
    """
    in_dir = LABELS_DIR / symbol / tf
    out_dir = SAVED_DIR / symbol / tf
    out_path = out_dir / f"neural_forecast_{label_col}.pkl"

    if out_path.exists() and not force:
        logger.info("NeuralForecast model exists at %s", out_path)
        return {}

    parquet_files = sorted(in_dir.glob("*.parquet")) if in_dir.exists() else []
    if not parquet_files:
        logger.warning("No label files found in %s", in_dir)
        return {}

    df = pl.concat([pl.read_parquet(f) for f in parquet_files]).sort("timestamp")
    if label_col not in df.columns:
        logger.error("Column '%s' not found in data", label_col)
        return {}

    freq = _TF_FREQ.get(tf, "h")
    # Limit to last 5000 rows for tractable training
    df_nixtla = prepare_nixtla_df(df, label_col).tail(5000)

    nf, metrics = train_neural_forecast(
        df_nixtla,
        n_windows=n_windows,
        freq=freq,
        input_size=input_size,
        max_steps=max_steps,
    )
    save_model(nf, metrics, out_path)
    return metrics


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Train NeuralForecast (N-HiTS + N-BEATS)")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--n-windows", type=int, default=5)
    parser.add_argument("--input-size", type=int, default=48)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    run_neural_forecast(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        n_windows=args.n_windows,
        input_size=args.input_size,
        max_steps=args.max_steps,
        force=args.force,
    )
