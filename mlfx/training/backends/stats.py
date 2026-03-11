"""
Package-native StatsForecast baseline backend.
"""

from __future__ import annotations

import argparse
import logging

import numpy as np
import polars as pl
from sklearn.metrics import f1_score
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, MSTL, SeasonalNaive

from mlfx.training.data import build_model_output_path, load_labelled_dataset
from mlfx.training.artifacts import save_pickle_artifact
from mlfx.training._utils import set_seed

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


def prepare_nixtla_df(df: pl.DataFrame, label_col: str, symbol: str = "XAUUSD") -> tuple[pl.DataFrame, list[str]]:
    """Format dataframe for Nixtla StatsForecast (unique_id, ds, y).

    Returns (df, feature_cols). StatsForecast uses only unique_id, ds, y;
    feature_cols is empty for API consistency with MLForecast.
    """
    subset = df.select(["timestamp", label_col]).drop_nulls()
    unique_id_col = pl.lit(symbol).alias("unique_id")
    ds_col = pl.col("timestamp").alias("ds")

    # Map labels {-2, -1, 0, 1, 2} to {0, 1, 2, 3, 4}.
    y_col = (pl.col(label_col) + 2).cast(pl.Float64).alias("y")

    subset = subset.with_columns([unique_id_col, ds_col, y_col])
    return subset.select(["unique_id", "ds", "y"]), []


def train_stats_baseline(
    df_nixtla: pl.DataFrame,
    n_splits: int = 5,
    season_length: int = 24,
    freq: str = "h",
) -> tuple[StatsForecast, dict]:
    models = [
        AutoARIMA(season_length=season_length),
        SeasonalNaive(season_length=season_length),
        MSTL(season_length=season_length),
    ]

    sf = StatsForecast(
        models=models,
        freq=freq,
        n_jobs=-1,
    )

    df_pd = df_nixtla.to_pandas()

    from sklearn.model_selection import TimeSeriesSplit

    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = {"AutoARIMA": [], "SeasonalNaive": [], "MSTL": []}

    for train_idx, val_idx in tscv.split(df_pd):
        df_tr = df_pd.iloc[train_idx]
        df_val = df_pd.iloc[val_idx]

        sf.fit(df_tr)
        preds = sf.predict(h=len(df_val))
        y_test = df_val["y"].values

        pred_arima = np.clip(np.round(preds["AutoARIMA"].values), 0, 4).astype(int)
        pred_snaive = np.clip(np.round(preds["SeasonalNaive"].values), 0, 4).astype(int)
        pred_mstl = np.clip(np.round(preds["MSTL"].values), 0, 4).astype(int)

        scores["AutoARIMA"].append(
            f1_score(y_test, pred_arima, average="macro", zero_division=0)
        )
        scores["SeasonalNaive"].append(
            f1_score(y_test, pred_snaive, average="macro", zero_division=0)
        )
        scores["MSTL"].append(
            f1_score(y_test, pred_mstl, average="macro", zero_division=0)
        )

    avg_scores = {key: float(np.mean(value)) for key, value in scores.items()}
    best_cv_f1_macro = float(max(avg_scores.values())) if avg_scores else 0.0
    logger.info("Baseline Cross-Validation F1: %s", avg_scores)

    sf.fit(df_pd)
    metrics = {
        "cv_f1_macro": avg_scores,
        "best_cv_f1_macro": best_cv_f1_macro,
        "n_samples": len(df_pd),
        "model_type": "StatsForecast_Baseline",
    }
    return sf, metrics


def save_model(sf: StatsForecast, metrics: dict, path) -> None:
    """Persist StatsForecast model to .pkl artifact for serving."""
    save_pickle_artifact(sf, metrics, path)
    logger.info("✓ StatsForecast baseline saved → %s", path)


def run_stats(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label_col: str = "label_10",
    n_splits: int = 5,
    season_length: int = 24,
    force: bool = False,
    seed: int = 42,
) -> dict:
    """Train StatsForecast baseline (AutoARIMA, SeasonalNaive, MSTL). Returns metrics dict or {} if skipped."""
    set_seed(seed)
    out_path = build_model_output_path(
        f"stats_baseline_{label_col}",
        symbol,
        tf,
        suffix=".pkl",
    )

    if out_path.exists() and not force:
        logger.info("StatsForecast baseline exists at %s", out_path)
        return {}

    df = load_labelled_dataset(symbol, tf)
    if df is None or label_col not in df.columns:
        return {}

    df_nixtla, _ = prepare_nixtla_df(df, label_col, symbol=symbol)
    df_nixtla = df_nixtla.tail(5000)
    freq = _TF_FREQ.get(tf, "h")
    sf, metrics = train_stats_baseline(df_nixtla, n_splits=n_splits, season_length=season_length, freq=freq)
    save_model(sf, metrics, out_path)
    metrics["artifact_path"] = str(out_path)
    return metrics


def build_parser() -> argparse.ArgumentParser:
    """Build argparse for standalone StatsForecast training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    """CLI entrypoint for standalone StatsForecast training."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args()
    run_stats(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        n_splits=args.n_splits,
        force=args.force,
    )


if __name__ == "__main__":
    main()
