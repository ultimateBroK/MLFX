import asyncio
import calendar
import json
import lzma
import os
import random
import struct
import urllib.request
from datetime import date, datetime

import aiohttp
import polars as pl

# ── Config (Defaults, overridden by argparse) ──────────────────────────────
BASE_URL = "https://datafeed.dukascopy.com/datafeed"

# Global config variables injected by main()
CONFIG = {
    "SYMBOL": "XAUUSD",
    "START_YEAR": 2015,
    "START_MONTH": 1,
    "OUTPUT_DIR": "data/raw/XAUUSD",
    "STATE_FILE": "data/raw/XAUUSD/completed_months.json",
    "MAX_CONCURRENT": 20,
    "ASSET_CLASS": "fx",
    "FORCE": False,
}


def get_state_file() -> str:
    return CONFIG["STATE_FILE"]


# ── State (single JSON) ───────────────────────────────────────────────────────
# Format: { "2015-01": {"rows": 2345022, "missing_hours": 0}, ... }


def load_state() -> dict:
    state_file = get_state_file()
    if os.path.exists(state_file):
        with open(state_file) as f:
            data = json.load(f)
        # Migrate old format: list of strings → dict
        if isinstance(data, list):
            data = {k: {"rows": -1, "missing_hours": 0} for k in data}
            _write_state(data)
            print(f"Migrated state file to new format ({len(data)} entries)")
        return data
    return {}


def _write_state(state: dict) -> None:
    state_file = get_state_file()
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def save_state(state: dict) -> None:
    _write_state(state)


def migrate_old_markers(state: dict) -> dict:
    """One-time: absorb old *.parquet.complete files into JSON, then remove them."""
    out_dir = CONFIG["OUTPUT_DIR"]
    if not os.path.exists(out_dir):
        return state

    old = [f for f in os.listdir(out_dir) if f.endswith(".parquet.complete")]
    for marker in old:
        key = marker.replace(".parquet.complete", "")
        state.setdefault(key, {"rows": -1, "missing_hours": 0})
        os.remove(os.path.join(out_dir, marker))
    if old:
        print(f"Migrated {len(old)} old markers → {get_state_file()}")
    return state


# ── Parse ─────────────────────────────────────────────────────────────────────


def parse_hour(
    raw: bytes, year: int, month: int, day: int, hour: int
) -> "pl.DataFrame | None":
    """Decode raw bi5 bytes → Polars DataFrame with timestamp_ms column."""
    if not raw:
        return None
    base_ms = int(datetime(year, month, day, hour).timestamp() * 1000)
    chunk = 20
    records = [
        (
            base_ms + struct.unpack_from(">I", raw, i)[0],
            struct.unpack_from(">I", raw, i + 4)[0] / 1000.0,  # ask
            struct.unpack_from(">I", raw, i + 8)[0] / 1000.0,  # bid
            struct.unpack_from(">f", raw, i + 12)[0],  # ask_vol
            struct.unpack_from(">f", raw, i + 16)[0],  # bid_vol
        )
        for i in range(0, len(raw) - chunk + 1, chunk)
    ]
    return (
        pl.DataFrame(
            records,
            schema=["timestamp_ms", "ask", "bid", "ask_volume", "bid_volume"],
            orient="row",
        )
        if records
        else None
    )


def to_datetime_df(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.from_epoch("timestamp_ms", time_unit="ms").alias("timestamp")
    ).select(["timestamp", "ask", "bid", "ask_volume", "bid_volume"])


# ── fetch_hour (sync, kept for tests) ─────────────────────────────────────────


def fetch_hour(
    year: int, month_idx: int, day: int, hour: int, retries: int = 4, timeout: int = 30
) -> "bytes | None | str":
    """Sync single-hour fetch. Returns bytes | None (404) | 'TIMEOUT'."""
    url = f"{BASE_URL}/{CONFIG['SYMBOL']}/{year:04d}/{month_idx:02d}/{day:02d}/{hour:02d}h_ticks.bi5"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return lzma.decompress(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt < retries - 1:
                import time

                time.sleep((2**attempt) + random.random())
        except Exception:
            if attempt < retries - 1:
                import time

                time.sleep((2**attempt) + random.random())
    return "TIMEOUT"


# ── Async fetch layer ─────────────────────────────────────────────────────────


async def _fetch_one(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    y: int,
    mi: int,
    d: int,
    h: int,
    month: int,
) -> "pl.DataFrame | None | str":
    """Async fetch + decompress + parse for one hour. Returns DataFrame | None | 'TIMEOUT'."""
    url = f"{BASE_URL}/{CONFIG['SYMBOL']}/{y:04d}/{mi:02d}/{d:02d}/{h:02d}h_ticks.bi5"
    async with sem:
        for attempt in range(4):
            try:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=30)
                ) as r:
                    if r.status == 404:
                        return None
                    if r.status in (429, 503):
                        await asyncio.sleep(min(2**attempt, 16) + random.random())
                        continue
                    compressed = await r.read()
                try:
                    raw = lzma.decompress(compressed)
                except lzma.LZMAError:
                    # Truncated read — retry
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                return parse_hour(raw, y, month, d, h)
            except (asyncio.TimeoutError, aiohttp.ClientError):
                if attempt < 3:
                    await asyncio.sleep(min(2**attempt, 8) * 0.5 + random.random())
    return "TIMEOUT"


