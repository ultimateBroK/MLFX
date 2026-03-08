"""Layout components for MLFX Streamlit UI."""

from __future__ import annotations

import streamlit as st

from mlfx.app.streamlit.config import ASSETS_DIR
from mlfx.app.streamlit.navigation import WorkflowStep, navigation


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
    """Render the sidebar with progress and quick navigation."""
    with st.sidebar:
        st.title("MLFX")
        st.caption("ICT-Based Price Prediction")
        st.divider()
        st.subheader("🔄 Workflow Progress")
        progress = navigation.get_step_progress()
        st.progress(progress)
        st.write(f"Completed: {progress*100:.0f}%")
        st.divider()
        st.subheader("⚙️ Global Settings")
        current_step = navigation.get_current_step()
        st.info(f"Current Step: {navigation.steps[current_step]['title']}")
        st.subheader("🧭 Quick Navigation")
        for step in WorkflowStep:
            step_info = navigation.steps[step]
            if navigation.can_navigate_to_step(step):
                if st.button(
                    f"{step_info['icon']} {step_info['title']}",
                    key=f"quick_nav_{step.value}",
                    use_container_width=True,
                ):
                    navigation.set_current_step(step)
                    st.rerun()

        st.divider()
        st.subheader("⚠️ Danger Zone")
        if st.button("♻️ Reset Workflow", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def render_navigation() -> None:
    """Render the horizontal workflow navigation bar."""
    navigation.render_navigation()
