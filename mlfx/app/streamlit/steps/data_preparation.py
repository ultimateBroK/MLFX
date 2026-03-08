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
from mlfx.pipeline.feature_engineering import run_feature_pipeline
from mlfx.pipeline.labeling import run_label_pipeline
from mlfx.pipeline.resampling import resample_symbol_tf


def render_data_preparation_step() -> None:
    """Render Step 2: Data Preparation."""
    cfg = load_config()
    pl_cfg = cfg.get("pipeline", {})

    navigation.render_step_header()

    symbol = st.session_state.get("symbol", "XAUUSD")

    c1, c2 = st.columns([1, 1])
    with c1:
        pl_symbol = st.text_input("Symbol", value=symbol, key="pl_symbol")
        pl_tf = st.selectbox(
            "Timeframe",
            options=TF_OPTIONS,
            index=TF_OPTIONS.index(pl_cfg.get("timeframe", "1H")),
            key="pl_tf",
        )
        pivot_type = st.selectbox(
            "Pivot Type",
            options=PIVOT_TYPE_OPTIONS,
            index=PIVOT_TYPE_OPTIONS.index(pl_cfg.get("pivot_type", "traditional")),
            key="pl_pivot_type",
        )
        pivot_anchor = st.selectbox(
            "Pivot Anchor",
            options=PIVOT_ANCHOR_OPTIONS,
            index=PIVOT_ANCHOR_OPTIONS.index(pl_cfg.get("pivot_anchor", "daily")),
            key="pl_pivot_anchor",
        )

    with c2:
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
        force_pl = st.checkbox("Force overwrite", value=False, key="pl_force")

        st.subheader("Pipeline Steps")
        do_resample = st.checkbox("1. Resample (Tick → OHLCV)", value=True, key="pl_resample")
        do_features = st.checkbox("2. Features (OHLCV → matrix)", value=True, key="pl_features")
        do_labels = st.checkbox("3. Labels (ATR-based)", value=True, key="pl_labels")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶ Run Pipeline", key="btn_pipeline", type="primary", use_container_width=True):
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

                    _buf = io.StringIO()
                    with redirect_stdout(_buf), redirect_stderr(_buf):
                        if do_resample:
                            status.update(label="Step 1/3: Resampling data...")
                            st.write("Running resample_symbol_tf...")
                            stats = resample_symbol_tf(**resample_kwargs)
                            msg = f"Resample: processed={stats['processed']} skipped={stats['skipped']} bars={stats['total_bars']:,}"
                            logs.append(msg)
                            st.write(f"✅ {msg}")

                        if do_features:
                            status.update(label="Step 2/3: Engineering features...")
                            st.write("Running run_feature_pipeline...")
                            stats = run_feature_pipeline(
                                symbol=pl_symbol or "XAUUSD",
                                tf=pl_tf,
                                pivot_type=pivot_type,
                                pivot_anchor=pivot_anchor,
                                force=force_pl,
                            )
                            msg = f"Features: processed={stats['processed']} bars={stats['total_bars']:,} cols={stats['total_features']}"
                            logs.append(msg)
                            st.write(f"✅ {msg}")

                        if do_labels:
                            status.update(label="Step 3/3: Generating labels...")
                            st.write("Running run_label_pipeline...")
                            stats = run_label_pipeline(
                                symbol=pl_symbol or "XAUUSD",
                                tf=pl_tf,
                                atr_period=int(atr_period),
                                atr_mult=atr_mult,
                                force=force_pl,
                            )
                            msg = f"Labels: processed={stats['processed']} bars={stats['total_bars']:,}"
                            logs.append(msg)
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
