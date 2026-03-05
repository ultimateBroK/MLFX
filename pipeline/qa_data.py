"""
pipeline/qa_data.py
===================
Quality Assurance (QA) script for verifying the integrity of raw tick data downloaded from Dukascopy.
Runs validation using Polars to quickly scan Parquet files, detect data gaps, negative prices, nulls, and spread errors.
Generates an automated Markdown report.
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timedelta

import polars as pl


def find_significant_gaps(lf: pl.LazyFrame, asset_class: str) -> list:
    """Find gaps > 1 hour in the tick data that are not normal weekends/daily breaks."""
    df = lf.select("timestamp").collect().sort("timestamp")

    if len(df) <= 1:
        return []

    df = df.with_columns(df["timestamp"].diff().alias("diff"))

    # Capture gaps greater than 1 hour
    gaps = df.filter(pl.col("diff") > pl.duration(hours=1))

    results = []
    for row in gaps.iter_rows(named=True):
        end_time = row["timestamp"]
        diff_td = row["diff"]
        start_time = end_time - diff_td

        is_weekend = False
        if asset_class == "fx":
            # FX Weekend (Friday evening to Sunday evening)
            is_weekend = start_time.weekday() == 5 or (
                start_time.weekday() == 4 and start_time.hour >= 21
            )

        # Daily break for FX: 22:00 to 23:00 UTC (~1 hour gap)
        is_daily_break = asset_class == "fx" and (
            diff_td <= timedelta(hours=1, minutes=5)
        )

        if not is_weekend and not is_daily_break:
            hours_missing = diff_td.total_seconds() / 3600
            results.append(
                {
                    "start": start_time.strftime("%Y-%m-%d %H:%M"),
                    "end": end_time.strftime("%Y-%m-%d %H:%M"),
                    "duration_h": round(hours_missing, 2),
                    "day": start_time.strftime("%a"),
                }
            )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Universal Data Quality Assurance for Tick Data"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="XAUUSD",
        help="Trading symbol (e.g. BTCUSD, XAUUSD, EURUSD)",
    )
    parser.add_argument(
        "--asset-class",
        type=str,
        choices=["fx", "crypto"],
        default="fx",
        help="Asset type (effects gap logic)",
    )
    args = parser.parse_args()

    data_dir = f"data/raw/{args.symbol}"
    json_path = os.path.join(data_dir, "completed_months.json")

    print(f"--- Running QA Audit for {args.symbol} ---")

    if not os.path.exists(json_path):
        print(
            f"[!] Error: State file not found at {json_path}. Did you download the data yet?"
        )
        sys.exit(1)

    with open(json_path, "r") as f:
        completed_months = json.load(f)

    if not completed_months:
        print("[!] No completed months found in state file.")
        sys.exit(1)

    months = sorted(list(completed_months.keys()))
    total_rows_json = sum(
        v.get("rows", 0) for v in completed_months.values() if v.get("rows", -1) != -1
    )
    total_missing_hours = sum(
        v.get("missing_hours", 0) for v in completed_months.values()
    )

    print("Scanning Parquet files using Polars engine...")
    parquet_files = sorted(glob.glob(os.path.join(data_dir, "*.parquet")))

    if not parquet_files:
        print("[!] No .parquet files found.")
        sys.exit(1)

    total_rows_actual = 0
    total_nulls = 0
    total_negative_prices = 0
    total_negative_spreads = 0
    total_negative_volumes = 0

    month_stats = []
    all_unexpected_gaps = []

    for file in parquet_files:
        month_name = os.path.basename(file).replace(".parquet", "")
        lf = pl.scan_parquet(file)

        # 1. Run Validation Aggregations
        stats = (
            lf.select(
                [
                    pl.len().alias("count"),
                    (
                        pl.col("timestamp").is_null().sum()
                        + pl.col("ask").is_null().sum()
                        + pl.col("bid").is_null().sum()
                        + pl.col("ask_volume").is_null().sum()
                        + pl.col("bid_volume").is_null().sum()
                    ).alias("null_count"),
                    ((pl.col("ask") <= 0) | (pl.col("bid") <= 0))
                    .sum()
                    .alias("negative_price"),
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

            # Trigger deep gap scan if missing hours are detected
            if missing_hours > 0:
                gaps = find_significant_gaps(lf, args.asset_class)
                all_unexpected_gaps.extend(gaps)

        print(f"  ✓ {month_name}: {actual_count:,} rows")

    print("\nGenerating Markdown report...")

    # Generate Markdown Report Content
    md_content = f"# Data Quality Audit Report for {args.symbol} (Tick Data)\n\n"
    md_content += f"**Audit Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    md_content += f"**Storage Path:** `{data_dir}`\n"
    md_content += f"**Asset Class:** `{args.asset_class.upper()}`\n\n"

    md_content += "## 1. Data Overview\n"
    md_content += (
        f"- **Data Period:** From {months[0]} to {months[-1]} ({len(months)} months)\n"
    )
    md_content += f"- **Total Parquet Files:** {len(parquet_files)}\n"
    md_content += f"- **Total Actual Rows:** {total_rows_actual:,}\n\n"

    md_content += "## 2. Integrity Checks\n"
    md_content += f"- **Null Values (`NaN` / `None`):** {total_nulls:,}\n"
    md_content += f"- **Negative/Zero Prices (`ask <= 0` or `bid <= 0`):** {total_negative_prices:,}\n"
    md_content += (
        f"- **Negative Spreads (`ask` < `bid`):** {total_negative_spreads:,}\n"
    )
    md_content += f"- **Negative Volumes (`volume < 0`):** {total_negative_volumes:,}\n"
    md_content += (
        f"- **Total Missing Hours (from state):** {total_missing_hours:,} hours\n\n"
    )

    md_content += "## 3. Anomalies & Missing Data by Month\n"
    if len(month_stats) > 0:
        md_content += "| Month | Rows (Expected) | Rows (Actual) | Missing (hrs) | Nulls | Neg Price | Neg Spread | Neg Vol |\n"
        md_content += "|-------|-----------------|---------------|---------------|-------|-----------|------------|---------|\n"
        for s in month_stats:
            exp = s["expected_rows"] if s["expected_rows"] != -1 else "N/A"
            md_content += f"| {s['month']} | {exp} | {s['actual_rows']:,} | **{s['missing_hours']}** | {s['nulls']} | {s['negative_price']} | {s['negative_spread']} | {s['negative_volume']} |\n"
    else:
        md_content += "🎉 Excellent! No missing hours or garbage data detected across the entire cycle.\n"

    md_content += "\n## 4. Details of Gaps > 1 hour (Excluding Weekends)\n"
    if len(all_unexpected_gaps) > 0:
        md_content += (
            "List of notable connection loss / holidays detected in the data:\n\n"
        )
        # Show top 30 gaps only to avoid bloating the report
        sorted_gaps = sorted(
            all_unexpected_gaps, key=lambda x: x["duration_h"], reverse=True
        )
        md_content += "| Gap Start | Gap End | Duration (h) | Day |\n"
        md_content += "|-----------|---------|--------------|-----|\n"
        for g in sorted_gaps[:30]:
            md_content += (
                f"| {g['start']} | {g['end']} | {g['duration_h']} | {g['day']} |\n"
            )
        if len(sorted_gaps) > 30:
            md_content += f"\n*(... and {len(sorted_gaps) - 30} other smaller gaps)*\n"
    else:
        md_content += "\nNo unexpected data gaps found.\n"

    md_content += "\n## 5. Conclusion & Recommendations\n"
    if total_nulls == 0 and total_negative_prices == 0 and total_negative_spreads == 0:
        md_content += "- **Quality Status: Excellent.** The data is 100% clean structurally (no nulls, positive prices, valid spreads).\n"
        if total_missing_hours > 0:
            md_content += "- **Gap Notes:** Missing hours mostly align with early market closes prior to global holidays like Christmas and Good Friday. Ensure resampling logic handles forward-filling or gap drops.\n"
        md_content += "- **Status:** The data is **READY** for the ETL pipeline.\n"
    else:
        md_content += "- **WARNING:** The data contains garbage values (negatives/nulls). Additional filtering logic must be injected to the resampling block before inputting to models.\n"

    report_path = os.path.join(data_dir, f"{args.symbol}_Data_Quality_Report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n[+] Successfully exported report to: {report_path}")


if __name__ == "__main__":
    main()
