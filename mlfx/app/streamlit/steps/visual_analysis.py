"""Step 4: Visual Analysis with Plotly charts."""

from __future__ import annotations

import polars as pl
import streamlit as st

from mlfx.app.streamlit.navigation import WorkflowStep, navigation
from mlfx.app.streamlit.visualization import visualizer
from mlfx.config.paths import DEFAULT_PATHS


_MAX_CHART_BARS = 800


@st.cache_data(ttl=300)
def _load_ohlcv_data(symbol: str, tf: str) -> pl.DataFrame | None:
    """Load OHLCV data from ohlcv_dir (multiple YYYY-MM.parquet files). Cached for 5 min."""
    ohlcv_dir = DEFAULT_PATHS.ohlcv_dir(symbol, tf)
    if not ohlcv_dir.exists():
        return None
    parquet_files = sorted(ohlcv_dir.glob("*.parquet"))
    if not parquet_files:
        return None
    dfs = [pl.read_parquet(f) for f in parquet_files]
    return pl.concat(dfs).sort("timestamp")


def render_visual_analysis_step() -> None:
    """Render Step 4: Visual Analysis with Plotly charts."""
    navigation.render_step_header()
    st.space("medium")

    symbol = st.session_state.get("symbol", "XAUUSD")
    tf = st.session_state.get("tf", "1H")
    label_col = st.session_state.get("label_col", "label_10")

    # KPI cards from model training step data
    step_data = navigation.get_step_data(WorkflowStep.MODEL_TRAINING)
    metrics = step_data.get("metrics") or {}
    if metrics:
        with st.container(border=True):
            kpi_cols = st.columns(4)
            kpi_cols[0].metric("Win Rate", metrics.get("Win Rate (%)", "N/A"))
            kpi_cols[1].metric("Sharpe", metrics.get("Sharpe Ratio", "N/A"))
            kpi_cols[2].metric("Net R", metrics.get("Net Profit (R)", "N/A"))
            kpi_cols[3].metric("Total Trades", metrics.get("Total Trades", "N/A"))
        st.space("medium")

    # Chart tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Market Overview",
        "💰 Trade Analysis",
        "🤖 Model Insights",
        "⚠️ Risk Analysis",
    ])

    with tab1:
        with st.container(border=True, height="stretch"):
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="chart-title">OHLCV Chart with Technical Indicators</h3>', unsafe_allow_html=True)

            try:
                df = _load_ohlcv_data(symbol, tf)
                if df is not None and not df.is_empty():
                    df_min = df["timestamp"].min().date()
                    df_max = df["timestamp"].max().date()
                    global_range = st.session_state.get("date_range")
                    if global_range and isinstance(global_range, (list, tuple)) and len(global_range) == 2:
                        date_range = (global_range[0], global_range[1])
                    else:
                        date_range = (df_min, df_max)

                    # Filter data by global date range
                    mask = (df["timestamp"].dt.date() >= date_range[0]) & (
                        df["timestamp"].dt.date() <= date_range[1]
                    )
                    filtered_df = df.filter(mask)

                    # Downsample to avoid chart lag when data is large
                    if len(filtered_df) > _MAX_CHART_BARS:
                        step = max(1, len(filtered_df) // _MAX_CHART_BARS)
                        filtered_df = (
                            filtered_df.with_row_index()
                            .filter(pl.col("index") % step == 0)
                            .drop("index")
                        )

                    # Create indicators dict
                    indicators = {}
                    if "rsi_14" in filtered_df.columns:
                        indicators["RSI"] = filtered_df["rsi_14"]
                    if "sma_20" in filtered_df.columns:
                        indicators["SMA 20"] = filtered_df["sma_20"]
                    if "ema_20" in filtered_df.columns:
                        indicators["EMA 20"] = filtered_df["ema_20"]

                    # Create and display chart
                    fig = visualizer.create_ohlcv_chart(
                        filtered_df,
                        title=f"{symbol} {tf} - Market Overview",
                        show_volume=True,
                        show_indicators=True,
                        indicators=indicators,
                    )
                    st.plotly_chart(fig, width='stretch')

                else:
                    st.warning("⚠️ OHLCV data not found. Please complete data preparation first.")

            except Exception as e:
                st.error(f"❌ Error loading market data: {str(e)}")

            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        with st.container(border=True, height="stretch"):
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="chart-title">Trade Analysis</h3>', unsafe_allow_html=True)

            try:
                reports_dir = DEFAULT_PATHS.reports_dir(symbol, tf)
                trades_path = reports_dir / f"model_{label_col}_R15_trades.parquet"

                if trades_path.exists():
                    trades_df = pl.read_parquet(trades_path)

                    st.markdown('<h4 class="chart-card-title">Equity Curve</h4>', unsafe_allow_html=True)
                    equity_fig = visualizer.create_equity_curve_chart(
                        trades_df,
                        title=f"Equity Curve: {symbol} {tf} ({label_col})",
                        show_drawdown=True,
                    )
                    st.plotly_chart(equity_fig, width='stretch')

                    st.markdown('<h4 class="chart-card-title">Session Performance</h4>', unsafe_allow_html=True)
                    heatmap_fig = visualizer.create_session_heatmap(
                        trades_df,
                        title=f"Avg PnL by Session: {symbol} {tf} ({label_col})",
                    )
                    st.plotly_chart(heatmap_fig, width='stretch')

                else:
                    st.warning("⚠️ Trade data not found. Please run model training and backtest first.")

            except Exception as e:
                st.error(f"❌ Error loading trade data: {str(e)}")

            st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        with st.container(border=True, height="stretch"):
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="chart-title">Model Insights</h3>', unsafe_allow_html=True)
            result = step_data.get("result") or {}
            if metrics or result:
                with st.container(border=True):
                    st.markdown("#### Model Metrics")
                    cols = st.columns(4)
                    cols[0].metric("Best CV F1 (macro)", f"{result.get('best_cv_f1_macro', 0):.4f}")
                    cols[1].metric("Train F1 (macro)", f"{result.get('f1_macro_train', 0):.4f}")
                    cols[2].metric("Win Rate", metrics.get("Win Rate (%)", "N/A"))
                    cols[3].metric("Sharpe Ratio", metrics.get("Sharpe Ratio", "N/A"))
                if result.get("selected_features"):
                    st.markdown("#### Selected Features")
                    st.write(", ".join(result["selected_features"][:30]))
                    if len(result["selected_features"]) > 30:
                        st.caption(f"... and {len(result['selected_features']) - 30} more")
            else:
                st.info("📈 Chạy Model Training và Evaluate để xem insights.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab4:
        with st.container(border=True, height="stretch"):
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="chart-title">Risk Analysis</h3>', unsafe_allow_html=True)
            reports_dir = DEFAULT_PATHS.reports_dir(symbol, tf)
            trades_path = reports_dir / f"model_{label_col}_R15_trades.parquet"
            if trades_path.exists():
                try:
                    risk_trades_df = pl.read_parquet(trades_path)
                    if not risk_trades_df.is_empty():
                        st.markdown("#### Drawdown Analysis")
                        dd_fig = visualizer.create_equity_curve_chart(
                            risk_trades_df,
                            title=f"Equity & Drawdown: {symbol} {tf} ({label_col})",
                            show_drawdown=True,
                        )
                        st.plotly_chart(dd_fig, width='stretch')
                        with st.container(border=True):
                            st.markdown("#### Risk Metrics")
                            r_cols = st.columns(4)
                            r_cols[0].metric("Win Rate", metrics.get("Win Rate (%)", "N/A"))
                            r_cols[1].metric("Sharpe", metrics.get("Sharpe Ratio", "N/A"))
                            r_cols[2].metric("Calmar", metrics.get("Calmar Ratio", "N/A"))
                            r_cols[3].metric("Net Profit (R)", metrics.get("Net Profit (R)", "N/A"))
                    else:
                        st.info("⚠️ Chạy Model Evaluation để tạo backtest và xem risk analysis.")
                except Exception as e:
                    st.error(f"❌ Error loading risk data: {str(e)}")
            elif metrics:
                with st.container(border=True):
                    st.markdown("#### Risk Metrics")
                    r_cols = st.columns(4)
                    r_cols[0].metric("Win Rate", metrics.get("Win Rate (%)", "N/A"))
                    r_cols[1].metric("Sharpe", metrics.get("Sharpe Ratio", "N/A"))
                    r_cols[2].metric("Calmar", metrics.get("Calmar Ratio", "N/A"))
                    r_cols[3].metric("Net Profit (R)", metrics.get("Net Profit (R)", "N/A"))
                st.info("💡 Chạy Model Evaluation để tạo file trades và xem biểu đồ drawdown chi tiết.")
            else:
                st.info("⚠️ Chạy Model Evaluation để tạo backtest và xem risk analysis.")
            st.markdown("</div>", unsafe_allow_html=True)

    st.space("medium")
    with st.container(horizontal=True, horizontal_alignment="center"):
        if st.button("✅ Complete Visual Analysis", key="btn_complete_visual"):
            navigation.mark_step_completed(WorkflowStep.VISUAL_ANALYSIS)
            st.rerun()

