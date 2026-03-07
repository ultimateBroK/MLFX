from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import polars as pl


class TestEvaluationBacktestContract:
    def test_backtest_adapter_exposes_compute_metrics(self):
        from mlfx.evaluation.backtest import compute_metrics

        metrics = compute_metrics(pl.DataFrame())
        assert metrics["total_trades"] == 0


class TestEvaluationReportingContract:
    def test_reporting_adapter_generates_expected_report_files(self, tmp_path: Path):
        from mlfx.evaluation.reporting import generate_full_report

        df = pl.DataFrame(
            {
                "timestamp": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
                "open": [1.0],
                "high": [2.0],
                "low": [0.5],
                "close": [1.5],
                "rsi_14": [55.0],
            }
        )
        trades = pl.DataFrame(
            {
                "entry_time": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
                "exit_time": [datetime(2024, 1, 1, 1, tzinfo=timezone.utc)],
                "signal": ["LONG"],
                "entry_price": [1.0],
                "exit_price": [1.5],
                "bars_held": [1],
                "pnl_r": [1.0],
                "reason": ["TP"],
                "weekday": [0],
                "hour": [0],
            }
        )

        generate_full_report("XAUUSD", "1H", df, trades, "label_10_R15", tmp_path)
        assert (tmp_path / "label_10_R15_candlestick.html").exists()
        assert (tmp_path / "label_10_R15_equity.png").exists()
        assert (tmp_path / "label_10_R15_heatmap.png").exists()


class TestEvaluationRunnerContract:
    def test_run_dataset_eval_returns_summary_metrics_and_artifacts(self, tmp_path: Path):
        from mlfx.evaluation.runner import run_dataset_eval

        df = pl.DataFrame(
            {
                "timestamp": [
                    datetime(2024, 1, 1, hour, tzinfo=timezone.utc) for hour in range(6)
                ],
                "open": [1.0, 1.1, 1.3, 1.2, 1.4, 1.5],
                "high": [1.2, 1.4, 1.6, 1.4, 1.6, 1.7],
                "low": [0.9, 1.0, 1.1, 1.1, 1.2, 1.3],
                "close": [1.1, 1.3, 1.2, 1.4, 1.5, 1.6],
                "atr_14": [0.2] * 6,
                "label_10": [1, 0, -1, 0, 1, 0],
                "rsi_14": [50.0] * 6,
            }
        )

        summary = run_dataset_eval(
            df,
            symbol="XAUUSD",
            tf="1H",
            label_col="label_10",
            out_dir=tmp_path,
        )

        assert "Total Trades" in summary
        assert "Win Rate (%)" in summary
        assert (tmp_path / "XAUUSD" / "1H" / "label_10_R15_candlestick.html").exists()
