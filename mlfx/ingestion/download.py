"""Download implementation for the Dukascopy ingestion pipeline."""

from __future__ import annotations

import asyncio
import calendar
from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
import lzma
from pathlib import Path
import random
import struct
import time
import urllib.error
import urllib.request

import aiohttp
import polars as pl

from mlfx.config.paths import DEFAULT_PATHS, ProjectPaths

BASE_URL = "https://datafeed.dukascopy.com/datafeed"


@dataclass(frozen=True)
class DownloadRuntimeConfig:
    symbol: str
    start_year: int
    start_month: int
    asset_class: str
    concurrency: int
    force: bool
    output_dir: Path
    state_file: Path


def build_download_config(
    symbol: str,
    start_year: int,
    start_month: int,
    asset_class: str,
    concurrency: int,
    force: bool,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> DownloadRuntimeConfig:
    """Build an immutable runtime config for the downloader."""
    return DownloadRuntimeConfig(
        symbol=symbol,
        start_year=start_year,
        start_month=start_month,
        asset_class=asset_class,
        concurrency=concurrency,
        force=force,
        output_dir=paths.raw_data_dir(symbol),
        state_file=paths.state_file(symbol),
    )


def load_state(state_file: Path) -> dict[str, dict[str, int]]:
    """Read the downloaded-month tracking state from disk."""
    if state_file.exists():
        with state_file.open() as handle:
            data = json.load(handle)
        if isinstance(data, list):
            migrated = {key: {"rows": -1, "missing_hours": 0} for key in data}
            save_state(state_file, migrated)
            print(f"Migrated state file to new format ({len(migrated)} entries)")
            return migrated
        return data
    return {}


def save_state(state_file: Path, state: dict[str, dict[str, int]]) -> None:
    """Persist the month-tracking state dictionary as JSON."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("w") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)


def migrate_old_markers(
    output_dir: Path,
    state_file: Path,
    state: dict[str, dict[str, int]],
) -> dict[str, dict[str, int]]:
    """Absorb old `*.parquet.complete` files into the JSON state file."""
    if not output_dir.exists():
        return state

    old_markers = list(output_dir.glob("*.parquet.complete"))
    for marker in old_markers:
        key = marker.name.replace(".parquet.complete", "")
        state.setdefault(key, {"rows": -1, "missing_hours": 0})
        marker.unlink()
    if old_markers:
        print(f"Migrated {len(old_markers)} old markers -> {state_file}")
    return state


def parse_hour(raw: bytes, year: int, month: int, day: int, hour: int) -> pl.DataFrame | None:
    """Decode raw Dukascopy bi5 bytes into a tick dataframe."""
    if not raw:
        return None

    base_ms = int(datetime(year, month, day, hour, tzinfo=timezone.utc).timestamp() * 1000)
    chunk = 20
    records = [
        (
            base_ms + struct.unpack_from(">I", raw, i)[0],
            struct.unpack_from(">I", raw, i + 4)[0] / 1000.0,
            struct.unpack_from(">I", raw, i + 8)[0] / 1000.0,
            struct.unpack_from(">f", raw, i + 12)[0],
            struct.unpack_from(">f", raw, i + 16)[0],
        )
        for i in range(0, len(raw) - chunk + 1, chunk)
    ]
    if not records:
        return None
    return pl.DataFrame(
        records,
        schema=["timestamp_ms", "ask", "bid", "ask_volume", "bid_volume"],
        orient="row",
    )


def to_datetime_df(df: pl.DataFrame) -> pl.DataFrame:
    """Convert an epoch-based tick dataframe into canonical timestamp columns."""
    return df.with_columns(
        pl.from_epoch("timestamp_ms", time_unit="ms").alias("timestamp")
    ).select(["timestamp", "ask", "bid", "ask_volume", "bid_volume"])


def fetch_hour(
    config: DownloadRuntimeConfig,
    year: int,
    month_idx: int,
    day: int,
    hour: int,
    retries: int = 4,
    timeout: int = 30,
) -> bytes | None | str:
    """Synchronously fetch a single hour. Returns bytes, None, or `TIMEOUT`."""
    url = (
        f"{BASE_URL}/{config.symbol}/{year:04d}/{month_idx:02d}/{day:02d}/{hour:02d}h_ticks.bi5"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return lzma.decompress(response.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if attempt < retries - 1:
                time.sleep((2**attempt) + random.random())
        except Exception:
            if attempt < retries - 1:
                time.sleep((2**attempt) + random.random())
    return "TIMEOUT"


async def _fetch_one(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    config: DownloadRuntimeConfig,
    year: int,
    month_idx: int,
    day: int,
    hour: int,
    month: int,
) -> pl.DataFrame | None | str:
    """Fetch, decompress, and parse one hourly file asynchronously."""
    url = (
        f"{BASE_URL}/{config.symbol}/{year:04d}/{month_idx:02d}/{day:02d}/{hour:02d}h_ticks.bi5"
    )
    async with semaphore:
        for attempt in range(4):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 404:
                        return None
                    if response.status in (429, 503):
                        await asyncio.sleep(min(2**attempt, 16) + random.random())
                        continue
                    compressed = await response.read()
                try:
                    raw = lzma.decompress(compressed)
                except lzma.LZMAError:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                return parse_hour(raw, year, month, day, hour)
            except (asyncio.TimeoutError, aiohttp.ClientError):
                if attempt < 3:
                    await asyncio.sleep(min(2**attempt, 8) * 0.5 + random.random())
    return "TIMEOUT"


async def _fetch_hours_async(
    config: DownloadRuntimeConfig,
    slots: list[tuple[int, int, int, int]],
    month: int,
) -> tuple[list[pl.DataFrame], int]:
    """Execute asynchronous downloads over multiple hourly slots."""
    semaphore = asyncio.Semaphore(config.concurrency)
    connector = aiohttp.TCPConnector(limit=config.concurrency, ttl_dns_cache=300)
    headers = {"User-Agent": "Mozilla/5.0"}

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        results = await asyncio.gather(
            *[
                _fetch_one(session, semaphore, config, year, month_idx, day, hour, month)
                for year, month_idx, day, hour in slots
            ]
        )

    frames: list[pl.DataFrame] = []
    timed_out = 0
    for result in results:
        if result is None:
            continue
        if isinstance(result, str):
            timed_out += 1
            continue
        frames.append(result)
    return frames, timed_out


def fetch_hours(
    config: DownloadRuntimeConfig,
    slots: list[tuple[int, int, int, int]],
    month: int,
) -> tuple[list[pl.DataFrame], int]:
    """Public sync interface that runs the async downloader under the hood."""
    if not slots:
        return [], 0
    frames, timed_out = asyncio.run(_fetch_hours_async(config, slots, month))
    if timed_out:
        print(f"  Warning: {timed_out} hours timed out (will retry on next run)", flush=True)
    return frames, timed_out


def all_slots(config: DownloadRuntimeConfig, year: int, month: int) -> list[tuple[int, int, int, int]]:
    """Return all tradeable hour slots for a month."""
    month_idx = month - 1
    days_in_month = calendar.monthrange(year, month)[1]
    if config.asset_class == "crypto":
        return [
            (year, month_idx, day, hour)
            for day in range(1, days_in_month + 1)
            for hour in range(24)
        ]
    return [
        (year, month_idx, day, hour)
        for day in range(1, days_in_month + 1)
        for hour in range(24)
        if date(year, month, day).weekday() != 5
        and not (date(year, month, day).weekday() == 6 and hour < 21)
    ]


def weekday_slots(
    config: DownloadRuntimeConfig,
    year: int,
    month: int,
) -> list[tuple[int, int, int, int]]:
    """Return Mon-Fri slots, or 24/7 slots for crypto, for repair checks."""
    month_idx = month - 1
    days_in_month = calendar.monthrange(year, month)[1]
    if config.asset_class == "crypto":
        return [
            (year, month_idx, day, hour)
            for day in range(1, days_in_month + 1)
            for hour in range(24)
        ]
    return [
        (year, month_idx, day, hour)
        for day in range(1, days_in_month + 1)
        if date(year, month, day).weekday() < 5
        for hour in range(24)
    ]


def repair_month(
    config: DownloadRuntimeConfig,
    year: int,
    month: int,
    file_path: Path,
) -> tuple[int, int]:
    """Detect and patch missing weekday-hour slots in an existing parquet file."""
    df = pl.read_parquet(file_path)
    covered = set(
        df.with_columns(
            [
                pl.col("timestamp").dt.day().alias("_day"),
                pl.col("timestamp").dt.hour().alias("_hour"),
            ]
        )
        .select(["_day", "_hour"])
        .unique()
        .rows()
    )

    missing = [
        (year, month_idx, day, hour)
        for year, month_idx, day, hour in weekday_slots(config, year, month)
        if (day, hour) not in covered
    ]
    if not missing:
        return len(df), 0

    print(f"  -> {len(missing)} weekday-hour slots missing, fetching...", flush=True)
    new_frames, _ = fetch_hours(config, missing, month)
    if new_frames:
        added = sum(len(frame) for frame in new_frames)
        df = (
            pl.concat([df] + [to_datetime_df(frame) for frame in new_frames])
            .unique(subset=["timestamp"], keep="first")
            .sort("timestamp")
        )
        df.write_parquet(file_path)
        print(f"  -> Patched +{added:,} rows")

    covered_after = set(
        df.with_columns(
            [
                pl.col("timestamp").dt.day().alias("_day"),
                pl.col("timestamp").dt.hour().alias("_hour"),
            ]
        )
        .select(["_day", "_hour"])
        .unique()
        .rows()
    )
    still_missing = sum(
        1
        for _, _, day, hour in weekday_slots(config, year, month)
        if (day, hour) not in covered_after
    )
    return len(df), still_missing


def run_download_job(
    symbol: str,
    asset_class: str,
    start_year: int,
    start_month: int,
    concurrency: int,
    force: bool,
    *,
    paths: ProjectPaths = DEFAULT_PATHS,
) -> None:
    """Download, validate, and repair monthly tick parquet files for one symbol."""
    config = build_download_config(
        symbol,
        start_year,
        start_month,
        asset_class,
        concurrency,
        force,
        paths=paths,
    )
    config.output_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    state = migrate_old_markers(
        config.output_dir,
        config.state_file,
        load_state(config.state_file),
    )

    for year in range(config.start_year, now.year + 1):
        month_start = config.start_month if year == config.start_year else 1
        month_end = now.month if year == now.year else 12
        for month in range(month_start, month_end + 1):
            key = f"{year}-{month:02d}"
            file_path = config.output_dir / f"{key}.parquet"
            is_past = not (year == now.year and month == now.month)
            entry = state.get(key)

            if (
                is_past
                and entry
                and entry["missing_hours"] == 0
                and file_path.exists()
                and not config.force
            ):
                print(f"Skip     {key}  rows={entry['rows']:>10,}  missing=0")
                continue

            if file_path.exists():
                print(f"Checking {key} ...")
                rows, missing = repair_month(config, year, month, file_path)
                flag = "full" if missing == 0 else f"{missing} hrs missing"
                print(f"   {key}  rows={rows:>10,}  {flag}")
                if is_past:
                    state[key] = {"rows": rows, "missing_hours": missing}
                    save_state(config.state_file, state)
                continue

            print(f"Download {key} ...", end=" ", flush=True)
            frames, timed_out = fetch_hours(config, all_slots(config, year, month), month)
            if frames:
                df = to_datetime_df(pl.concat(frames).sort("timestamp_ms"))
                df.write_parquet(file_path)
                print(f"Saved {len(df):,} rows.")
            else:
                df = None
                print("No data found.")

            if is_past:
                rows = len(df) if df is not None else 0
                state[key] = {"rows": rows, "missing_hours": timed_out}
                save_state(config.state_file, state)
