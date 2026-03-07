from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl


def test_file_tracker_round_trip(tmp_path: Path):
    from mlfx.tracking.tracker import FileTracker

    tracker = FileTracker(runs_dir=tmp_path / "runs")
    run_id = tracker.start_run("unit_test_run", {"backend": "mlf"})
    tracker.log_metrics(run_id, {"f1": 0.1234567})
    tracker.end_run(run_id, status="FINISHED")

    run_file = tmp_path / "runs" / f"{run_id}.json"
    assert run_file.exists()
    payload = run_file.read_text()
    assert '"status": "FINISHED"' in payload
    assert '"f1": 0.123457' in payload


def test_drift_detector_reference_and_detect(tmp_path: Path):
    from mlfx.monitoring.drift import DriftDetector, save_reference

    base_ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    train_df = pl.DataFrame(
        {
            "timestamp": [base_ts + timedelta(hours=i) for i in range(80)],
            "feat_x": [float(i) for i in range(80)],
            "feat_y": [float(i % 5) for i in range(80)],
        }
    )
    live_df = pl.DataFrame(
        {
            "timestamp": [base_ts + timedelta(hours=i) for i in range(80, 160)],
            "feat_x": [float(i + 100) for i in range(80)],  # strong shift
            "feat_y": [float(i % 5) for i in range(80)],
        }
    )

    save_reference(
        train_df,
        feature_cols=["feat_x", "feat_y"],
        symbol="XAUUSD",
        tf="1H",
        out_dir=tmp_path / "monitoring",
    )
    detector = DriftDetector.load("XAUUSD", "1H", ref_dir=tmp_path / "monitoring")
    report = detector.detect(live_df, threshold_ks=0.05, threshold_psi=0.05, min_samples=30)

    assert report["n_tested"] >= 2
    assert "feat_x" in report["drifted_features"]
