"""
Package-native MLForecast backend for XAUUSD direction prediction.
"""

from __future__ import annotations

import argparse
import logging
import warnings

import lightgbm as lgb
import numpy as np
import optuna
import polars as pl
from mlforecast import MLForecast
from sklearn.metrics import f1_score

from mlfx.training._utils import set_seed
from mlfx.training.artifacts import save_pickle_artifact
from mlfx.training.data import build_model_output_path, load_labelled_dataset
from mlfx.training.feature_selection import (
    DEFAULT_FEATURE_BLACKLIST,
    select_numeric_feature_columns,
)

logger = logging.getLogger(__name__)

# Preserve the historical public symbol expected by tests/importers.
FEATURE_BLACKLIST = DEFAULT_FEATURE_BLACKLIST


def get_feature_columns(df: pl.DataFrame) -> list[str]:
    """Return numeric feature columns excluding blacklisted (timestamp, OHLCV, labels)."""
    return select_numeric_feature_columns(df)


# Lag order used by MLForecast; trim this many leading rows so lag features have no nulls.
MLF_LAG_ORDER = 5


def prepare_nixtla_df(df: pl.DataFrame, label_col: str, symbol: str = "XAUUSD") -> tuple[pl.DataFrame, list[str]]:
    """Format dataframe for Nixtla MLForecast (unique_id, ds, y).

    Drops rows with null in any feature/label, then trims the first MLF_LAG_ORDER
    rows per series so that lag features (1..5) are never null, avoiding
    mlforecast "Found null values" warnings.
    """
    feature_cols = get_feature_columns(df)
    subset = df.select(["timestamp", label_col] + feature_cols).drop_nulls()

    unique_id_col = pl.lit(symbol).alias("unique_id")
    ds_col = pl.col("timestamp").alias("ds")
    y_col = (pl.col(label_col) + 2).cast(pl.Int64).alias("y")
    subset = subset.with_columns([unique_id_col, ds_col, y_col])

    # Trim first MLF_LAG_ORDER rows per series so lag features have no nulls.
    if len(subset) > MLF_LAG_ORDER:
        subset = subset.slice(MLF_LAG_ORDER)
    return subset.select(["unique_id", "ds", "y"] + feature_cols), feature_cols


