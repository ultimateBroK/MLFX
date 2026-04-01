from __future__ import annotations

import json
from pathlib import Path


def test_research_notebook_exists_and_has_expected_sections() -> None:
    notebook_path = Path("notebooks/mlfx_research_walkthrough.ipynb")
    assert notebook_path.exists()

    notebook = json.loads(notebook_path.read_text())
    assert notebook["nbformat"] == 4
    assert notebook["nbformat_minor"] >= 5

    cells = notebook["cells"]
    assert cells, "notebook must contain cells"

    joined_sources = "\n".join(
        "".join(cell.get("source", []))
        for cell in cells
    )

    assert "load_labelled_dataset" in joined_sources
    assert "predictions.parquet" in joined_sources
    assert "_trades.parquet" in joined_sources
    assert "get_equity_curve_figure" in joined_sources
    assert "select_numeric_feature_columns" in joined_sources


def test_research_notebook_starts_with_markdown_title() -> None:
    notebook_path = Path("notebooks/mlfx_research_walkthrough.ipynb")
    notebook = json.loads(notebook_path.read_text())

    first_cell = notebook["cells"][0]
    assert first_cell["cell_type"] == "markdown"
    first_cell_source = "".join(first_cell["source"])
    assert "MLFX Research Walkthrough" in first_cell_source


def test_visual_analytics_notebook_exists_and_references_metrics_predictions() -> None:
    notebook_path = Path("notebooks/mlfx_visual_analytics.ipynb")
    assert notebook_path.exists()

    notebook = json.loads(notebook_path.read_text())
    joined_sources = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
    )

    assert "registry.json" in joined_sources
    assert ".metrics.json" in joined_sources
    assert "predictions.parquet" in joined_sources
    assert "_trades.parquet" in joined_sources
    assert "compute_metrics" in joined_sources
    assert "metrics_log.jsonl" in joined_sources


def test_visual_analytics_notebook_has_markdown_title() -> None:
    notebook_path = Path("notebooks/mlfx_visual_analytics.ipynb")
    notebook = json.loads(notebook_path.read_text())
    first_cell = notebook["cells"][0]
    assert first_cell["cell_type"] == "markdown"
    assert "MLFX Visual Analytics Notebook" in "".join(first_cell["source"])
