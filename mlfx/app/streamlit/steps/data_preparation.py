"""Step 2: Data Preparation."""

from __future__ import annotations

import io
import logging
from contextlib import redirect_stderr, redirect_stdout

import streamlit as st

from mlfx.app.streamlit.config import (
    PIVOT_ANCHOR_OPTIONS,
    PIVOT_TYPE_OPTIONS,
    TF_OPTIONS,
)
from mlfx.app.streamlit.navigation import WorkflowStep, navigation
from mlfx.app.streamlit.utils import load_config
from mlfx.config.paths import DEFAULT_PATHS
from mlfx.pipeline.feature_engineering import run_feature_pipeline
from mlfx.pipeline.labeling import run_label_pipeline
from mlfx.pipeline.resampling import resample_symbol_tf


def render_data_preparation_step() -> None:
    """Render Step 2: Data Preparation."""
    cfg = load_config()
    pl_cfg = cfg.get("pipeline", {})

    navigation.render_step_header()
    st.space("medium")

    symbol = st.session_state.get("symbol", "XAUUSD")

    with st.container(border=True):
        c1, c2 = st.columns([1, 1])
        with c1:
            pl_symbol = st.text_input("Symbol", value=symbol, key="pl_symbol")
            pl_tf = st.selectbox(
                "Timeframe",
                options=TF_OPTIONS,
                index=TF_OPTIONS.index(pl_cfg.get("timeframe", "1H"))
                if pl_cfg.get("timeframe", "1H") in TF_OPTIONS
                else 4,
                key="pl_tf",
            )
            atr_period = st.number_input(
                "ATR Period",
                value=pl_cfg.get("atr_period", 14),
                min_value=1,
                key="pl_atr_period",
            )
            atr_mult = st.number_input(
                "ATR Multiplier",
                value=float(pl_cfg.get("atr_multiplier", 0.5)),
                min_value=0.1,
                key="pl_atr_mult",
            )

        with c2:
            with st.container(gap="small"):
                st.subheader("Pipeline Steps")
                do_resample = st.checkbox("1. Resample (Tick → OHLCV)", value=True, key="pl_resample")
                do_features = st.checkbox("2. Features (OHLCV → matrix)", value=True, key="pl_features")
                do_labels = st.checkbox("3. Labels (ATR-based)", value=True, key="pl_labels")

            with st.expander("Pivot / Anchor nâng cao"):
                pivot_type = st.selectbox(
                    "Pivot Type",
                    options=PIVOT_TYPE_OPTIONS,
                    index=PIVOT_TYPE_OPTIONS.index(pl_cfg.get("pivot_type", "traditional"))
                    if pl_cfg.get("pivot_type", "traditional") in PIVOT_TYPE_OPTIONS
                    else 0,
                    key="pl_pivot_type",
                )
                pivot_anchor = st.selectbox(
                    "Pivot Anchor",
                    options=PIVOT_ANCHOR_OPTIONS,
                    index=PIVOT_ANCHOR_OPTIONS.index(pl_cfg.get("pivot_anchor", "daily"))
                    if pl_cfg.get("pivot_anchor", "daily") in PIVOT_ANCHOR_OPTIONS
                    else 0,
                    key="pl_pivot_anchor",
                )
                force_pl = st.checkbox("Force overwrite", value=False, key="pl_force")

    date_range = st.session_state.get("date_range")
    if date_range and isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        st.caption(f"📅 Global date range: {date_range[0]} → {date_range[1]}")

    # Pipeline results KPI (after completion)
    prep_data = navigation.get_step_data(WorkflowStep.DATA_PREPARATION)
    prep_stats = prep_data.get("stats") or {}
    if prep_stats:
        with st.container(border=True):
            st.subheader("📊 Pipeline Results")
            k1, k2, k3 = st.columns(3)
            k1.metric("OHLCV bars", f"{prep_stats.get('resample_bars', 0):,}", "resampled")
            k2.metric("Feature cols", prep_stats.get("feature_cols", 0), "engineered")
            k3.metric("Label bars", f"{prep_stats.get('label_bars', 0):,}", "labelled")

    # Data availability check
    pl_symbol = st.session_state.get("pl_symbol", symbol) or symbol
    pl_tf = st.session_state.get("pl_tf", pl_cfg.get("timeframe", "1H"))
    raw_dir = DEFAULT_PATHS.raw_data_dir(pl_symbol)
    ohlcv_dir = DEFAULT_PATHS.ohlcv_dir(pl_symbol, pl_tf)
    features_dir = DEFAULT_PATHS.features_dir(pl_symbol, pl_tf)
    raw_files = list(raw_dir.glob("????-??.parquet")) if raw_dir.exists() else []
    ohlcv_files = list(ohlcv_dir.glob("*.parquet")) if ohlcv_dir.exists() else []
    feature_files = list(features_dir.glob("*.parquet")) if features_dir.exists() else []

    with st.container(border=True):
        st.subheader("📋 Data Availability")
        c1, c2, c3 = st.columns(3)
        c1.metric("Raw months", len(raw_files), "tick data" if raw_files else "—")
        c2.metric("OHLCV months", len(ohlcv_files), f"{pl_tf}" if ohlcv_files else "—")
        c3.metric("Feature months", len(feature_files), "ready" if feature_files else "—")

    data_start = st.session_state.get("data_start")
    data_end = st.session_state.get("data_end")
    do_resample = st.session_state.get("pl_resample", True)
    do_features = st.session_state.get("pl_features", True)
    do_labels = st.session_state.get("pl_labels", True)
    if do_resample and not raw_files:
        st.warning("⚠️ No raw tick data found. Complete Data Loading first (download or use existing).")
    if do_resample and (data_start or data_end) and not (data_start and data_end):
        st.warning("⚠️ Date range partial: data_start/data_end should both be set from Data Loading.")
    if do_features and not ohlcv_files:
        st.warning("⚠️ No OHLCV data. Run Resample first or complete Data Loading.")
    if do_labels and not feature_files:
        st.warning("⚠️ No feature data. Run Features step first.")

    st.space("medium")
    with st.container(horizontal=True, horizontal_alignment="center"):
        if st.button("▶ Run Pipeline", key="btn_pipeline", type="primary"):
            with st.status("Running pipeline...", expanded=True) as status:
                logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
                logs: list[str] = []
                try:
                    data_start = st.session_state.get("data_start")
                    data_end = st.session_state.get("data_end")
                    resample_kwargs: dict = {
                        "symbol": pl_symbol or "XAUUSD",
                        "tf": pl_tf,
                        "force": force_pl,
                    }
                    if data_start is not None and data_end is not None:
                        resample_kwargs["start_year"] = data_start[0]
                        resample_kwargs["start_month"] = data_start[1]
                        resample_kwargs["end_year"] = data_end[0]
                        resample_kwargs["end_month"] = data_end[1]

                    pl_stats: dict = {}
                    _buf = io.StringIO()
                    with redirect_stdout(_buf), redirect_stderr(_buf):
                        if do_resample:
                            status.update(label="Step 1/3: Resampling data...")
                            st.write("Running resample_symbol_tf...")
                            resample_stats = resample_symbol_tf(**resample_kwargs)
                            msg = f"Resample: processed={resample_stats['processed']} skipped={resample_stats['skipped']} bars={resample_stats['total_bars']:,}"
                            logs.append(msg)
                            pl_stats["resample_bars"] = resample_stats["total_bars"]
                            st.write(f"✅ {msg}")

                        if do_features:
                            status.update(label="Step 2/3: Engineering features...")
                            st.write("Running run_feature_pipeline...")
                            feat_stats = run_feature_pipeline(
                                symbol=pl_symbol or "XAUUSD",
                                tf=pl_tf,
                                pivot_type=pivot_type,
                                pivot_anchor=pivot_anchor,
                                force=force_pl,
                            )
                            msg = f"Features: processed={feat_stats['processed']} bars={feat_stats['total_bars']:,} cols={feat_stats['total_features']}"
                            logs.append(msg)
                            pl_stats["feature_bars"] = feat_stats["total_bars"]
                            pl_stats["feature_cols"] = feat_stats["total_features"]
                            st.write(f"✅ {msg}")

                        if do_labels:
                            status.update(label="Step 3/3: Generating labels...")
                            st.write("Running run_label_pipeline...")
                            label_stats = run_label_pipeline(
                                symbol=pl_symbol or "XAUUSD",
                                tf=pl_tf,
                                atr_period=int(atr_period),
                                atr_mult=atr_mult,
                                force=force_pl,
                            )
                            msg = f"Labels: processed={label_stats['processed']} bars={label_stats['total_bars']:,}"
                            logs.append(msg)
                            pl_stats["label_bars"] = label_stats["total_bars"]
                            st.write(f"✅ {msg}")

                    navigation.mark_step_completed(WorkflowStep.DATA_PREPARATION)
                    navigation.store_step_data(
                        WorkflowStep.DATA_PREPARATION,
                        {
                            "symbol": pl_symbol,
                            "timeframe": pl_tf,
                            "pivot_type": pivot_type,
                            "pivot_anchor": pivot_anchor,
                            "atr_period": atr_period,
                            "atr_mult": atr_mult,
                            "stats": pl_stats,
                        },
                    )
                    navigation.invalidate_subsequent_steps(WorkflowStep.DATA_PREPARATION)
                    st.session_state["tf"] = pl_tf

                    for line in logs:
                        st.write(f"✅ {line}")

                    status.update(label="Pipeline completed successfully!", state="complete", expanded=False)
                    st.rerun()

                except Exception as e:
                    navigation.mark_step_error(WorkflowStep.DATA_PREPARATION, str(e))
                    status.update(label=f"Error: {str(e)}", state="error", expanded=True)