def _lgb_objective(
    trial: optuna.Trial,
    df_train: pl.DataFrame,
    feature_cols: list[str],
    n_splits: int,
    freq: str = "1h",
    seed: int = 42,
) -> float:
    del feature_cols, freq

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
        "random_state": seed,
    }

    df_pd = df_train.to_pandas()
    # Replace ds with continuous integers to avoid "missing inputs" errors
    # caused by market/weekend gaps in timestamps.
    df_pd["ds"] = np.arange(len(df_pd))
    step_size = max(1, len(df_pd) // (n_splits * 10))
    h = step_size

    model = lgb.LGBMClassifier(**params)
    mlf = MLForecast(
        models=[model],
        freq=1,
        lags=[1, 2, 3, 4, 5],
    )

    cv_df = mlf.cross_validation(
        df=df_pd,
        n_windows=n_splits,
        step_size=step_size,
        h=h,
        static_features=[],
    )

    y_true = cv_df["y"].values
    preds = cv_df["LGBMClassifier"].values
    return float(f1_score(y_true, preds, average="macro", zero_division=0))


def train_ml_models(
    df: pl.DataFrame,
    feature_cols: list[str],
    n_trials: int = 15,
    n_splits: int = 5,
    seed: int = 42,
) -> tuple[MLForecast, dict]:
    """Train MLForecast with LightGBM and Optuna HPO. Returns (mlf, metrics)."""
    # Avoid hundreds of "Found null values in ema_200" from mlforecast (lag warmup).
    warnings.filterwarnings(
        "ignore",
        message="Found null values",
        category=UserWarning,
        module="mlforecast",
    )
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    logger.info(
        "Hyperparameter search: n_trials=%d, n_splits=%d, samples=%d",
        n_trials,
        n_splits,
        len(df),
    )
    study.optimize(
        lambda trial: _lgb_objective(trial, df, feature_cols, n_splits=n_splits, seed=seed),
        n_trials=n_trials,
        show_progress_bar=True,
    )

    best_params = study.best_params | {
        "objective": "multiclass",
        "num_class": 5,
        "verbose": -1,
        "random_state": seed,
    }

    logger.info("Best LGBM params: %s | F1: %.4f", best_params, study.best_value)

    model = lgb.LGBMClassifier(**best_params)
    mlf = MLForecast(
        models=[model],
        freq="1h",
        lags=[1, 2, 3, 4, 5],
    )

    df_pd = df.to_pandas()
    mlf.fit(df_pd, static_features=[])

    df_preps = mlf.preprocess(df_pd, static_features=[])
    # Keep feature matrix as a DataFrame so LightGBM preserves column names,
    # avoiding scikit-learn's "X does not have valid feature names" warning.
    X_train = df_preps.drop(columns=["unique_id", "ds", "y"])
    y_train = df_preps["y"]

    final_lgb = mlf.models_["LGBMClassifier"]
    preds = final_lgb.predict(X_train)

    train_f1 = float(
        f1_score(
            y_train.to_numpy(),
            preds,
            average="macro",
            zero_division=0,
        )
    )

    metrics = {
        "best_cv_f1_macro": study.best_value,
        "f1_macro_train": train_f1,
        "best_params": best_params,
        "n_samples": len(df_preps),
        "selected_features": feature_cols,
        "model_type": "LGBMClassifier_MLForecast",
    }

    logger.info("Final Train F1: %.4f", train_f1)
    return mlf, metrics


def save_model(mlf: MLForecast, metrics: dict, path) -> None:
    """Persist MLForecast model to .pkl artifact for serving."""
    save_pickle_artifact(mlf, metrics, path)
    logger.info("✓ MLForecast model saved → %s", path)


def run_ml_models(
    symbol: str = "XAUUSD",
    tf: str = "1H",
    label_col: str = "label_10",
    n_trials: int = 15,
    n_splits: int = 5,
    force: bool = False,
    seed: int = 42,
    train_start: str | None = None,
    train_end: str | None = None,
) -> dict:
    """Train MLForecast + LightGBM with Optuna HPO. Returns metrics dict or {} if skipped."""
    set_seed(seed)
    out_path = build_model_output_path(
        f"ml_models_{label_col}",
        symbol,
        tf,
        label_col,
        suffix=".pkl",
    )

    if out_path.exists() and not force:
        logger.info("MLForecast model exists at %s", out_path)
        return {}

    df = load_labelled_dataset(
        symbol,
        tf,
        train_start=train_start,
        train_end=train_end,
    )
    if df is None or label_col not in df.columns:
        logger.warning("No labelled data or missing column %s", label_col)
        return {}

    n_raw = len(df)
    df_nixtla, feature_cols = prepare_nixtla_df(df, label_col, symbol=symbol)
    n_used = len(df_nixtla)
    logger.info(
        "Data: %d rows loaded → %d after drop_nulls + warmup trim (%d features)",
        n_raw,
        n_used,
        len(feature_cols),
    )
    mlf, metrics = train_ml_models(
        df_nixtla,
        feature_cols,
        n_trials=n_trials,
        n_splits=n_splits,
        seed=seed,
    )
    save_model(mlf, metrics, out_path)
    metrics["artifact_path"] = str(out_path)
    return metrics


def build_parser() -> argparse.ArgumentParser:
    """Build argparse for standalone MLForecast training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--tf", default="1H")
    parser.add_argument("--label", default="label_10")
    parser.add_argument("--n-trials", type=int, default=15)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    """CLI entrypoint for standalone MLForecast training."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args()
    run_ml_models(
        symbol=args.symbol,
        tf=args.tf,
        label_col=args.label,
        n_trials=args.n_trials,
        n_splits=args.n_splits,
        force=args.force,
    )


if __name__ == "__main__":
    main()