async def _fetch_hours_async(slots: list, month: int) -> tuple[list, int]:
    sem = asyncio.Semaphore(CONFIG["MAX_CONCURRENT"])
    connector = aiohttp.TCPConnector(limit=CONFIG["MAX_CONCURRENT"], ttl_dns_cache=300)
    headers = {"User-Agent": "Mozilla/5.0"}

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        results = await asyncio.gather(
            *[_fetch_one(session, sem, y, mi, d, h, month) for y, mi, d, h in slots]
        )

    frames = []
    timed_out = 0
    for r in results:
        if r is None:
            pass  # 404 — no data for this hour
        elif isinstance(r, str):  # "TIMEOUT"
            timed_out += 1
        elif isinstance(r, pl.DataFrame):
            frames.append(r)
    return frames, timed_out


def fetch_hours(slots: list, month: int) -> list:
    """Public sync interface. Runs async fetch under the hood."""
    if not slots:
        return []
    frames, timed_out = asyncio.run(_fetch_hours_async(slots, month))
    if timed_out:
        print(f"  ⚠ {timed_out} hours timed out (will retry on next run)", flush=True)
    return frames


# ── Slot helpers ──────────────────────────────────────────────────────────────


def all_slots(year: int, month: int) -> list:
    """All tradeable hour slots in month."""
    mi = month - 1
    days_in_month = calendar.monthrange(year, month)[1]

    if CONFIG["ASSET_CLASS"] == "crypto":
        # Crypto matches 24/7 (do not filter out weekends)
        return [
            (year, mi, d, h) for d in range(1, days_in_month + 1) for h in range(24)
        ]
    else:
        # FX defaults: Skips Saturday + Sunday before 21:00 UTC (market closed).
        return [
            (year, mi, d, h)
            for d in range(1, days_in_month + 1)
            for h in range(24)
            if not (date(year, month, d).weekday() == 5)  # skip Sat
            and not (date(year, month, d).weekday() == 6 and h < 21)  # skip Sun 00-20h
        ]


def weekday_slots(year: int, month: int) -> list:
    """Mon–Fri all 24h slots (used for repair gap detection). Crypto returns 24/7 slots."""
    mi = month - 1
    days_in_month = calendar.monthrange(year, month)[1]

    if CONFIG["ASSET_CLASS"] == "crypto":
        return [
            (year, mi, d, h) for d in range(1, days_in_month + 1) for h in range(24)
        ]
    else:
        return [
            (year, mi, d, h)
            for d in range(1, days_in_month + 1)
            if date(year, month, d).weekday() < 5
            for h in range(24)
        ]


# ── Repair ────────────────────────────────────────────────────────────────────


