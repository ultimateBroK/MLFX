"""Shared utilities for MLFX Streamlit UI."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout

import streamlit as st

from mlfx.app.streamlit.config import CONFIG_FILE
from mlfx.app.streamlit.navigation import WorkflowStep, navigation
from mlfx.config.settings import load_config as shared_load_config


def load_config() -> dict:
    """Load config.toml via shared config layer."""
    return shared_load_config(CONFIG_FILE)


def run_with_capture(func, *args, **kwargs):
    """Run function capturing stdout/stderr, return (result, log_output)."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            result = func(*args, **kwargs)
        return result, buf.getvalue()
    except Exception as e:
        return None, buf.getvalue() + f"\nError: {e}"


def store_data_range_and_complete(
    symbol: str,
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    asset_class: str = "fx",
) -> None:
    """Store date range in session and mark step complete."""
    st.session_state["symbol"] = symbol
    st.session_state["data_start"] = (start_year, start_month)
    st.session_state["data_end"] = (end_year, end_month)
    st.session_state["asset_class"] = asset_class
    navigation.mark_step_completed(WorkflowStep.DATA_LOADING)
    navigation.store_step_data(WorkflowStep.DATA_LOADING, {
        "symbol": symbol,
        "asset_class": asset_class,
        "start_year": start_year,
        "start_month": start_month,
        "end_year": end_year,
        "end_month": end_month,
    })
    navigation.invalidate_subsequent_steps(WorkflowStep.DATA_LOADING)
