"""MLFX Streamlit UI - Main entrypoint."""

from __future__ import annotations

import streamlit as st

from mlfx.app.streamlit.layout import inject_css, render_navigation, render_sidebar
from mlfx.app.streamlit.navigation import WorkflowStep, navigation
from mlfx.app.streamlit.steps import (
    render_data_loading_step,
    render_data_preparation_step,
    render_export_reports_step,
    render_model_training_step,
    render_visual_analysis_step,
)


def main() -> None:
    """Main entrypoint for Streamlit UI."""
    st.set_page_config(
        page_title="MLFX — ICT Price Prediction",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_css()
    navigation.initialize_workflow_state()
    render_sidebar()
    render_navigation()

    current_step = navigation.get_current_step()

    if current_step == WorkflowStep.DATA_LOADING:
        render_data_loading_step()
    elif current_step == WorkflowStep.DATA_PREPARATION:
        render_data_preparation_step()
    elif current_step == WorkflowStep.MODEL_TRAINING:
        render_model_training_step()
    elif current_step == WorkflowStep.VISUAL_ANALYSIS:
        render_visual_analysis_step()
    elif current_step == WorkflowStep.EXPORT_REPORTS:
        render_export_reports_step()


if __name__ == "__main__":
    main()
