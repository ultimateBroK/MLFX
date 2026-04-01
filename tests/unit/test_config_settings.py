"""tests/unit/test_config_settings.py
======================================
Unit tests for settings helpers and ServingSettings configuration.
"""
from __future__ import annotations

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# settings.py helpers
# ---------------------------------------------------------------------------

class TestSettingsHelpers:
    def test_load_config_includes_profiles_mapping(self, tmp_path: Path):
        from mlfx.config.settings import load_config

        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
[profiles.research.train]
backend = "mlf"

[profiles.research.benchmark]
backends = ["mlf", "sgd"]
"""
        )

        cfg = load_config(cfg_file)
        assert "research" in cfg.profiles
        assert cfg.profiles["research"].train is not None
        assert cfg.profiles["research"].train.backend == "mlf"
        assert cfg.profiles["research"].benchmark is not None
        assert cfg.profiles["research"].benchmark.backends == ["mlf", "sgd"]

    def test_resolve_profile_section_returns_single_section(self, tmp_path: Path):
        from mlfx.cli.resolve import resolve_profile_section
        from mlfx.config.settings import load_config

        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
[profiles.research.train]
backend = "mlf"

[profiles.oos.evaluate]
eval_start = "20250101"
"""
        )

        cfg = load_config(cfg_file)
        section = resolve_profile_section(cfg, "research", "train")
        assert section["backend"] == "mlf"

    def test_resolve_profile_section_raises_for_unknown_profile(self, tmp_path: Path):
        from mlfx.cli.resolve import resolve_profile_section
        from mlfx.config.settings import load_config

        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
[profiles.research.train]
backend = "mlf"
"""
        )

        cfg = load_config(cfg_file)
        with pytest.raises(ValueError, match="Unknown profile"):
            resolve_profile_section(cfg, "missing", "train")

    def test_resolve_profile_section_handles_missing_and_none(self, tmp_path: Path):
        from mlfx.cli.resolve import resolve_profile_section
        from mlfx.config.settings import load_config

        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """
[profiles.research.train]
backend = "mlf"
"""
        )
        cfg = load_config(cfg_file)

        assert resolve_profile_section(cfg, None, "train") == {}

        with pytest.raises(ValueError, match="does not define a 'benchmark' section"):
            resolve_profile_section(cfg, "research", "benchmark")


# ---------------------------------------------------------------------------
# ServingSettings env-var overrides
# ---------------------------------------------------------------------------

class TestServingSettings:
    def test_default_log_level(self):
        from mlfx.config.schema import ServingSettings

        s = ServingSettings()
        assert s.log_level == "INFO"

    def test_env_override_log_level(self, monkeypatch):
        monkeypatch.setenv("MLFX_LOG_LEVEL", "DEBUG")
        # Re-instantiate to pick up the env var.
        from mlfx.config.schema import ServingSettings  # noqa: PLC0415

        s = ServingSettings()
        assert s.log_level == "DEBUG"

    def test_env_override_data_root(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MLFX_DATA_ROOT", str(tmp_path / "data"))
        from mlfx.config.schema import ServingSettings  # noqa: PLC0415

        s = ServingSettings()
        assert str(s.data_root) == str(tmp_path / "data")

    def test_env_override_propagates_to_get_project_paths(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MLFX_DATA_ROOT", str(tmp_path / "override_data"))
        from mlfx.config.paths import get_project_paths  # noqa: PLC0415
        from mlfx.config.schema import ServingSettings  # noqa: PLC0415

        paths = get_project_paths(ServingSettings())
        assert paths.data_root == (tmp_path / "override_data").resolve()
