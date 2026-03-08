"""
tests/test_models.py
====================
Unit tests for `mlfx.training` backends.

All tests use small synthetic DataFrames — no disk I/O required.

Run: pytest tests/test_models.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import polars as pl
import pytest


# ── Shared fixture ────────────────────────────────────────────────────────────


@pytest.fixture
def tiny_label_df() -> pl.DataFrame:
    """
    200 synthetic 1H bars with pre-computed label_10 column.
    Mirrors the schema produced by `mlfx.pipeline.labeling`.
    """
    n = 200
    base = datetime(2024, 1, 8, 0, tzinfo=timezone.utc)
    rng = np.random.default_rng(42)
    closes = 2020.0 + np.cumsum(rng.normal(0, 0.5, n))
    labels = rng.choice([-2, -1, 0, 1, 2], size=n).astype(np.int8)
    atr = np.full(n, 3.0)
    rsi = rng.uniform(20, 80, n)
    macd = rng.normal(0, 0.1, n)

    return pl.DataFrame(
        {
            "timestamp": [base + timedelta(hours=i) for i in range(n)],
            "open": (closes - 0.3).tolist(),
            "high": (closes + 2.0).tolist(),
            "low": (closes - 2.0).tolist(),
            "close": closes.tolist(),
            "tick_count": [1000] * n,
            "atr_14": atr.tolist(),
            "rsi_14": rsi.tolist(),
            "macd": macd.tolist(),
            "label_10": labels.tolist(),
        }
    )


# ── tests/backend_stats_baseline ────────────────────────────────────────────


class TestStatsForecastBaseline:
    """Tests for `mlfx.training.backend_stats_baseline` using statsforecast."""

    def test_prepare_nixtla_df_schema(self, tiny_label_df):
        """Output must have exactly [unique_id, ds, y] columns."""
        from mlfx.training.backends.stats import prepare_nixtla_df

        out, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        assert list(out.columns) == ["unique_id", "ds", "y"]

    def test_prepare_nixtla_df_unique_id_constant(self, tiny_label_df):
        """unique_id should be the literal string 'XAUUSD' for every row."""
        from mlfx.training.backends.stats import prepare_nixtla_df

        out, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        assert out["unique_id"].unique().to_list() == ["XAUUSD"]

    def test_prepare_nixtla_df_y_range(self, tiny_label_df):
        """y values should be in [0, 4] (remapped from {-2..2})."""
        from mlfx.training.backends.stats import prepare_nixtla_df

        out, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        y = out["y"].drop_nulls()
        assert float(y.min()) >= 0.0
        assert float(y.max()) <= 4.0

    def test_prepare_nixtla_df_row_count(self, tiny_label_df):
        """Output row count must equal input after drop_nulls on label column."""
        from mlfx.training.backends.stats import prepare_nixtla_df

        expected = tiny_label_df.drop_nulls("label_10").shape[0]
        out, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        assert len(out) == expected

    def test_train_stats_baseline_returns_sf_and_metrics(self, tiny_label_df):
        """train_stats_baseline must return (StatsForecast, dict) tuple."""
        from statsforecast import StatsForecast

        from mlfx.training.backends.stats import (
            prepare_nixtla_df,
            train_stats_baseline,
        )

        df_nixtla, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        sf, metrics = train_stats_baseline(df_nixtla, n_splits=2)

        assert isinstance(sf, StatsForecast)
        assert "cv_f1_macro" in metrics
        assert "model_type" in metrics
        assert metrics["model_type"] == "StatsForecast_Baseline"

    def test_train_stats_baseline_f1_keys(self, tiny_label_df):
        """cv_f1_macro must contain 'AutoARIMA' and 'SeasonalNaive' keys."""
        from mlfx.training.backends.stats import (
            prepare_nixtla_df,
            train_stats_baseline,
        )

        df_nixtla, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        _, metrics = train_stats_baseline(df_nixtla, n_splits=2)

        assert "AutoARIMA" in metrics["cv_f1_macro"]
        assert "SeasonalNaive" in metrics["cv_f1_macro"]

    def test_train_stats_baseline_f1_in_range(self, tiny_label_df):
        """F1 scores must be floats in [0, 1]."""
        from mlfx.training.backends.stats import (
            prepare_nixtla_df,
            train_stats_baseline,
        )

        df_nixtla, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        _, metrics = train_stats_baseline(df_nixtla, n_splits=2)

        for v in metrics["cv_f1_macro"].values():
            assert 0.0 <= v <= 1.0, f"F1 out of range: {v}"


# ── tests/backend_ml_models ─────────────────────────────────────────────────


class TestMLForecastModels:
    """Tests for `mlfx.training.backend_ml_models` using MLForecast + LightGBM."""

    def test_get_feature_columns_excludes_blacklist(self, tiny_label_df):
        """get_feature_columns must not include blacklisted columns."""
        from mlfx.training.backends.mlforecast import FEATURE_BLACKLIST, get_feature_columns

        cols = get_feature_columns(tiny_label_df)
        for bl in FEATURE_BLACKLIST:
            assert bl not in cols, f"Blacklisted col '{bl}' found in feature list"

    def test_get_feature_columns_only_numeric(self, tiny_label_df):
        """Feature columns must all be numeric dtype."""
        from mlfx.training.backends.mlforecast import get_feature_columns

        cols = get_feature_columns(tiny_label_df)
        for c in cols:
            assert tiny_label_df[c].dtype in (
                pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int8
            ), f"Non-numeric feature column: {c}"

    def test_prepare_nixtla_df_schema(self, tiny_label_df):
        """Output must include [unique_id, ds, y] plus feature columns."""
        from mlfx.training.backends.mlforecast import prepare_nixtla_df

        out, feat_cols = prepare_nixtla_df(tiny_label_df, "label_10")
        assert "unique_id" in out.columns
        assert "ds" in out.columns
        assert "y" in out.columns
        assert len(feat_cols) > 0

    def test_prepare_nixtla_df_y_dtype_int64(self, tiny_label_df):
        """y column must be Int64 (class indices)."""
        from mlfx.training.backends.mlforecast import prepare_nixtla_df

        out, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        assert out["y"].dtype == pl.Int64

    def test_train_ml_models_returns_mlforecast_and_metrics(self, tiny_label_df):
        """train_ml_models must return (MLForecast, dict)."""
        from mlforecast import MLForecast

        from mlfx.training.backends.mlforecast import prepare_nixtla_df, train_ml_models

        df_nixtla, feat_cols = prepare_nixtla_df(tiny_label_df, "label_10")
        # Use minimal trials and splits for speed
        mlf, metrics = train_ml_models(
            df_nixtla, feat_cols, n_trials=2, n_splits=2
        )

        assert isinstance(mlf, MLForecast)
        assert "best_cv_f1_macro" in metrics
        assert "model_type" in metrics
        assert metrics["model_type"] == "LGBMClassifier_MLForecast"

    def test_train_ml_models_f1_in_range(self, tiny_label_df):
        """CV F1 macro must be in [0, 1]."""
        from mlfx.training.backends.mlforecast import prepare_nixtla_df, train_ml_models

        df_nixtla, feat_cols = prepare_nixtla_df(tiny_label_df, "label_10")
        _, metrics = train_ml_models(df_nixtla, feat_cols, n_trials=2, n_splits=2)

        assert 0.0 <= metrics["best_cv_f1_macro"] <= 1.0

    def test_train_ml_models_n_samples_correct(self, tiny_label_df):
        """n_samples in metrics should match preprocessed row count (> 0)."""
        from mlfx.training.backends.mlforecast import prepare_nixtla_df, train_ml_models

        df_nixtla, feat_cols = prepare_nixtla_df(tiny_label_df, "label_10")
        _, metrics = train_ml_models(df_nixtla, feat_cols, n_trials=2, n_splits=2)

        assert metrics["n_samples"] > 0


# ── tests/backend_neural_forecast ───────────────────────────────────────────


class TestNeuralForecast:
    """Tests for `mlfx.training.backend_neural_forecast` using NeuralForecast."""

    def test_prepare_nixtla_df_schema(self, tiny_label_df):
        """Output must have exactly [unique_id, ds, y]."""
        from mlfx.training.backends.neuralforecast import prepare_nixtla_df

        out, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        assert list(out.columns) == ["unique_id", "ds", "y"]

    def test_prepare_nixtla_df_y_float64(self, tiny_label_df):
        """y must be Float64 for regression-style training."""
        from mlfx.training.backends.neuralforecast import prepare_nixtla_df

        out, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        assert out["y"].dtype == pl.Float64

    def test_prepare_nixtla_df_y_range(self, tiny_label_df):
        """y values must be in [0, 4] after remapping."""
        from mlfx.training.backends.neuralforecast import prepare_nixtla_df

        out, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        y = out["y"].drop_nulls()
        assert float(y.min()) >= 0.0
        assert float(y.max()) <= 4.0

    def test_train_neural_forecast_returns_nf_and_metrics(self, tiny_label_df):
        """train_neural_forecast must return (NeuralForecast, dict)."""
        from neuralforecast import NeuralForecast

        from mlfx.training.backends.neuralforecast import (
            prepare_nixtla_df,
            train_neural_forecast,
        )

        df_nixtla, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        nf, metrics = train_neural_forecast(
            df_nixtla,
            n_windows=2,
            freq="h",
            input_size=12,
            max_steps=5,  # minimal steps for test speed
        )

        assert isinstance(nf, NeuralForecast)
        assert "cv_f1_macro" in metrics
        assert "model_type" in metrics
        assert metrics["model_type"] == "NeuralForecast_NHiTS_NBEATS"

    def test_train_neural_forecast_f1_keys(self, tiny_label_df):
        """cv_f1_macro must contain NHiTS and NBEATS entries."""
        from mlfx.training.backends.neuralforecast import (
            prepare_nixtla_df,
            train_neural_forecast,
        )

        df_nixtla, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        _, metrics = train_neural_forecast(
            df_nixtla, n_windows=2, freq="h", input_size=12, max_steps=5
        )

        assert "NHITS" in metrics["cv_f1_macro"]
        assert "NBEATS" in metrics["cv_f1_macro"]

    def test_train_neural_forecast_f1_in_range(self, tiny_label_df):
        """All CV F1 values must be floats in [0, 1]."""
        from mlfx.training.backends.neuralforecast import (
            prepare_nixtla_df,
            train_neural_forecast,
        )

        df_nixtla, _ = prepare_nixtla_df(tiny_label_df, "label_10")
        _, metrics = train_neural_forecast(
            df_nixtla, n_windows=2, freq="h", input_size=12, max_steps=5
        )

        for k, v in metrics["cv_f1_macro"].items():
            assert 0.0 <= v <= 1.0, f"{k} F1 out of range: {v}"

    def test_freq_map_coverage(self):
        """_TF_FREQ must map all standard timeframe keys."""
        from mlfx.training.backends.neuralforecast import _TF_FREQ

        for tf in ["1m", "5m", "15m", "30m", "1H", "2H", "4H", "1D"]:
            assert tf in _TF_FREQ, f"Missing freq mapping for '{tf}'"
