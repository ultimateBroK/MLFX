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

# ── Config ───────────────────────────────────────────────────────────────────
SYMBOL = "XAUUSD"
START_YEAR = 2015
START_MONTH = 1
OUTPUT_DIR = f"data/raw/{SYMBOL}"
STATE_FILE = os.path.join(OUTPUT_DIR, "completed_months.json")
MAX_CONCURRENT = 20  # simultaneous aiohttp connections

os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_URL = "https://datafeed.dukascopy.com/datafeed"


# ── State (single JSON) ───────────────────────────────────────────────────────
# Format: { "2015-01": {"rows": 2345022, "missing_hours": 0}, ... }


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            data = json.load(f)
        # Migrate old format: list of strings → dict
        if isinstance(data, list):
            data = {k: {"rows": -1, "missing_hours": 0} for k in data}
            _write_state(data)
            print(f"Migrated state file to new format ({len(data)} entries)")
        return data
    return {}


def _write_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def save_state(state: dict) -> None:
    _write_state(state)


def migrate_old_markers(state: dict) -> dict:
    """One-time: absorb old *.parquet.complete files into JSON, then remove them."""
    old = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".parquet.complete")]
    for marker in old:
        key = marker.replace(".parquet.complete", "")
        state.setdefault(key, {"rows": -1, "missing_hours": 0})
        os.remove(os.path.join(OUTPUT_DIR, marker))
    if old:
        print(f"Migrated {len(old)} old markers → {STATE_FILE}")
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
    url = f"{BASE_URL}/{SYMBOL}/{year:04d}/{month_idx:02d}/{day:02d}/{hour:02d}h_ticks.bi5"
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
    url = f"{BASE_URL}/{SYMBOL}/{y:04d}/{mi:02d}/{d:02d}/{h:02d}h_ticks.bi5"
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
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT, ttl_dns_cache=300)
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
    """All tradeable hour slots in month.
    Skips: all Saturday + Sunday before 21:00 UTC (gold market closed)."""
    mi = month - 1
    return [
        (year, mi, d, h)
        for d in range(1, calendar.monthrange(year, month)[1] + 1)
        for h in range(24)
        if not (date(year, month, d).weekday() == 5)  # skip Sat
        and not (date(year, month, d).weekday() == 6 and h < 21)  # skip Sun 00-20h
    ]


def weekday_slots(year: int, month: int) -> list:
    """Mon–Fri all 24h slots (used for repair gap detection)."""
    mi = month - 1
    return [
        (year, mi, d, h)
        for d in range(1, calendar.monthrange(year, month)[1] + 1)
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
    now = datetime.now()
    state = migrate_old_markers(load_state())

    print(f"Downloading {SYMBOL} from {START_YEAR} to present...\n")

    for year in range(START_YEAR, now.year + 1):
        m_start = START_MONTH if year == START_YEAR else 1
        m_end = now.month if year == now.year else 12

        for month in range(m_start, m_end + 1):
            key = f"{year}-{month:02d}"
            file_path = os.path.join(OUTPUT_DIR, f"{key}.parquet")
            is_past = not (year == now.year and month == now.month)
            entry = state.get(key)

            # ── Already complete → skip ────────────────────────────────────
            if is_past and entry and entry["missing_hours"] == 0:
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
