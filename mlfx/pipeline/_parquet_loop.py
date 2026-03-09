"""Shared parquet file processing loop for pipeline stages."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq


def _file_sha256(path: Path) -> str:
    """Return the hex-encoded SHA-256 digest of *path* using 64 KiB read chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


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
        hash_file = out_dir / (in_file.stem + ".sha256")
        if out_file.exists() and not force:
            # Skip only when the source file hash matches the recorded sidecar.
            if hash_file.exists() and hash_file.read_text().strip() == _file_sha256(in_file):
                stats["skipped"] += 1  # type: ignore[operator]
                continue
            # Hash mismatch — source has changed, reprocess.

        df = pl.read_parquet(in_file)
        if df.is_empty():
            continue

        result = transform_fn(df)
        if result.is_empty():
            continue

        pq.write_table(result.to_arrow(), str(out_file), compression=compression)
        hash_file.write_text(_file_sha256(in_file) + "\n")
        stats["processed"] += 1  # type: ignore[operator]
        stats["total_bars"] += len(result)  # type: ignore[operator]
        if on_processed:
            stats.update(on_processed(result))

    return stats
