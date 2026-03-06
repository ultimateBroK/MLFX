"""
models/stats_baseline.py
========================
Replaces prophet_alt.py using Nixtla's statsforecast.
Provides AutoARIMA and SeasonalNaive models as univariates baseline.

Output: outputs/models/{symbol}/{tf}/stats_baseline_{label_col}.pkl
"""

import json
import logging
import pickle
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.metrics import f1_score
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, SeasonalNaive, MSTL

logger = logging.getLogger(__name__)

LABELS_DIR = Path("data/labels")
SAVED_DIR = Path("outputs/models")

def prepare_nixtla_df(df: pl.DataFrame, label_col: str) -> pl.DataFrame:
    """Format dataframe for Nixtla StatsForecast (unique_id, ds, y)."""
    subset = df.select(["timestamp", label_col]).drop_nulls()
    unique_id_col = pl.lit("XAUUSD").alias("unique_id")
    ds_col = pl.col("timestamp").alias("ds")
    
    # Map labels {-2, -1, 0, 1, 2} to {0, 1, 2, 3, 4}
    y_col = (pl.col(label_col) + 2).cast(pl.Float64).alias("y")
    
    subset = subset.with_columns([unique_id_col, ds_col, y_col])
    return subset.select(["unique_id", "ds", "y"])

def train_stats_baseline(df_nixtla: pl.DataFrame, n_splits: int = 5) -> tuple[StatsForecast, dict]:
    # MSTL / AutoARIMA / SeasonalNaive for building baselines
    models = [
        AutoARIMA(season_length=24),
        SeasonalNaive(season_length=24),
        MSTL(season_length=24)
    ]
    
    sf = StatsForecast(
        models=models,
        freq='1h',
        n_jobs=-1
    )
    
    # Cross-validation
    df_pd = df_nixtla.to_pandas()
    from sklearn.model_selection import TimeSeriesSplit
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    scores = {"AutoARIMA": [], "SeasonalNaive": [], "MSTL": []}
    
    for train_idx, val_idx in tscv.split(df_pd):
        df_tr = df_pd.iloc[train_idx]
        df_val = df_pd.iloc[val_idx]
        
        sf.fit(df_tr)
        h = len(df_val)
        preds = sf.predict(h=h)
        
        y_test = df_val['y'].values
        
        pred_arima = np.clip(np.round(preds['AutoARIMA'].values), 0, 4).astype(int)
        pred_snaive = np.clip(np.round(preds['SeasonalNaive'].values), 0, 4).astype(int)
        pred_mstl = np.clip(np.round(preds['MSTL'].values), 0, 4).astype(int)
        
        scores["AutoARIMA"].append(f1_score(y_test, pred_arima, average="macro", zero_division=0))
        scores["SeasonalNaive"].append(f1_score(y_test, pred_snaive, average="macro", zero_division=0))
        scores["MSTL"].append(f1_score(y_test, pred_mstl, average="macro", zero_division=0))
        
    avg_scores = {k: float(np.mean(v)) for k,v in scores.items()}
    logger.info("Baseline Cross-Validation F1: %s", avg_scores)
    
    # Fit on all data
    sf.fit(df_pd)
    metrics = {
        "cv_f1_macro": avg_scores,
        "n_samples": len(df_pd),
        "model_type": "StatsForecast_Baseline"
    }
    return sf, metrics

def save_model(sf: StatsForecast, metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(sf, f)
    metrics_path = path.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2, default=str))
    logger.info("✓ StatsForecast baseline saved → %s", path)

def run_stats(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label_col: str = "label_10",
    n_splits: int = 5,
    force: bool = False,
) -> dict:
    in_dir = LABELS_DIR / symbol / tf
    out_dir = SAVED_DIR / symbol / tf
    out_path = out_dir / f"stats_baseline_{label_col}.pkl"

    if out_path.exists() and not force:
        logger.info("StatsForecast baseline exists at %s", out_path)
        return {}

    parquet_files = sorted(in_dir.glob("*.parquet")) if in_dir.exists() else []
    if not parquet_files:
        return {}

    df = pl.concat([pl.read_parquet(f) for f in parquet_files]).sort("timestamp")
    if label_col not in df.columns:
        return {}

    df_nixtla = prepare_nixtla_df(df, label_col).tail(5000)

    sf, metrics = train_stats_baseline(df_nixtla, n_splits=n_splits)
    save_model(sf, metrics, out_path)
    return metrics

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    run_stats(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        n_splits=args.n_splits,
        force=args.force,
    )
