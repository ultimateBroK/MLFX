"""Feature and prediction drift detection.

Compares live / recent data distributions against a *reference* snapshot that
was captured at training time.  Uses the Kolmogorov-Smirnov (KS) test for
continuous features and Population Stability Index (PSI) as a complementary
scalar summary.

Typical workflow::

    from mlfx.monitoring.drift import DriftDetector, save_reference

    # --- at training time ---
    save_reference(train_df, feature_cols, symbol="XAUUSD", tf="1H")

    # --- in production ---
    detector = DriftDetector.load(symbol="XAUUSD", tf="1H")
    report = detector.detect(live_df, threshold_ks=0.1, threshold_psi=0.2)
    if report["drifted_features"]:
        print("Drift detected:", report["drifted_features"])
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from scipy import stats  # type: ignore[import]

from mlfx.config.paths import DEFAULT_PATHS

logger = logging.getLogger(__name__)

_REFERENCE_FILENAME = "drift_reference.json"


# ---------------------------------------------------------------------------
# Reference snapshot utilities
# ---------------------------------------------------------------------------


def save_reference(
    df: pl.DataFrame,
    feature_cols: list[str],
    symbol: str,
    tf: str,
    *,
    out_dir: Path | None = None,
    log_to_mlflow: bool = True,
) -> Path:
    """Compute and persist per-feature statistics for drift reference.

    For each feature column we store the mean, std, 5 percentile points
    (p5, p25, p50, p75, p95), and the raw sample (capped at 10 000 values) for
    KS testing.

    Parameters
    ----------
    df:
        Training or reference DataFrame.
    feature_cols:
        Columns to capture statistics for.
    symbol, tf:
        Identifiers used to scope the reference file name.
    out_dir:
        Output directory.  Defaults to ``outputs/monitoring/<symbol>/<tf>/``.
    log_to_mlflow:
        Whether to log the reference to MLflow.

    Returns
    -------
    Path
        Path to the written reference JSON.
    """
    base = out_dir or DEFAULT_PATHS.monitoring_dir(symbol, tf)
    base.mkdir(parents=True, exist_ok=True)

    reference: dict[str, Any] = {"symbol": symbol, "tf": tf, "features": {}}
    for col in feature_cols:
        if col not in df.columns:
            continue
        series = df[col].drop_nulls().to_numpy().astype(float)
        if len(series) == 0:
            continue
        sample = series[:10_000].tolist()
        reference["features"][col] = {
            "mean": float(np.mean(series)),
            "std": float(np.std(series)),
            "p5": float(np.percentile(series, 5)),
            "p25": float(np.percentile(series, 25)),
            "p50": float(np.percentile(series, 50)),
            "p75": float(np.percentile(series, 75)),
            "p95": float(np.percentile(series, 95)),
            "sample": sample,
        }

    out_path = base / _REFERENCE_FILENAME
    out_path.write_text(json.dumps(reference, indent=2))
    logger.info("Drift reference saved → %s  (%d features)", out_path, len(reference["features"]))

    # Log to MLflow
    if log_to_mlflow:
        _log_reference_to_mlflow(reference, out_path, symbol, tf)

    return out_path


def _log_reference_to_mlflow(
    reference: dict[str, Any],
    reference_path: Path,
    symbol: str,
    tf: str,
) -> None:
    """Log drift reference to MLflow."""
    try:
        import mlflow  # noqa: PLC0415

        from mlfx.config.mlflow import get_mlflow_config

        config = get_mlflow_config()
        if not config.is_mlflow_available():
            return

        config.setup_mlflow()

        # Set experiment
        experiment_name = f"{config.experiment_prefix}/monitoring/drift"
        mlflow.set_experiment(experiment_name)

        # Start run
        with mlflow.start_run(run_name=f"drift_reference_{symbol}_{tf}"):
            # Log params
            mlflow.log_params({
                "symbol": symbol,
                "tf": tf,
                "n_features": len(reference.get("features", {})),
            })

            # Log reference file as artifact
            mlflow.log_artifact(str(reference_path), artifact_path="drift_reference")

            # Log summary metrics
            for col, stats in reference.get("features", {}).items():
                safe_col = col.replace("/", "_").replace(" ", "_")
                mlflow.log_metrics({
                    f"feature.{safe_col}.mean": stats["mean"],
                    f"feature.{safe_col}.std": stats["std"],
                })

        logger.debug("Logged drift reference to MLflow")

    except ImportError:
        logger.debug("MLflow not installed; skipping drift reference logging.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to log drift reference to MLflow: %s", exc)


# ---------------------------------------------------------------------------
# Drift detector
# ---------------------------------------------------------------------------


class DriftDetector:
    """Compare live data distributions against a saved reference snapshot.

    Parameters
    ----------
    reference:
        Pre-loaded reference dict as produced by :func:`save_reference`.
    """

    def __init__(self, reference: dict[str, Any]) -> None:
        self._ref = reference

    @classmethod
    def load(
        cls,
        symbol: str,
        tf: str,
        *,
        ref_dir: Path | None = None,
    ) -> "DriftDetector":
        """Load a reference snapshot from disk.

        Raises :class:`FileNotFoundError` if no reference exists yet.
        """
        base = ref_dir or DEFAULT_PATHS.monitoring_dir(symbol, tf)
        path = base / _REFERENCE_FILENAME
        if not path.exists():
            raise FileNotFoundError(
                f"No drift reference found at {path}. "
                "Run save_reference() on training data first."
            )
        reference = json.loads(path.read_text())
        return cls(reference)

    # ------------------------------------------------------------------

    def detect(
        self,
        live_df: pl.DataFrame,
        *,
        threshold_ks: float = 0.1,
        threshold_psi: float = 0.2,
        min_samples: int = 30,
        log_to_mlflow: bool = True,
    ) -> dict[str, Any]:
        """Compute drift metrics for each feature and classify drift.

        Parameters
        ----------
        live_df:
            Recent production data (same schema as training data).
        threshold_ks:
            KS-statistic threshold above which a feature is *drifted*.
        threshold_psi:
            PSI threshold above which a feature is *drifted*.
        min_samples:
            Minimum live samples required to run the test.
        log_to_mlflow:
            Whether to log the drift report to MLflow.

        Returns
        -------
        dict
            ``{"drifted_features": [...], "metrics": {col: {ks, psi, ...}}}``
        """
        results: dict[str, dict[str, float]] = {}
        drifted: list[str] = []

        for col, ref_stats in self._ref.get("features", {}).items():
            if col not in live_df.columns:
                continue

            live_series = live_df[col].drop_nulls().to_numpy().astype(float)
            if len(live_series) < min_samples:
                logger.debug("Skipping %s: only %d live samples.", col, len(live_series))
                continue

            ref_sample = np.array(ref_stats["sample"], dtype=float)
            ks_stat, ks_p = stats.ks_2samp(ref_sample, live_series)
            psi = _compute_psi(ref_sample, live_series)

            results[col] = {
                "ks_stat": round(float(ks_stat), 4),
                "ks_p": round(float(ks_p), 4),
                "psi": round(float(psi), 4),
            }

            if ks_stat > threshold_ks or psi > threshold_psi:
                drifted.append(col)
                logger.warning(
                    "Drift detected in feature '%s'  ks=%.3f  psi=%.3f",
                    col, ks_stat, psi,
                )

        report: dict[str, Any] = {
            "drifted_features": drifted,
            "n_tested": len(results),
            "n_drifted": len(drifted),
            "metrics": results,
        }
        if drifted:
            logger.warning(
                "Total drifted features: %d / %d", len(drifted), len(results)
            )
        else:
            logger.info("No feature drift detected (%d features tested).", len(results))

        # Log to MLflow
        if log_to_mlflow:
            self._log_drift_to_mlflow(report)

        return report

    def _log_drift_to_mlflow(self, report: dict[str, Any]) -> None:
        """Log drift detection report to MLflow."""
        try:
            import mlflow  # noqa: PLC0415

            from mlfx.config.mlflow import get_mlflow_config

            config = get_mlflow_config()
            if not config.is_mlflow_available():
                return

            config.setup_mlflow()

            symbol = self._ref.get("symbol", "unknown")
            tf = self._ref.get("tf", "unknown")

            # Set experiment
            experiment_name = f"{config.experiment_prefix}/monitoring/drift"
            mlflow.set_experiment(experiment_name)

            # Start run
            with mlflow.start_run(run_name=f"drift_detection_{symbol}_{tf}"):
                # Log params
                mlflow.log_params({
                    "symbol": symbol,
                    "tf": tf,
                })

                # Log summary metrics
                mlflow.log_metrics({
                    "n_tested": report["n_tested"],
                    "n_drifted": report["n_drifted"],
                    "drift_ratio": report["n_drifted"] / max(report["n_tested"], 1),
                })

                # Log per-feature metrics
                for col, metrics in report.get("metrics", {}).items():
                    safe_col = col.replace("/", "_").replace(" ", "_")
                    mlflow.log_metrics({
                        f"drift.{safe_col}.ks_stat": metrics["ks_stat"],
                        f"drift.{safe_col}.psi": metrics["psi"],
                    })

                # Set tag for drifted features
                if report["drifted_features"]:
                    mlflow.set_tag("drifted_features", ",".join(report["drifted_features"]))

            logger.debug("Logged drift report to MLflow")

        except ImportError:
            logger.debug("MLflow not installed; skipping drift report logging.")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to log drift report to MLflow: %s", exc)


# ---------------------------------------------------------------------------
# PSI helper
# ---------------------------------------------------------------------------


def _compute_psi(
    reference: np.ndarray,
    production: np.ndarray,
    bins: int = 10,
    epsilon: float = 1e-6,
) -> float:
    """Population Stability Index between reference and production distributions."""
    combined = np.concatenate([reference, production])
    breakpoints = np.percentile(combined, np.linspace(0, 100, bins + 1))
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf

    ref_counts = np.histogram(reference, bins=breakpoints)[0].astype(float)
    prod_counts = np.histogram(production, bins=breakpoints)[0].astype(float)

    ref_pct = (ref_counts + epsilon) / (ref_counts.sum() + epsilon * bins)
    prod_pct = (prod_counts + epsilon) / (prod_counts.sum() + epsilon * bins)

    psi = float(np.sum((prod_pct - ref_pct) * np.log(prod_pct / ref_pct + epsilon)))
    return max(0.0, psi)
