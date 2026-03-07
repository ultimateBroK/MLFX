"""Quality-audit utilities for downloaded raw tick data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from datetime import datetime, timedelta

import polars as pl

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths


def find_significant_gaps(lazy_frame: pl.LazyFrame, asset_class: str) -> list[dict[str, object]]:
    """Find gaps larger than one hour that are not normal market closures."""
    df = lazy_frame.select("timestamp").collect().sort("timestamp")
    if len(df) <= 1:
        return []

    df = df.with_columns(df["timestamp"].diff().alias("diff"))
    gaps = df.filter(pl.col("diff") > pl.duration(hours=1))

    results: list[dict[str, object]] = []
    for row in gaps.iter_rows(named=True):
        end_time = row["timestamp"]
        diff_td = row["diff"]
        start_time = end_time - diff_td

        is_weekend = False
        if asset_class == "fx":
            is_weekend = start_time.weekday() == 5 or (
                start_time.weekday() == 4 and start_time.hour >= 21
            )

        is_daily_break = asset_class == "fx" and diff_td <= timedelta(hours=1, minutes=5)
        if is_weekend or is_daily_break:
            continue

        results.append(
            {
                "start": start_time.strftime("%Y-%m-%d %H:%M"),
                "end": end_time.strftime("%Y-%m-%d %H:%M"),
                "duration_h": round(diff_td.total_seconds() / 3600, 2),
                "day": start_time.strftime("%a"),
            }
        )
    return results


def run_quality_audit(
    symbol: str = "XAUUSD",
    asset_class: str = "fx",
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> Path:
    """Scan raw monthly parquet files and write a Markdown QA report."""
    data_dir = paths.raw_data_dir(symbol)
    state_file = paths.state_file(symbol)

    print(f"--- Running QA Audit for {symbol} ---")
    if not state_file.exists():
        print(f"[!] Error: State file not found at {state_file}. Did you download the data yet?")
        raise SystemExit(1)

    completed_months = json.loads(state_file.read_text())
    if not completed_months:
        print("[!] No completed months found in state file.")
        raise SystemExit(1)

    months = sorted(completed_months.keys())
    total_missing_hours = sum(entry.get("missing_hours", 0) for entry in completed_months.values())
    parquet_files = sorted(data_dir.glob("*.parquet"))
    if not parquet_files:
        print("[!] No .parquet files found.")
        raise SystemExit(1)

    total_rows_actual = 0
    total_nulls = 0
    total_negative_prices = 0
    total_negative_spreads = 0
    total_negative_volumes = 0
    month_stats: list[dict[str, object]] = []
    all_unexpected_gaps: list[dict[str, object]] = []

    print("Scanning Parquet files using Polars engine...")
    for parquet_file in parquet_files:
        month_name = parquet_file.stem
        lazy_frame = pl.scan_parquet(parquet_file)
        stats = (
            lazy_frame.select(
                [
                    pl.len().alias("count"),
                    (
                        pl.col("timestamp").is_null().sum()
                        + pl.col("ask").is_null().sum()
                        + pl.col("bid").is_null().sum()
                        + pl.col("ask_volume").is_null().sum()
                        + pl.col("bid_volume").is_null().sum()
                    ).alias("null_count"),
                    ((pl.col("ask") <= 0) | (pl.col("bid") <= 0)).sum().alias("negative_price"),
                    (pl.col("ask") < pl.col("bid")).sum().alias("negative_spread"),
                    ((pl.col("ask_volume") < 0) | (pl.col("bid_volume") < 0))
                    .sum()
                    .alias("negative_volume"),
                ]
            )
            .collect()
            .to_dicts()[0]
        )

        actual_count = stats["count"]
        total_rows_actual += actual_count
        total_nulls += stats["null_count"]
        total_negative_prices += stats["negative_price"]
        total_negative_spreads += stats["negative_spread"]
        total_negative_volumes += stats["negative_volume"]

        expected_count = completed_months.get(month_name, {}).get("rows", -1)
        missing_hours = completed_months.get(month_name, {}).get("missing_hours", 0)
        is_anomalous = (
            stats["null_count"] > 0
            or stats["negative_price"] > 0
            or stats["negative_spread"] > 0
            or stats["negative_volume"] > 0
            or (expected_count != -1 and actual_count != expected_count)
            or missing_hours > 0
        )

        if is_anomalous:
            month_stats.append(
                {
                    "month": month_name,
                    "expected_rows": expected_count,
                    "actual_rows": actual_count,
                    "missing_hours": missing_hours,
                    "nulls": stats["null_count"],
                    "negative_price": stats["negative_price"],
                    "negative_spread": stats["negative_spread"],
                    "negative_volume": stats["negative_volume"],
                }
            )
            if missing_hours > 0:
                all_unexpected_gaps.extend(find_significant_gaps(lazy_frame, asset_class))

        print(f"  ✓ {month_name}: {actual_count:,} rows")

    report_path = data_dir / f"{symbol}_Data_Quality_Report.md"
    report_path.write_text(
        _build_markdown_report(
            symbol=symbol,
            asset_class=asset_class,
            data_dir=data_dir,
            months=months,
            parquet_files=parquet_files,
            total_rows_actual=total_rows_actual,
            total_nulls=total_nulls,
            total_negative_prices=total_negative_prices,
            total_negative_spreads=total_negative_spreads,
            total_negative_volumes=total_negative_volumes,
            total_missing_hours=total_missing_hours,
            month_stats=month_stats,
            all_unexpected_gaps=all_unexpected_gaps,
        ),
        encoding="utf-8",
    )
    print(f"\n[+] Successfully exported report to: {report_path}")
    return report_path


def _build_markdown_report(
    *,
    symbol: str,
    asset_class: str,
    data_dir: Path,
    months: list[str],
    parquet_files: list[Path],
    total_rows_actual: int,
    total_nulls: int,
    total_negative_prices: int,
    total_negative_spreads: int,
    total_negative_volumes: int,
    total_missing_hours: int,
    month_stats: list[dict[str, object]],
    all_unexpected_gaps: list[dict[str, object]],
) -> str:
    """Render the audit report as Markdown."""
    content = f"# Data Quality Audit Report for {symbol} (Tick Data)\n\n"
    content += f"**Audit Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"**Storage Path:** `{data_dir}`\n"
    content += f"**Asset Class:** `{asset_class.upper()}`\n\n"

    content += "## 1. Data Overview\n"
    content += f"- **Data Period:** From {months[0]} to {months[-1]} ({len(months)} months)\n"
    content += f"- **Total Parquet Files:** {len(parquet_files)}\n"
    content += f"- **Total Actual Rows:** {total_rows_actual:,}\n\n"

    content += "## 2. Integrity Checks\n"
    content += f"- **Null Values (`NaN` / `None`):** {total_nulls:,}\n"
    content += f"- **Negative/Zero Prices (`ask <= 0` or `bid <= 0`):** {total_negative_prices:,}\n"
    content += f"- **Negative Spreads (`ask < bid`):** {total_negative_spreads:,}\n"
    content += f"- **Negative Volumes (`volume < 0`):** {total_negative_volumes:,}\n"
    content += f"- **Total Missing Hours (from state):** {total_missing_hours:,} hours\n\n"

    content += "## 3. Anomalies & Missing Data by Month\n"
    if month_stats:
        content += "| Month | Rows (Expected) | Rows (Actual) | Missing (hrs) | Nulls | Neg Price | Neg Spread | Neg Vol |\n"
        content += "|-------|-----------------|---------------|---------------|-------|-----------|------------|---------|\n"
        for stat in month_stats:
            expected_rows = stat["expected_rows"] if stat["expected_rows"] != -1 else "N/A"
            content += (
                f"| {stat['month']} | {expected_rows} | {stat['actual_rows']:,} | "
                f"**{stat['missing_hours']}** | {stat['nulls']} | {stat['negative_price']} | "
                f"{stat['negative_spread']} | {stat['negative_volume']} |\n"
            )
    else:
        content += "Excellent! No missing hours or garbage data detected across the entire cycle.\n"

    content += "\n## 4. Details of Gaps > 1 hour (Excluding Weekends)\n"
    if all_unexpected_gaps:
        content += "List of notable connection loss / holidays detected in the data:\n\n"
        sorted_gaps = sorted(
            all_unexpected_gaps,
            key=lambda item: item["duration_h"],
            reverse=True,
        )
        content += "| Gap Start | Gap End | Duration (h) | Day |\n"
        content += "|-----------|---------|--------------|-----|\n"
        for gap in sorted_gaps[:30]:
            content += f"| {gap['start']} | {gap['end']} | {gap['duration_h']} | {gap['day']} |\n"
        if len(sorted_gaps) > 30:
            content += f"\n*... and {len(sorted_gaps) - 30} other smaller gaps*\n"
    else:
        content += "\nNo unexpected data gaps found.\n"

    content += "\n## 5. Conclusion & Recommendations\n"
    if total_nulls == 0 and total_negative_prices == 0 and total_negative_spreads == 0:
        content += "- **Quality Status: Excellent.** The data is structurally clean.\n"
        if total_missing_hours > 0:
            content += "- **Gap Notes:** Review holiday-related closures before downstream modeling.\n"
        content += "- **Status:** The data is **READY** for the ETL pipeline.\n"
    else:
        content += "- **Warning:** The data contains garbage values and needs further cleaning before modeling.\n"

    return content


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quality assurance audit for raw tick data")
    parser.add_argument("--symbol", type=str, default="XAUUSD")
    parser.add_argument("--asset-class", type=str, choices=["fx", "crypto"], default="fx")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        run_quality_audit(symbol=args.symbol, asset_class=args.asset_class)
    except SystemExit as exc:
        sys.exit(exc.code)


if __name__ == "__main__":
    main()
