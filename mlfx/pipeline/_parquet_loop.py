"""Shared parquet file processing loop for pipeline stages."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq


def process_parquet_files(
    in_dir: Path,
    out_dir: Path,
    transform_fn: Callable[[pl.DataFrame], pl.DataFrame],
    *,
    force: bool = False,
    glob_pattern: str = "*.parquet",
    compression: str = "snappy",
    on_processed: Callable[[pl.DataFrame], dict] | None = None,
) -> dict[str, int | list]:
    """Process parquet files: read, transform, write. Skip existing unless force.

    Returns stats dict with processed, skipped, total_bars. If on_processed is
    provided, its return value is merged into stats for each processed file.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    stats: dict[str, int | list] = {"processed": 0, "skipped": 0, "total_bars": 0}
    parquet_files = sorted(in_dir.glob(glob_pattern)) if in_dir.exists() else []

    for in_file in parquet_files:
        out_file = out_dir / in_file.name
        if out_file.exists() and not force:
            stats["skipped"] += 1  # type: ignore[operator]
            continue

        df = pl.read_parquet(in_file)
        if df.is_empty():
            continue

        result = transform_fn(df)
        if result.is_empty():
            continue

        pq.write_table(result.to_arrow(), str(out_file), compression=compression)
        stats["processed"] += 1  # type: ignore[operator]
        stats["total_bars"] += len(result)  # type: ignore[operator]
        if on_processed:
            stats.update(on_processed(result))

    return stats
