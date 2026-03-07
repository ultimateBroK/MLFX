from __future__ import annotations

from pathlib import Path


class TestDownloadConfigHelpers:
    def test_build_download_config_uses_project_paths(self, tmp_path: Path):
        from mlfx.config.paths import ProjectPaths
        from mlfx.ingestion.download import build_download_config

        paths = ProjectPaths(project_root=tmp_path)
        config = build_download_config(
            symbol="BTCUSD",
            start_year=2024,
            start_month=2,
            asset_class="crypto",
            concurrency=8,
            force=True,
            paths=paths,
        )

        assert config.symbol == "BTCUSD"
        assert config.output_dir == tmp_path / "data" / "raw" / "BTCUSD"
        assert config.state_file == tmp_path / "data" / "raw" / "BTCUSD" / "completed_months.json"

    def test_load_state_migrates_legacy_marker_format(self, tmp_path: Path):
        from mlfx.ingestion.download import load_state

        state_file = tmp_path / "completed_months.json"
        state_file.write_text('["2024-01", "2024-02"]')

        state = load_state(state_file)

        assert state["2024-01"]["missing_hours"] == 0
        assert state["2024-02"]["rows"] == -1


class TestDownloadSlotPolicy:
    def test_fx_slots_skip_weekends(self, tmp_path: Path):
        from mlfx.config.paths import ProjectPaths
        from mlfx.ingestion.download import all_slots, build_download_config

        config = build_download_config(
            symbol="XAUUSD",
            start_year=2024,
            start_month=1,
            asset_class="fx",
            concurrency=4,
            force=False,
            paths=ProjectPaths(project_root=tmp_path),
        )
        slots = all_slots(config, 2024, 1)

        assert (2024, 0, 6, 12) not in slots
        assert (2024, 0, 7, 12) not in slots

    def test_crypto_slots_include_weekends(self, tmp_path: Path):
        from mlfx.config.paths import ProjectPaths
        from mlfx.ingestion.download import all_slots, build_download_config

        config = build_download_config(
            symbol="BTCUSD",
            start_year=2024,
            start_month=1,
            asset_class="crypto",
            concurrency=4,
            force=False,
            paths=ProjectPaths(project_root=tmp_path),
        )
        slots = all_slots(config, 2024, 1)

        assert (2024, 0, 6, 12) in slots
        assert (2024, 0, 7, 12) in slots
