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
    assert "MLFX consolidated CLI" in result.stdout


def test_mlfx_pipeline_help_smoke() -> None:
    result = _run_entrypoint("mlfx", "pipeline", "--help")
    assert result.returncode == 0, result.stderr
    assert "--skip-resample" in result.stdout


def test_mlfx_qa_help_smoke() -> None:
    result = _run_entrypoint("mlfx", "qa", "--help")
    assert result.returncode == 0, result.stderr
    assert "--asset-class" in result.stdout


def test_mlfx_tui_console_script_registration_smoke() -> None:
    result = _run_python(
        "from importlib import import_module; "
        "from importlib.metadata import entry_points; "
        "ep = next(ep for ep in entry_points(group='console_scripts') if ep.name == 'mlfx-tui'); "
        "module_name, attr_name = ep.value.split(':', 1); "
        "target = getattr(import_module(module_name), attr_name); "
        "print(ep.value); "
        "print(callable(target))"
    )
    assert result.returncode == 0, result.stderr
    assert "mlfx.app.tui.main:main" in result.stdout
    assert "True" in result.stdout
