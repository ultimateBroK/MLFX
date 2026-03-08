"""Step 1: Data Loading."""

from __future__ import annotations

import logging
from datetime import datetime

import streamlit as st

from mlfx.app.streamlit.config import ASSET_CLASS_OPTIONS
from mlfx.app.streamlit.navigation import WorkflowStep, navigation
from mlfx.app.streamlit.utils import load_config, run_with_capture, store_data_range_and_complete
from mlfx.ingestion.download import list_available_raw_months, run_download_job


def render_data_loading_step() -> None:
    """Render Step 1: Data Loading."""
    cfg = load_config()
    dl_cfg = cfg.get("download", {})
    now = datetime.now()

    navigation.render_step_header()

    dl_mode = st.radio(
        "Data source",
        options=["Download new data", "Use existing data"],
        key="dl_mode",
        horizontal=True,
    )

    dl_symbol = st.text_input(
        "Symbol",
        value=st.session_state.get("symbol", dl_cfg.get("symbol", "XAUUSD")),
        key="dl_symbol",
    )
    symbol = dl_symbol or "XAUUSD"

    if dl_mode == "Download new data":
        asset_class = st.selectbox(
            "Asset Class",
            options=ASSET_CLASS_OPTIONS,
            index=0 if dl_cfg.get("asset_class", "fx") == "fx" else 1,
            key="dl_asset_class",
        )
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Date range")
            start_year = st.number_input(
                "Start Year",
                value=dl_cfg.get("start_year", 2015),
                min_value=2000,
                key="dl_start_year",
            )
            start_month = st.number_input(
                "Start Month",
                value=dl_cfg.get("start_month", 1),
                min_value=1,
                max_value=12,
                key="dl_start_month",
            )
            end_year = st.number_input(
                "End Year",
                value=now.year,
                min_value=2000,
                key="dl_end_year",
            )
            end_month = st.number_input(
                "End Month",
                value=now.month,
                min_value=1,
                max_value=12,
                key="dl_end_month",
            )
        with c2:
            concurrency = st.number_input(
                "Concurrency",
                value=dl_cfg.get("concurrency", 20),
                min_value=1,
                key="dl_concurrency",
            )
            force_dl = st.checkbox("Force re-verify", value=False, key="dl_force")
            skip_current = st.checkbox(
                "Skip current month (faster when up-to-date)",
                value=False,
                key="dl_skip_current",
            )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("▶ Start Data Loading", key="btn_download", type="primary", use_container_width=True):
                with st.status("Loading data...", expanded=True) as status:
                    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
                    try:
                        result, log = run_with_capture(
                            run_download_job,
                            symbol=symbol,
                            asset_class=asset_class,
                            start_year=int(start_year),
                            start_month=int(start_month),
                            concurrency=int(concurrency),
                            force=force_dl,
                            end_year=int(end_year),
                            end_month=int(end_month),
                            skip_current_month=skip_current,
                        )

                        if result is not None:
                            store_data_range_and_complete(
                                symbol=symbol,
                                start_year=int(start_year),
                                start_month=int(start_month),
                                end_year=int(end_year),
                                end_month=int(end_month),
                                asset_class=asset_class,
                            )
                            status.update(label="Data loading completed successfully!", state="complete", expanded=False)
                            st.rerun()
                        else:
                            navigation.mark_step_error(WorkflowStep.DATA_LOADING, "Failed to load data")
                            status.update(label="Failed to load data", state="error", expanded=True)

                        if log:
                            st.code(log, language="text")

                    except Exception as e:
                        navigation.mark_step_error(WorkflowStep.DATA_LOADING, str(e))
                        status.update(label=f"Error: {str(e)}", state="error", expanded=True)

    else:
        st.subheader("Use existing data")
        last_scanned = st.session_state.get("_last_scanned_symbol")
        
        # Auto-scan immediately without requiring a button click
        if last_scanned != symbol:
            with st.status(f"Scanning available data for {symbol}...", expanded=True) as status:
                months = list_available_raw_months(symbol)
                st.session_state["_available_months"] = months
                st.session_state["_last_scanned_symbol"] = symbol
                status.update(label="Scan complete", state="complete", expanded=False)

        available = st.session_state.get("_available_months", [])
        if available:
            min_ym = min(available)
            max_ym = max(available)
            st.info(f"Found {len(available)} months: {min_ym[0]}-{min_ym[1]:02d} to {max_ym[0]}-{max_ym[1]:02d}")

            c1, c2 = st.columns(2)
            with c1:
                start_year = st.number_input(
                    "Start Year",
                    value=min_ym[0],
                    min_value=min_ym[0],
                    max_value=max_ym[0],
                    key="ex_start_year",
                )
                start_month = st.number_input(
                    "Start Month",
                    value=min_ym[1],
                    min_value=1,
                    max_value=12,
                    key="ex_start_month",
                )
            with c2:
                end_year = st.number_input(
                    "End Year",
                    value=max_ym[0],
                    min_value=min_ym[0],
                    max_value=max_ym[0],
                    key="ex_end_year",
                )
                end_month = st.number_input(
                    "End Month",
                    value=max_ym[1],
                    min_value=1,
                    max_value=12,
                    key="ex_end_month",
                )

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Confirm & proceed", key="btn_confirm_existing", type="primary", use_container_width=True):
                    store_data_range_and_complete(
                        symbol=symbol,
                        start_year=int(start_year),
                        start_month=int(start_month),
                        end_year=int(end_year),
                        end_month=int(end_month),
                        asset_class=dl_cfg.get("asset_class", "fx"),
                    )
                    st.success("✅ Using existing data. Proceed to Data Preparation.")
                    st.rerun()
        else:
            st.warning(f"No existing data found for {symbol}. Switch to 'Download new data' to fetch it.")
