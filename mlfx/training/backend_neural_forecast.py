"""
Package-native NeuralForecast backend.
"""

from __future__ import annotations

import argparse
import logging

import numpy as np
import polars as pl
from neuralforecast import NeuralForecast
from neuralforecast.models import NBEATS, NHITS
from sklearn.metrics import f1_score

from mlfx.training.dataset import build_model_output_path, load_labelled_dataset
from mlfx.training.persistence import save_pickle_artifact

logger = logging.getLogger(__name__)

# Timeframe -> Pandas frequency string.
_TF_FREQ: dict[str, str] = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1H": "h",
    "2H": "2h",
    "4H": "4h",
    "1D": "D",
}


def prepare_nixtla_df(df: pl.DataFrame, label_col: str) -> pl.DataFrame:
    """Format Polars dataframe for Nixtla NeuralForecast (unique_id, ds, y)."""
    subset = df.select(["timestamp", label_col]).drop_nulls()
    return subset.with_columns(
        [
            pl.lit("XAUUSD").alias("unique_id"),
            pl.col("timestamp").alias("ds"),
            # Map {-2,-1,0,1,2} -> {0,1,2,3,4} as a float regression target.
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
    """Train N-HiTS + N-BEATS with walk-forward cross-validation."""
    models = [
        NHITS(
            h=1,
            input_size=input_size,
            max_steps=max_steps,
            scaler_type="standard",
            early_stop_patience_steps=-1,
            logger=False,
            enable_checkpointing=False,
            enable_progress_bar=False,
        ),
        NBEATS(
            h=1,
            input_size=input_size,
            max_steps=max_steps,
            stack_types=["identity", "identity"],
            scaler_type="standard",
            early_stop_patience_steps=-1,
            logger=False,
            enable_checkpointing=False,
            enable_progress_bar=False,
        ),
    ]

    nf = NeuralForecast(models=models, freq=freq)
    df_pd = df_nixtla.to_pandas()

    step_size = max(1, len(df_pd) // (n_windows * 10))
    logger.info(
        "NeuralForecast CV: n_windows=%d  step_size=%d  input_size=%d  max_steps=%d",
        n_windows,
        step_size,
        input_size,
        max_steps,
    )

    cv_df = nf.cross_validation(df_pd, n_windows=n_windows, step_size=step_size)

    y_true = np.clip(np.round(cv_df["y"].to_numpy()).astype(int), 0, 4)
    scores: dict[str, float] = {}
    for col in ["NHITS", "NBEATS"]:
        if col in cv_df.columns:
            y_pred = np.clip(np.round(cv_df[col].to_numpy()).astype(int), 0, 4)
            scores[col] = float(
                f1_score(y_true, y_pred, average="macro", zero_division=0)
            )

    logger.info("NeuralForecast CV F1: %s", scores)

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


def save_model(nf: NeuralForecast, metrics: dict, path) -> None:
    save_pickle_artifact(nf, metrics, path)
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
    """Entry point: load labels, train NeuralForecast, and save the model."""
    out_path = build_model_output_path(
        f"neural_forecast_{label_col}",
        symbol,
        tf,
        suffix=".pkl",
    )

    if out_path.exists() and not force:
        logger.info("NeuralForecast model exists at %s", out_path)
        return {}

    df = load_labelled_dataset(symbol, tf)
    if df is None:
        logger.warning("No label files found for %s %s", symbol, tf)
        return {}
    if label_col not in df.columns:
        logger.error("Column '%s' not found in data", label_col)
        return {}

    freq = _TF_FREQ.get(tf, "h")
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train NeuralForecast (N-HiTS + N-BEATS)")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--n-windows", type=int, default=5)
    parser.add_argument("--input-size", type=int, default=48)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args()
    run_neural_forecast(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        n_windows=args.n_windows,
        input_size=args.input_size,
        max_steps=args.max_steps,
        force=args.force,
    )


if __name__ == "__main__":
    main()
