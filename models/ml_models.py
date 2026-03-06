"""
models/ml_models.py
===================
MLForecast approach using LightGBM for XAUUSD direction prediction.
Replaces ts_forest.py and gradient_boost.py.

Optuna is used to find optimal LightGBM parameters via TimeSeriesSplit.
Features include static exogenous features (computed prior) and lags.

Output: outputs/models/{symbol}/{tf}/ml_models_{label_col}.pkl
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import optuna
import polars as pl
from mlforecast import MLForecast
from sklearn.metrics import f1_score
from sklearn.model_selection import TimeSeriesSplit

logger = logging.getLogger(__name__)

LABELS_DIR = Path("data/labels")
SAVED_DIR = Path("outputs/models")

FEATURE_BLACKLIST = {
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "tick_count",
    "close_ahead_5",
    "close_ahead_10",
    "close_ahead_20",
    "label_5",
    "label_10",
    "label_20",
}

def get_feature_columns(df: pl.DataFrame) -> list[str]:
    return [
        c
        for c in df.columns
        if c not in FEATURE_BLACKLIST
        and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int8)
    ]

def prepare_nixtla_df(df: pl.DataFrame, label_col: str) -> pl.DataFrame:
    """Format dataframe for Nixtla MLForecast (unique_id, ds, y)."""
    feature_cols = get_feature_columns(df)
    subset = df.select(["timestamp", label_col] + feature_cols).drop_nulls()
    
    unique_id_col = pl.lit("XAUUSD").alias("unique_id")
    ds_col = pl.col("timestamp").alias("ds")
    
    # Map labels {-2, -1, 0, 1, 2} to {0, 1, 2, 3, 4} for multi-class classifiers
    y_col = (pl.col(label_col) + 2).cast(pl.Int64).alias("y")
    
    subset = subset.with_columns([unique_id_col, ds_col, y_col])
    
    return subset.select(["unique_id", "ds", "y"] + feature_cols), feature_cols

def _lgb_objective(
    trial: optuna.Trial,
    df_train: pl.DataFrame,
    feature_cols: list[str],
    n_splits: int,
    freq: str = '1h'
) -> float:
    params = {
        "num_leaves": trial.suggest_int("num_leaves", 15, 127),
        "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.3, log=True),
        "n_estimators": trial.suggest_int("n_estimators", 100, 300),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "objective": "multiclass",
        "num_class": 5,
        "verbose": -1,
        "random_state": 42,
    }

    df_pd = df_train.to_pandas()
    # Replace ds with continuous integers to avoid "missing inputs" errors due to weekend gaps in dates
    df_pd['ds'] = np.arange(len(df_pd))
    step_size = max(1, len(df_pd) // (n_splits * 10))
    h = step_size
    
    model = lgb.LGBMClassifier(**params)
    mlf = MLForecast(
        models=[model],
        freq=1,  # Since we use integer ds
        lags=[1, 2, 3, 4, 5],
    )
    
    cv_df = mlf.cross_validation(
        df=df_pd,
        n_windows=n_splits,
        step_size=step_size,
        h=h,
        static_features=[]
    )
    
    y_true = cv_df['y'].values
    preds = cv_df['LGBMClassifier'].values
    return float(f1_score(y_true, preds, average="macro", zero_division=0))

def train_ml_models(
    df: pl.DataFrame,
    feature_cols: list[str],
    n_trials: int = 15,
    n_splits: int = 5,
) -> tuple[MLForecast, dict]:
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize")
    
    study.optimize(
        lambda t: _lgb_objective(t, df, feature_cols, n_splits=n_splits),
        n_trials=n_trials,
        show_progress_bar=False,
    )
    
    best_params = study.best_params | {
        "objective": "multiclass",
        "num_class": 5,
        "verbose": -1,
        "random_state": 42,
    }
    
    logger.info("Best LGBM params: %s | F1: %.4f", best_params, study.best_value)

    # Train final MLForecast wrapper
    model = lgb.LGBMClassifier(**best_params)
    mlf = MLForecast(
        models=[model],
        freq='1h',
        lags=[1, 2, 3, 4, 5], # Extract basic lag features via MLForecast
    )
    
    # Fit the whole dataset
    df_pd = df.to_pandas()
    mlf.fit(df_pd, static_features=[])

    # Compute train metric
    df_preps = mlf.preprocess(df_pd, static_features=[])
    X_train = df_preps.drop(columns=['unique_id', 'ds', 'y']).values
    y_train = df_preps['y'].values
    
    # The underlying model is inside mlf.models_[model.__class__.__name__]
    final_lgb = mlf.models_['LGBMClassifier']
    preds = final_lgb.predict(X_train)
    
    train_f1 = float(f1_score(y_train, preds, average="macro", zero_division=0))
    
    metrics = {
        "best_cv_f1_macro": study.best_value,
        "f1_macro_train": train_f1,
        "best_params": best_params,
        "n_samples": len(df_preps),
        "model_type": "LGBMClassifier_MLForecast"
    }
    
    logger.info("Final Train F1: %.4f", train_f1)
    return mlf, metrics

def save_model(mlf: MLForecast, metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(mlf, f)
    metrics_path = path.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2, default=str))
    logger.info("✓ MLForecast model saved → %s", path)

def run_ml_models(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label_col: str = "label_10",
    n_trials: int = 15,
    n_splits: int = 5,
    force: bool = False,
) -> dict:
    in_dir = LABELS_DIR / symbol / tf
    out_dir = SAVED_DIR / symbol / tf
    out_path = out_dir / f"ml_models_{label_col}.pkl"

    if out_path.exists() and not force:
        logger.info("MLForecast model exists at %s", out_path)
        return {}

    parquet_files = sorted(in_dir.glob("*.parquet")) if in_dir.exists() else []
    if not parquet_files:
        return {}

    df = pl.concat([pl.read_parquet(f) for f in parquet_files]).sort("timestamp")
    if label_col not in df.columns:
        return {}

    df_nixtla, feature_cols = prepare_nixtla_df(df, label_col)

    mlf, metrics = train_ml_models(df_nixtla, feature_cols, n_trials=n_trials, n_splits=n_splits)
    save_model(mlf, metrics, out_path)
    return metrics

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--n-trials", type=int, default=15)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    run_ml_models(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        n_trials=args.n_trials,
        n_splits=args.n_splits,
        force=args.force,
    )