def repair_month(year: int, month: int, file_path: str) -> tuple[int, int]:
    """Detect and patch missing weekday-hour slots in existing parquet.
    Returns: (total_rows, remaining_missing_hours)"""
    df = pl.read_parquet(file_path)
    covered = set(
        df.with_columns(
            [
                pl.col("timestamp").dt.day().alias("_d"),
                pl.col("timestamp").dt.hour().alias("_h"),
            ]
        )
        .select(["_d", "_h"])
        .unique()
        .rows()
    )

    missing = [
        (y, mi, d, h)
        for y, mi, d, h in weekday_slots(year, month)
        if (d, h) not in covered
    ]
    if not missing:
        return len(df), 0

    print(f"  → {len(missing)} weekday-hour slots missing, fetching...", flush=True)
    new_frames = fetch_hours(missing, month)

    if new_frames:
        added = sum(len(f) for f in new_frames)
        df = (
            pl.concat([df] + [to_datetime_df(f) for f in new_frames])
            .unique(subset=["timestamp"], keep="first")
            .sort("timestamp")
        )
        df.write_parquet(file_path)
        print(f"  → Patched +{added:,} rows")

    covered2 = set(
        df.with_columns(
            [
                pl.col("timestamp").dt.day().alias("_d"),
                pl.col("timestamp").dt.hour().alias("_h"),
            ]
        )
        .select(["_d", "_h"])
        .unique()
        .rows()
    )
    still_missing = sum(
        1 for y, mi, d, h in weekday_slots(year, month) if (d, h) not in covered2
    )
    return len(df), still_missing


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Universal Dukascopy Tick Downloader")
    parser.add_argument(
        "--symbol",
        type=str,
        default="XAUUSD",
        help="Trading symbol (e.g. BTCUSD, XAUUSD, EURUSD)",
    )
    parser.add_argument("--start-year", type=int, default=2015, help="Start year")
    parser.add_argument("--start-month", type=int, default=1, help="Start month (1-12)")
    parser.add_argument(
        "--end-year", type=int, default=datetime.now().year, help="End year"
    )
    parser.add_argument(
        "--end-month", type=int, default=datetime.now().month, help="End month (1-12)"
    )
    parser.add_argument(
        "--asset-class",
        type=str,
        choices=["fx", "crypto"],
        default="fx",
        help="Asset type (fx drops weekends, crypto does 24/7)",
    )
    parser.add_argument(
        "--concurrency", type=int, default=20, help="Max concurrent downloads"
    )
    parser.add_argument(
        "--force-repair",
        action="store_true",
        help="Force complete verification instead of skipping verified months",
    )

    args = parser.parse_args()

    # Update CONFIG
    CONFIG["SYMBOL"] = args.symbol
    CONFIG["START_YEAR"] = args.start_year
    CONFIG["START_MONTH"] = args.start_month
    CONFIG["ASSET_CLASS"] = args.asset_class
    CONFIG["MAX_CONCURRENT"] = args.concurrency
    CONFIG["FORCE"] = args.force_repair

    out_dir = f"data/raw/{args.symbol}"
    CONFIG["OUTPUT_DIR"] = out_dir
    CONFIG["STATE_FILE"] = os.path.join(out_dir, "completed_months.json")
    os.makedirs(out_dir, exist_ok=True)

    state = migrate_old_markers(load_state())

    print(
        f"Downloading {args.symbol} ({args.asset_class.upper()}) from {args.start_year}-{args.start_month:02d} to {args.end_year}-{args.end_month:02d}..."
    )

    for year in range(args.start_year, args.end_year + 1):
        m_start = args.start_month if year == args.start_year else 1
        m_end = args.end_month if year == args.end_year else 12

        for month in range(m_start, m_end + 1):
            key = f"{year}-{month:02d}"
            file_path = os.path.join(CONFIG["OUTPUT_DIR"], f"{key}.parquet")
            is_past = not (
                year == datetime.now().year and month == datetime.now().month
            )
            entry = state.get(key)

            # ── Already complete → skip ────────────────────────────────────
            if (
                is_past
                and entry
                and entry["missing_hours"] == 0
                and os.path.exists(file_path)
                and not CONFIG["FORCE"]
            ):
                rows = entry["rows"]
                print(f"Skip     {key}  rows={rows:>10,}  missing=0 ✓")
                continue

            # ── File exists → integrity check + repair ─────────────────────
            if os.path.exists(file_path):
                label = (
                    f"missing={entry['missing_hours']} hrs (retry)"
                    if entry
                    else "not yet verified"
                )
                print(f"Checking {key}  [{label}]")
                rows, missing = repair_month(year, month, file_path)
                flag = (
                    "✓ full"
                    if missing == 0
                    else f"⚠ {missing} weekday-hrs still missing"
                )
                print(f"         {key}  rows={rows:>10,}  {flag}\n")
                if is_past:
                    state[key] = {"rows": rows, "missing_hours": missing}
                    save_state(state)
                continue

            # ── Not on disk → fresh download ────────────────────────────────
            print(f"Download {key} ...", end=" ", flush=True)
            frames = fetch_hours(all_slots(year, month), month)
            if frames:
                df = to_datetime_df(pl.concat(frames).sort("timestamp_ms"))
                df.write_parquet(file_path)
                print(f"Saved {len(df):,} rows.")
            else:
                print("No data found.")

            if is_past:
                rows = len(df) if frames else 0
                state[key] = {"rows": rows, "missing_hours": 0}
                save_state(state)


if __name__ == "__main__":
    main()
