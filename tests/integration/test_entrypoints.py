from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_entrypoint(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["RATTLER_CACHE_DIR"] = str(REPO_ROOT / ".pixi-cache")
    return subprocess.run(
        ["pixi", "run", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_python(code: str) -> subprocess.CompletedProcess[str]:
    return _run_entrypoint("python", "-c", code)


def test_mlfx_help_smoke() -> None:
    result = _run_entrypoint("mlfx", "--help")
    assert result.returncode == 0, result.stderr
    assert "MLFX — Machine Learning for Forex. Terminal-first workflow." in result.stdout


def test_mlfx_pipeline_help_smoke() -> None:
    result = _run_entrypoint("mlfx", "pipeline", "--help")
    assert result.returncode == 0, result.stderr
    assert "--skip-resample" in result.stdout


def test_mlfx_qa_help_smoke() -> None:
    result = _run_entrypoint("mlfx", "qa", "--help")
    assert result.returncode == 0, result.stderr
    assert "--asset-class" in result.stdout


def test_mlfx_benchmark_help_smoke() -> None:
    result = _run_entrypoint("mlfx", "benchmark", "--help")
    assert result.returncode == 0, result.stderr
    assert "--backends" in result.stdout
