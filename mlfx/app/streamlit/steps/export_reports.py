"""Step 5: Export & Reports."""

from __future__ import annotations

import io

import polars as pl
import streamlit as st

from mlfx.app.streamlit.navigation import WorkflowStep, navigation
from mlfx.app.streamlit.utils import load_config
from mlfx.config.paths import DEFAULT_PATHS
from mlfx.evaluation.runner import run_full_eval, run_model_backtest
from mlfx.training.data import load_labelled_dataset


def render_export_reports_step() -> None:
    """Render Step 5: Export & Reports."""
    navigation.render_step_header()
    st.space("medium")

    symbol = st.session_state.get("symbol", "XAUUSD")
    tf = st.session_state.get("tf", "1H")
    label_col = st.session_state.get("label_col", "label_10")
    reports_dir = DEFAULT_PATHS.reports_dir(symbol, tf)
    step_data = navigation.get_step_data(WorkflowStep.MODEL_TRAINING)
    tp_r = step_data.get("tp_r", 1.5)
    sl_r = step_data.get("sl_r", 1.0)

    with st.container(border=True):
        st.markdown("#### Export Options")
        st.caption(f"Output path: `{reports_dir}`")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📊 Data Export")
            ohlcv_dir = DEFAULT_PATHS.ohlcv_dir(symbol, tf)
            labels_dir = DEFAULT_PATHS.labels_dir(symbol, tf)

            ohlcv_files = sorted(ohlcv_dir.glob("*.parquet")) if ohlcv_dir.exists() else []
            label_files = sorted(labels_dir.glob("*.parquet")) if labels_dir.exists() else []
            trades_path = reports_dir / f"model_{label_col}_R{int(tp_r * 10)}_trades.parquet"
            if not trades_path.exists():
                trades_path = reports_dir / f"model_{label_col}_R15_trades.parquet"

            if ohlcv_files:
                combined_ohlcv = pl.concat(pl.read_parquet(f) for f in ohlcv_files).sort("timestamp")
                buf = io.BytesIO()
                combined_ohlcv.write_parquet(buf)
                ohlcv_bytes = buf.getvalue()
                st.download_button(
                    "📥 Download OHLCV (Parquet)",
                    data=ohlcv_bytes,
                    file_name=f"{symbol}_{tf}_ohlcv.parquet",
                    mime="application/octet-stream",
                    key="btn_dl_ohlcv",
                )
            else:
                st.caption("OHLCV data not found. Complete data preparation first.")

            if trades_path.exists():
                trades_df = pl.read_parquet(trades_path)
                buf = io.BytesIO()
                trades_df.write_parquet(buf)
                trades_bytes = buf.getvalue()
                st.download_button(
                    "📥 Download Trades (Parquet)",
                    data=trades_bytes,
                    file_name=f"{symbol}_{tf}_{label_col}_trades.parquet",
                    mime="application/octet-stream",
                    key="btn_dl_trades",
                )
            else:
                st.caption("Trade data not found. Run model training and backtest first.")

            if label_files:
                combined_labels = pl.concat(pl.read_parquet(f) for f in label_files).sort("timestamp")
                buf = io.BytesIO()
                combined_labels.write_parquet(buf)
                labels_bytes = buf.getvalue()
                st.download_button(
                    "📥 Download Features/Labels (Parquet)",
                    data=labels_bytes,
                    file_name=f"{symbol}_{tf}_features_labels.parquet",
                    mime="application/octet-stream",
                    key="btn_dl_features",
                )
            else:
                st.caption("Feature/label data not found. Complete data preparation first.")

        with col2:
            st.subheader("📄 Generate Reports")
            st.caption("Run backtest to create or refresh HTML/PNG reports.")

            if st.button("📄 Generate Reports", key="btn_export_reports", width="stretch"):
                df = load_labelled_dataset(symbol, tf)
                if df is None or df.is_empty():
                    st.warning("⚠️ No labelled data found. Complete data preparation and training first.")
                else:
                    with st.status("Generating reports...", expanded=True) as status:
                        try:
                            cfg = load_config()
                            bt_cfg = cfg.get("backtest", {})
                            initial_capital = float(bt_cfg.get("initial_capital", 10000.0))
                            risk_pct = float(bt_cfg.get("risk_pct", 1.0))
                            commission = float(bt_cfg.get("commission", 0.1))

                            metrics = run_model_backtest(
                                symbol=symbol,
                                tf=tf,
                                label_col=label_col,
                                tp_r=tp_r,
                                sl_r=sl_r,
                                initial_capital=initial_capital,
                                risk_pct=risk_pct,
                                commission=commission,
                            )
                            if metrics:
                                status.update(
                                    label="Reports generated successfully!",
                                    state="complete",
                                    expanded=False,
                                )
                                st.success(f"✅ Reports saved to `{reports_dir}`")
                            else:
                                status.update(
                                    label="No model found, generating labels baseline report...",
                                    state="running",
                                )
                                run_full_eval(
                                    symbol=symbol,
                                    tf=tf,
                                    label_col=label_col,
                                    tp_r=tp_r,
                                    sl_r=sl_r,
                                    initial_capital=initial_capital,
                                    risk_pct=risk_pct,
                                    commission=commission,
                                )
                                status.update(
                                    label="Labels baseline report generated.",
                                    state="complete",
                                    expanded=False,
                                )
                                st.success(f"✅ Labels baseline report saved to `{reports_dir}`")
                        except Exception as e:
                            status.update(label=f"Error: {str(e)}", state="error", expanded=True)
                            st.error(f"❌ Report generation failed: {str(e)}")

        with st.expander("Xem trước"):
            st.caption(f"Export path: `{reports_dir}`")
            st.caption("Use Download buttons for data. Generate Reports creates HTML/PNG backtest artifacts.")

    st.space("medium")

    with st.container(border=True):
        st.markdown("#### Workflow Summary")

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

    st.space("medium")
    with st.container(horizontal=True, horizontal_alignment="center"):
        if st.button("🎉 Complete Workflow", key="btn_complete_workflow", type="primary"):
            navigation.mark_step_completed(WorkflowStep.EXPORT_REPORTS)
            st.success("🎉 Congratulations! MLFX workflow completed successfully!")
            st.balloons()
