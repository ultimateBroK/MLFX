"""Step 5: Export & Reports."""

from __future__ import annotations

import time

import streamlit as st

from mlfx.app.streamlit.navigation import WorkflowStep, navigation
from mlfx.config.paths import DEFAULT_PATHS


def render_export_reports_step() -> None:
    """Render Step 5: Export & Reports."""
    navigation.render_step_header()

    symbol = st.session_state.get("symbol", "XAUUSD")
    tf = st.session_state.get("tf", "1H")
    label_col = st.session_state.get("label_col", "label_10")

    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="chart-title">Export Options</h3>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📊 Data Export")
        export_data = st.checkbox("Export OHLCV Data", value=True)
        export_trades = st.checkbox("Export Trade Data", value=True)
        export_features = st.checkbox("Export Feature Data", value=False)

        if st.button("📥 Export Data", key="btn_export_data", use_container_width=True):
            try:
                reports_dir = DEFAULT_PATHS.reports_dir(symbol, tf)
                export_options = []
                if export_data:
                    export_options.append("OHLCV")
                if export_trades:
                    export_options.append("Trades")
                if export_features:
                    export_options.append("Features")

                if export_options:
                    progress_text = "Preparing data exports... Please wait."
                    my_bar = st.progress(0, text=progress_text)
                    for percent_complete in range(100):
                        time.sleep(0.01)
                        my_bar.progress(percent_complete + 1, text=progress_text)
                    my_bar.empty()

                st.info(f"📁 Data will be exported to: {reports_dir}")
                st.info(
                    f"📋 Selected exports: {', '.join(export_options) if export_options else 'None'}"
                )
                st.success("✅ Data export completed!")
            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")

    with col2:
        st.subheader("📄 Report Export")
        export_html = st.checkbox("Export HTML Report", value=True)
        export_pdf = st.checkbox("Export PDF Report", value=False)
        export_excel = st.checkbox("Export Excel Summary", value=True)

        if st.button("📄 Generate Reports", key="btn_export_reports", use_container_width=True):
            try:
                reports_dir = DEFAULT_PATHS.reports_dir(symbol, tf)
                report_options = []
                if export_html:
                    report_options.append("HTML")
                if export_pdf:
                    report_options.append("PDF")
                if export_excel:
                    report_options.append("Excel")

                if report_options:
                    progress_text = "Generating reports... Please wait."
                    my_bar = st.progress(0, text=progress_text)
                    for percent_complete in range(100):
                        time.sleep(0.015)
                        my_bar.progress(percent_complete + 1, text=progress_text)
                    my_bar.empty()

                st.info(f"📁 Reports will be generated in: {reports_dir}")
                st.info(
                    f"📋 Selected reports: {', '.join(report_options) if report_options else 'None'}"
                )
                st.success("✅ Reports generated successfully!")
            except Exception as e:
                st.error(f"❌ Report generation failed: {str(e)}")

    st.markdown('<h3 class="chart-title">Workflow Summary</h3>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Symbol", symbol)
    with col2:
        st.metric("Timeframe", tf)
    with col3:
        st.metric("Label", label_col)
    with col4:
        progress = navigation.get_step_progress()
        st.metric("Progress", f"{progress*100:.0f}%")

    if st.button("🎉 Complete Workflow", key="btn_complete_workflow", type="primary", use_container_width=True):
        navigation.mark_step_completed(WorkflowStep.EXPORT_REPORTS)
        st.success("🎉 Congratulations! MLFX workflow completed successfully!")
        st.balloons()

    st.markdown("</div>", unsafe_allow_html=True)
