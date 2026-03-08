"""Step 4: Visual Analysis with Plotly charts."""

from __future__ import annotations

import polars as pl
import streamlit as st

from mlfx.app.streamlit.navigation import WorkflowStep, navigation
from mlfx.app.streamlit.visualization import visualizer
from mlfx.config.paths import DEFAULT_PATHS


def _load_ohlcv_data(symbol: str, tf: str) -> pl.DataFrame | None:
    """Load OHLCV data from ohlcv_dir (multiple YYYY-MM.parquet files)."""
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

    symbol = st.session_state.get("symbol", "XAUUSD")
    tf = st.session_state.get("tf", "1H")
    label_col = st.session_state.get("label_col", "label_10")

    # Chart tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Market Overview",
        "💰 Trade Analysis",
        "🤖 Model Insights",
        "⚠️ Risk Analysis",
    ])

    with tab1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">OHLCV Chart with Technical Indicators</h3>', unsafe_allow_html=True)

        try:
            df = _load_ohlcv_data(symbol, tf)
            if df is not None and not df.is_empty():
                # Date range selector
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    date_range = st.date_input(
                        "Select Date Range",
                        value=[df["timestamp"].min().date(), df["timestamp"].max().date()],
                        key="market_date_range",
                    )

                # Filter data
                if len(date_range) == 2:
                    mask = (df["timestamp"].dt.date() >= date_range[0]) & (
                        df["timestamp"].dt.date() <= date_range[1]
                    )
                    filtered_df = df.filter(mask)
                else:
                    filtered_df = df

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
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.warning("⚠️ OHLCV data not found. Please complete data preparation first.")

        except Exception as e:
            st.error(f"❌ Error loading market data: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
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
                st.plotly_chart(equity_fig, use_container_width=True)

                st.markdown('<h4 class="chart-card-title">Session Performance</h4>', unsafe_allow_html=True)
                heatmap_fig = visualizer.create_session_heatmap(
                    trades_df,
                    title=f"Avg PnL by Session: {symbol} {tf} ({label_col})",
                )
                st.plotly_chart(heatmap_fig, use_container_width=True)

            else:
                st.warning("⚠️ Trade data not found. Please run model training and backtest first.")

        except Exception as e:
            st.error(f"❌ Error loading trade data: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">Model Insights</h3>', unsafe_allow_html=True)
        st.info("📈 Model insights will be available after training completion.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">Risk Analysis</h3>', unsafe_allow_html=True)
        st.info("⚠️ Risk analysis charts will be available after backtest completion.")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("✅ Complete Visual Analysis", key="btn_complete_visual", use_container_width=True):
        navigation.mark_step_completed(WorkflowStep.VISUAL_ANALYSIS)
        st.rerun()

