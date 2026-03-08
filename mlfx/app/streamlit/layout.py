"""Layout components for MLFX Streamlit UI."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta

import streamlit as st

from mlfx.app.streamlit.config import (
    ASSETS_DIR,
    LABEL_OPTIONS,
    TF_OPTIONS,
)
from mlfx.app.streamlit.navigation import WorkflowStep, navigation


@st.dialog("Confirm reset")
def _confirm_reset_dialog() -> None:
    """Dialog to confirm workflow reset."""
    st.write("Are you sure you want to reset the workflow? All progress will be lost.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", width='stretch'):
            st.rerun()
    with col2:
        if st.button("Reset", type="primary", width='stretch'):
            st.session_state.clear()
            st.rerun()


def inject_css() -> None:
    """Inject custom CSS for workflow and chart styling."""
    glass_css_path = ASSETS_DIR / "glass_emerald.css"
    if glass_css_path.exists():
        st.markdown(f"<style>{glass_css_path.read_text()}</style>", unsafe_allow_html=True)
    workflow_css_path = ASSETS_DIR / "workflow_styles.css"
    if workflow_css_path.exists():
        st.markdown(f"<style>{workflow_css_path.read_text()}</style>", unsafe_allow_html=True)
    chart_css_path = ASSETS_DIR / "chart_styles.css"
    if chart_css_path.exists():
        st.markdown(f"<style>{chart_css_path.read_text()}</style>", unsafe_allow_html=True)


def render_sidebar() -> None:
    """Render the sidebar with global filters and quick navigation."""
    with st.sidebar:
        st.title("MLFX")
        st.caption("ICT-Based Price Prediction")
        st.divider()

        st.subheader("Global Filters")
        symbol = st.text_input(
            "Symbol",
            value=st.session_state.get("symbol", "XAUUSD"),
            key="sidebar_symbol",
        )
        if symbol:
            st.session_state["symbol"] = symbol

        tf = st.selectbox(
            "Timeframe",
            options=TF_OPTIONS,
            index=TF_OPTIONS.index(st.session_state.get("tf", "1H"))
            if st.session_state.get("tf", "1H") in TF_OPTIONS
            else 4,
            key="sidebar_tf",
        )
        st.session_state["tf"] = tf

        label_col = st.selectbox(
            "Label",
            options=LABEL_OPTIONS,
            index=LABEL_OPTIONS.index(st.session_state.get("label_col", "label_10"))
            if st.session_state.get("label_col", "label_10") in LABEL_OPTIONS
            else 1,
            key="sidebar_label_col",
        )
        st.session_state["label_col"] = label_col

        default_end = date.today()
        default_start = default_end - timedelta(days=365)
        data_start = st.session_state.get("data_start")
        data_end = st.session_state.get("data_end")
        if st.session_state.get("date_range") is not None:
            default_range = st.session_state["date_range"]
        elif data_start and data_end:
            sy, sm = data_start
            ey, em = data_end
            _, last_day = monthrange(ey, em)
            default_range = (date(sy, sm, 1), date(ey, em, last_day))
        else:
            default_range = (default_start, default_end)
        date_range = st.date_input(
            "Date range",
            value=default_range,
            key="sidebar_date_range",
        )
        if date_range and isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            st.session_state["date_range"] = date_range

        st.divider()
        st.subheader("Workflow Progress")
        progress = navigation.get_step_progress()
        st.progress(progress)
        st.write(f"Completed: {progress*100:.0f}%")
        st.divider()

        st.subheader("Quick Navigation")
        for step in WorkflowStep:
            step_info = navigation.steps[step]
            if navigation.can_navigate_to_step(step):
                if st.button(
                    f"{step_info['icon']} {step_info['title']}",
                    key=f"quick_nav_{step.value}",
                    width='stretch',
                ):
                    navigation.set_current_step(step)
                    st.rerun()

        with st.expander("Nâng cao"):
            st.caption("QA, drift detection, batch-predict (coming soon)")

        st.divider()
        st.subheader("Danger Zone")
        if st.button("Reset Workflow", type="primary", width='stretch', key="btn_reset_workflow"):
            _confirm_reset_dialog()

        st.divider()
        st.caption("App v1.x")


def render_navigation() -> None:
    """Render the horizontal workflow navigation bar."""
    navigation.render_navigation()
