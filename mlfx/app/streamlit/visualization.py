"""Visualization utilities for MLFX Streamlit UI with Plotly integration."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class MLFXVisualizer:
    """Main visualization class for MLFX data analysis."""

    def __init__(self):
        self.color_scheme = {
            "primary": "#10B981",
            "secondary": "#34D399",
            "success": "#00C896",
            "danger": "#FF4C4C",
            "warning": "#FFD700",
            "background": "#0d0d1a",
            "grid": "#1a1a2e",
            "text": "#888888",
        }

    def create_ohlcv_chart(
        self,
        df: pl.DataFrame,
        title: str = "OHLCV Chart",
        show_volume: bool = True,
        show_indicators: bool = True,
        trades_df: Optional[pl.DataFrame] = None,
        indicators: Optional[Dict[str, pl.Series]] = None,
    ) -> go.Figure:
        """Create interactive OHLCV candlestick chart with optional indicators and trades."""
        pandas_df = df.to_pandas()
        if show_volume:
            fig = make_subplots(
                rows=3, cols=1, shared_xaxes=True,
                row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.02,
            )
        else:
            fig = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                row_heights=[0.8, 0.2], vertical_spacing=0.02,
            )
        fig.add_trace(
            go.Candlestick(
                x=pandas_df["timestamp"],
                open=pandas_df["open"], high=pandas_df["high"],
                low=pandas_df["low"], close=pandas_df["close"],
                increasing_line_color=self.color_scheme["success"],
                decreasing_line_color=self.color_scheme["danger"],
                name="Price",
            ),
            row=1, col=1,
        )
        if show_volume and "volume" in pandas_df.columns:
            fig.add_trace(
                go.Bar(
                    x=pandas_df["timestamp"], y=pandas_df["volume"],
                    marker_color=self.color_scheme["primary"],
                    name="Volume", opacity=0.6,
                ),
                row=2, col=1,
            )
        if show_indicators and indicators:
            indicator_row = 3 if show_volume else 2
            for name, series in indicators.items():
                pandas_series = series.to_pandas()
                if "rsi" in name.lower():
                    fig.add_trace(
                        go.Scatter(
                            x=pandas_df["timestamp"], y=pandas_series,
                            line=dict(color=self.color_scheme["warning"], width=1.5),
                            name=name.upper(),
                        ),
                        row=indicator_row, col=1,
                    )
                    fig.add_hline(y=70, line_dash="dash", line_color=self.color_scheme["danger"], opacity=0.5, row=indicator_row, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color=self.color_scheme["success"], opacity=0.5, row=indicator_row, col=1)
                else:
                    fig.add_trace(
                        go.Scatter(
                            x=pandas_df["timestamp"], y=pandas_series,
                            line=dict(color=self.color_scheme["secondary"], width=1.2),
                            name=name,
                        ),
                        row=1, col=1,
                    )
        if trades_df is not None and not trades_df.is_empty():
            trade_df = trades_df.to_pandas()
            longs = trade_df[trade_df["signal"] == "LONG"]
            if not longs.empty:
                fig.add_trace(
                    go.Scatter(
                        x=longs["entry_time"], y=longs["entry_price"],
                        mode="markers",
                        marker=dict(symbol="triangle-up", color=self.color_scheme["success"], size=12, line=dict(width=1, color="black")),
                        name="LONG Entry",
                    ),
                    row=1, col=1,
                )
            shorts = trade_df[trade_df["signal"] == "SHORT"]
            if not shorts.empty:
                fig.add_trace(
                    go.Scatter(
                        x=shorts["entry_time"], y=shorts["entry_price"],
                        mode="markers",
                        marker=dict(symbol="triangle-down", color=self.color_scheme["danger"], size=12, line=dict(width=1, color="black")),
                        name="SHORT Entry",
                    ),
                    row=1, col=1,
                )
        fig.update_layout(
            title=title, template="plotly_dark", height=800,
            xaxis_rangeslider_visible=False,
            paper_bgcolor=self.color_scheme["background"],
            plot_bgcolor=self.color_scheme["background"],
            font_color=self.color_scheme["text"],
        )
        fig.update_yaxes(title_text="Price", row=1, col=1)
        if show_volume:
            fig.update_yaxes(title_text="Volume", row=2, col=1)
        return fig

    def create_equity_curve_chart(
        self,
        trades_df: pl.DataFrame,
        title: str = "Equity Curve",
        show_drawdown: bool = True,
    ) -> go.Figure:
        """Create interactive equity curve chart with optional drawdown."""
        if trades_df.is_empty():
            fig = go.Figure()
            fig.add_annotation(text="No trades data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=self.color_scheme["text"]))
            return fig
        pandas_df = trades_df.to_pandas()
        equity = pandas_df["pnl_r"].cumsum()
        pandas_df["equity"] = equity
        if show_drawdown:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.02)
        else:
            fig = go.Figure()
        if show_drawdown:
            fig.add_trace(
                go.Scatter(x=pandas_df["exit_time"], y=equity, line=dict(color=self.color_scheme["warning"], width=2), name="Equity (R)", fill="tonexty", fillcolor="rgba(255, 215, 0, 0.1)"),
                row=1, col=1,
            )
        else:
            fig.add_trace(
                go.Scatter(x=pandas_df["exit_time"], y=equity, line=dict(color=self.color_scheme["warning"], width=2), name="Equity (R)", fill="tonexty", fillcolor="rgba(255, 215, 0, 0.1)")
            )
        if show_drawdown:
            peak = equity.expanding().max()
            drawdown = equity - peak
            fig.add_trace(
                go.Scatter(x=pandas_df["exit_time"], y=drawdown, line=dict(color=self.color_scheme["danger"], width=1.5), name="Drawdown (R)", fill="tozeroy", fillcolor="rgba(255, 76, 76, 0.3)"),
                row=2, col=1,
            )
        layout_kwargs = {"title": title, "template": "plotly_dark", "height": 600, "paper_bgcolor": self.color_scheme["background"], "plot_bgcolor": self.color_scheme["background"], "font_color": self.color_scheme["text"]}
        if show_drawdown:
            fig.update_layout(**layout_kwargs)
            fig.update_yaxes(title_text="Equity (R)", row=1, col=1)
            fig.update_yaxes(title_text="Drawdown (R)", row=2, col=1)
        else:
            fig.update_layout(**layout_kwargs)
            fig.update_yaxes(title_text="Equity (R)")
        return fig

    def create_session_heatmap(
        self,
        trades_df: pl.DataFrame,
        title: str = "Session Performance Heatmap",
    ) -> go.Figure:
        """Create heatmap of average PnL by UTC hour and weekday."""
        if trades_df.is_empty():
            fig = go.Figure()
            fig.add_annotation(text="No trades data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=self.color_scheme["text"]))
            return fig
        pandas_df = trades_df.to_pandas()
        pivot_table = pandas_df.pivot_table(index="hour", columns="weekday", values="pnl_r", aggfunc="mean", fill_value=0)
        day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        for day in range(5):
            if day not in pivot_table.columns:
                pivot_table[day] = 0.0
        pivot_table = pivot_table[[0, 1, 2, 3, 4]]
        pivot_table.columns = day_labels
        for hour in range(24):
            if hour not in pivot_table.index:
                pivot_table.loc[hour] = [0.0] * 5
        pivot_table = pivot_table.sort_index()
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values, x=day_labels, y=pivot_table.index,
            colorscale="RdYlGn", zmid=0, colorbar=dict(title="Avg PnL (R)"), hoverongaps=False,
        ))
        fig.update_layout(title=title, template="plotly_dark", height=500, paper_bgcolor=self.color_scheme["background"], plot_bgcolor=self.color_scheme["background"], font_color=self.color_scheme["text"], xaxis_title="Weekday", yaxis_title="UTC Hour")
        return fig

    def create_feature_importance_chart(
        self,
        feature_names: List[str],
        importance_scores: List[float],
        title: str = "Feature Importance",
        top_n: int = 20,
    ) -> go.Figure:
        """Create horizontal bar chart of feature importance."""
        feature_importance = list(zip(feature_names, importance_scores))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        feature_importance = feature_importance[:top_n]
        features, scores = zip(*feature_importance)
        fig = go.Figure(data=go.Bar(x=list(scores), y=list(features), orientation="h", marker_color=self.color_scheme["primary"]))
        fig.update_layout(title=title, template="plotly_dark", height=max(400, len(features) * 25), paper_bgcolor=self.color_scheme["background"], plot_bgcolor=self.color_scheme["background"], font_color=self.color_scheme["text"], xaxis_title="Importance Score", yaxis_title="Features")
        return fig

    def create_prediction_scatter(
        self,
        actual: List[float],
        predicted: List[float],
        title: str = "Predictions vs Actual",
    ) -> go.Figure:
        """Create scatter plot of predictions vs actual values."""
        fig = go.Figure()
        min_val = min(min(actual), min(predicted))
        max_val = max(max(actual), max(predicted))
        fig.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val, max_val], mode="lines", line=dict(color=self.color_scheme["text"], dash="dash"), name="Perfect Prediction"))
        fig.add_trace(go.Scatter(x=actual, y=predicted, mode="markers", marker=dict(color=self.color_scheme["primary"], size=6, opacity=0.7), name="Predictions"))
        fig.update_layout(title=title, template="plotly_dark", height=500, paper_bgcolor=self.color_scheme["background"], plot_bgcolor=self.color_scheme["background"], font_color=self.color_scheme["text"], xaxis_title="Actual Values", yaxis_title="Predicted Values")
        return fig

    def create_correlation_heatmap(
        self,
        df: pl.DataFrame,
        title: str = "Feature Correlation Heatmap",
        features: Optional[List[str]] = None,
    ) -> go.Figure:
        """Create correlation heatmap of features."""
        pandas_df = df.to_pandas()
        if features:
            pandas_df = pandas_df[features]
        corr_matrix = pandas_df.corr()
        fig = go.Figure(data=go.Heatmap(z=corr_matrix.values, x=corr_matrix.columns, y=corr_matrix.columns, colorscale="RdBu", zmid=0, colorbar=dict(title="Correlation"), hoverongaps=False))
        fig.update_layout(title=title, template="plotly_dark", height=max(400, len(corr_matrix.columns) * 25), paper_bgcolor=self.color_scheme["background"], plot_bgcolor=self.color_scheme["background"], font_color=self.color_scheme["text"])
        return fig


visualizer = MLFXVisualizer()
