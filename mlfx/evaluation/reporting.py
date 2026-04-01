"""Reporting utilities for backtest artifacts."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import polars as pl
import seaborn as sns

logger = logging.getLogger(__name__)
plt.style.use("dark_background")


# =============================================================================
# AMOLED Dark Theme Constants
# =============================================================================

# Pure black backgrounds for AMOLED efficiency
AMOLED_BG = "#000000"
AMOLED_PAPER = "#000000"
AMOLED_PLOT = "#0a0a0a"

# Glassmorphism effect colors
GLASS_BG = "rgba(20, 20, 20, 0.7)"
GLASS_BORDER = "rgba(255, 255, 255, 0.1)"
GLASS_HIGHLIGHT = "rgba(255, 255, 255, 0.05)"

# Emerald accent palette
EMERALD = {
    "primary": "#10B981",
    "light": "#34D399",
    "lighter": "#6EE7B7",
    "dark": "#059669",
    "glow": "rgba(16, 185, 129, 0.3)",
}

# Supporting colors
CRIMSON = {
    "primary": "#EF4444",
    "light": "#F87171",
    "dark": "#DC2626",
    "glow": "rgba(239, 68, 68, 0.3)",
}

GOLD = {
    "primary": "#F59E0B",
    "light": "#FBBF24",
    "dark": "#D97706",
}

# Text colors
TEXT = {
    "primary": "#E5E7EB",
    "secondary": "#9CA3AF",
    "muted": "#6B7280",
    "dark": "#4B5563",
}

# Grid and line colors
GRID_COLOR = "rgba(255, 255, 255, 0.05)"
LINE_COLOR = "rgba(255, 255, 255, 0.1)"


# =============================================================================
# Styling Helper Functions
# =============================================================================


def _get_amoled_layout_kwargs(title: str, height: int = 600) -> dict:
    """Return standard AMOLED dark theme layout kwargs for Plotly figures."""
    return {
        "title": dict(
            text=title,
            font=dict(color=TEXT["primary"], size=16),
            x=0.5,
            xanchor="center",
        ),
        "paper_bgcolor": AMOLED_PAPER,
        "plot_bgcolor": AMOLED_PLOT,
        "font": dict(color=TEXT["secondary"], family="Inter, system-ui, sans-serif"),
        "margin": dict(l=60, r=40, t=60, b=60),
        "height": height,
        "hovermode": "closest",
        "hoverlabel": dict(
            bgcolor="rgba(20, 20, 20, 0.95)",
            bordercolor=EMERALD["primary"],
            font=dict(color=TEXT["primary"]),
        ),
    }


def _apply_amoled_axis_styling(fig: go.Figure, row: int = 1, col: int = 1) -> None:
    """Apply AMOLED dark theme styling to axis."""
    update_kwargs = dict(
        gridcolor=GRID_COLOR,
        linecolor=LINE_COLOR,
        tickfont=dict(color=TEXT["secondary"]),
    )
    # Only use row/col if figure has subplots (check if _grid_ref exists)
    if hasattr(fig, "_grid_ref") and fig._grid_ref is not None:
        fig.update_xaxes(**update_kwargs, row=row, col=col)
        fig.update_yaxes(**update_kwargs, row=row, col=col)
    else:
        fig.update_xaxes(**update_kwargs)
        fig.update_yaxes(**update_kwargs)


def _add_glass_card(
    fig: go.Figure,
    x0: float = 0,
    y0: float = 0,
    x1: float = 1,
    y1: float = 1,
    layer: str = "below",
) -> None:
    """Add a glass-like card shape to the figure."""
    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=x0,
        y0=y0,
        x1=x1,
        y1=y1,
        line=dict(color=GLASS_BORDER, width=1),
        fillcolor=GLASS_HIGHLIGHT,
        layer=layer,
    )


def _create_empty_figure_with_message(message: str) -> go.Figure:
    """Create an empty figure with centered message for no data cases."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color=TEXT["muted"]),
    )
    fig.update_layout(**_get_amoled_layout_kwargs("No Data"))
    return fig


def get_candlestick_figure(
    df: pl.DataFrame,
    title: str,
    trades_df: pl.DataFrame | None = None,
) -> go.Figure:
    """Generate an interactive Plotly candlestick chart figure with AMOLED dark theme."""
    pandas_df = df.to_pandas()
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.02,
    )
    
    # Candlestick with emerald (bullish) and crimson (bearish)
    fig.add_trace(
        go.Candlestick(
            x=pandas_df["timestamp"],
            open=pandas_df["open"],
            high=pandas_df["high"],
            low=pandas_df["low"],
            close=pandas_df["close"],
            increasing_line_color=EMERALD["primary"],
            decreasing_line_color=CRIMSON["primary"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    if "rsi_14" in pandas_df.columns:
        fig.add_trace(
            go.Scatter(
                x=pandas_df["timestamp"],
                y=pandas_df["rsi_14"],
                line=dict(color=GOLD["primary"], width=1.2),
                name="RSI 14",
                hovertemplate="RSI: %{y:.1f}<extra></extra>",
            ),
            row=2,
            col=1,
        )

    if trades_df is not None and not trades_df.is_empty():
        trade_df = trades_df.to_pandas()
        longs = trade_df[trade_df["signal"] == "LONG"]
        shorts = trade_df[trade_df["signal"] == "SHORT"]

        # LONG entries with emerald glow
        fig.add_trace(
            go.Scatter(
                x=longs["entry_time"],
                y=longs["entry_price"],
                mode="markers",
                marker=dict(
                    symbol="triangle-up",
                    color=EMERALD["light"],
                    size=12,
                    line=dict(width=1, color=EMERALD["dark"]),
                ),
                name="LONG Entry",
                hovertemplate="LONG @ %{y:.2f}<br>%{x}<extra></extra>",
            ),
            row=1,
            col=1,
        )
        # SHORT entries with crimson
        fig.add_trace(
            go.Scatter(
                x=shorts["entry_time"],
                y=shorts["entry_price"],
                mode="markers",
                marker=dict(
                    symbol="triangle-down",
                    color=CRIMSON["light"],
                    size=12,
                    line=dict(width=1, color=CRIMSON["dark"]),
                ),
                name="SHORT Entry",
                hovertemplate="SHORT @ %{y:.2f}<br>%{x}<extra></extra>",
            ),
            row=1,
            col=1,
        )

    # Apply AMOLED dark theme
    fig.update_layout(**_get_amoled_layout_kwargs(title, height=700))
    fig.update_layout(xaxis_rangeslider_visible=False)
    _apply_amoled_axis_styling(fig, row=1, col=1)
    _apply_amoled_axis_styling(fig, row=2, col=1)
    _add_glass_card(fig)
    
    return fig


def get_equity_curve_figure(trades_df: pl.DataFrame, title: str) -> go.Figure:
    """Generate an interactive equity curve figure with AMOLED dark theme."""
    if trades_df.is_empty():
        return _create_empty_figure_with_message("No trades data available")

    equity = trades_df["pnl_r"].cum_sum().to_list()
    pandas_df = trades_df.to_pandas()
    
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.02,
    )
    
    # Equity curve with emerald gradient
    fig.add_trace(
        go.Scatter(
            x=pandas_df["exit_time"],
            y=equity,
            line=dict(color=EMERALD["primary"], width=2),
            name="Equity (R)",
            fill="tozeroy",
            fillcolor=EMERALD["glow"],
            hovertemplate="Equity: %{y:.2f}R<br>%{x}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    
    # Drawdown calculation
    peak = 0
    drawdown: list[float] = []
    for value in equity:
        if value > peak:
            peak = value
        drawdown.append(value - peak)
    
    # Drawdown with crimson fill
    fig.add_trace(
        go.Scatter(
            x=pandas_df["exit_time"],
            y=drawdown,
            line=dict(color=CRIMSON["primary"], width=1.5),
            name="Drawdown (R)",
            fill="tozeroy",
            fillcolor=CRIMSON["glow"],
            hovertemplate="Drawdown: %{y:.2f}R<br>%{x}<extra></extra>",
        ),
        row=2,
        col=1,
    )
    
    # Apply AMOLED dark theme
    fig.update_layout(**_get_amoled_layout_kwargs(title, height=600))
    fig.update_yaxes(title_text="Equity (R)", row=1, col=1)
    fig.update_yaxes(title_text="Drawdown (R)", row=2, col=1)
    _apply_amoled_axis_styling(fig, row=1, col=1)
    _apply_amoled_axis_styling(fig, row=2, col=1)
    _add_glass_card(fig)
    
    return fig


def get_session_heatmap_figure(trades_df: pl.DataFrame, title: str) -> go.Figure:
    """Generate an interactive session performance heatmap figure with AMOLED dark theme."""
    if trades_df.is_empty():
        return _create_empty_figure_with_message("No trades data available")

    pivot_table = trades_df.to_pandas().pivot_table(
        index="hour",
        columns="weekday",
        values="pnl_r",
        aggfunc="mean",
        fill_value=0,
    )
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

    # Custom colorscale: Crimson -> Black -> Emerald
    colorscale = [
        [0.0, CRIMSON["dark"]],
        [0.3, CRIMSON["primary"]],
        [0.5, "#1a1a1a"],
        [0.7, EMERALD["dark"]],
        [1.0, EMERALD["primary"]],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=day_labels,
        y=pivot_table.index,
        colorscale=colorscale,
        zmid=0,
        colorbar=dict(
            title=dict(text="Avg PnL (R)", font=dict(color=TEXT["secondary"])),
            tickfont=dict(color=TEXT["secondary"]),
            thickness=15,
            len=0.8,
        ),
        hoverongaps=False,
        hovertemplate="Hour: %{y}<br>Day: %{x}<br>Avg PnL: %{z:.2f}R<extra></extra>",
    ))

    # Apply AMOLED dark theme
    fig.update_layout(**_get_amoled_layout_kwargs(title, height=500))
    fig.update_layout(
        xaxis_title="Weekday",
        yaxis_title="UTC Hour",
    )
    _apply_amoled_axis_styling(fig)
    _add_glass_card(fig)
    
    return fig


def plot_interactive_candlestick(
    df: pl.DataFrame,
    title: str,
    out_path: Path,
    trades_df: pl.DataFrame | None = None,
) -> None:
    """Generate an interactive Plotly candlestick chart with AMOLED dark theme."""
    fig = get_candlestick_figure(df, title, trades_df)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path))
    logger.info("Saved report %s", out_path)


def plot_equity_curve(trades_df: pl.DataFrame, title: str, out_path: Path) -> None:
    """Generate a static equity and drawdown chart with AMOLED dark theme."""
    if trades_df.is_empty():
        return

    equity = trades_df["pnl_r"].cum_sum().to_list()
    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(14, 8),
        facecolor=AMOLED_BG,
        gridspec_kw={"height_ratios": [3, 1]},
    )
    ax1.set_facecolor(AMOLED_PLOT)
    ax2.set_facecolor(AMOLED_PLOT)

    # Equity curve with emerald
    ax1.plot(equity, color=EMERALD["primary"], linewidth=1.5, label="Equity (R)")
    ax1.fill_between(range(len(equity)), equity, alpha=0.15, color=EMERALD["primary"])
    ax1.axhline(0, color=TEXT["muted"], linewidth=0.5)
    ax1.set_title(title, color=EMERALD["primary"], fontsize=13)
    ax1.set_ylabel("Cumulative R", color=TEXT["secondary"])
    ax1.legend(facecolor=AMOLED_BG, labelcolor=TEXT["primary"])

    # Drawdown calculation
    peak = 0
    drawdown: list[float] = []
    for value in equity:
        if value > peak:
            peak = value
        drawdown.append(value - peak)

    # Drawdown with crimson
    ax2.fill_between(range(len(drawdown)), drawdown, 0, color=CRIMSON["primary"], alpha=0.6)
    ax2.set_ylabel("Drawdown (R)", color=TEXT["secondary"])

    for axis in (ax1, ax2):
        axis.tick_params(colors=TEXT["secondary"])
        for spine in axis.spines.values():
            spine.set_color(TEXT["muted"])

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info("Saved report %s", out_path)


def plot_session_performance(trades_df: pl.DataFrame, title: str, out_path: Path) -> None:
    """Generate a heatmap of average PnL by UTC hour and weekday with AMOLED dark theme."""
    if trades_df.is_empty():
        return

    pivot_table = trades_df.to_pandas().pivot_table(
        index="hour",
        columns="weekday",
        values="pnl_r",
        aggfunc="mean",
        fill_value=0,
    )
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

    fig, ax = plt.subplots(figsize=(9, 10), facecolor=AMOLED_BG)
    
    # Custom colormap: Crimson -> Black -> Emerald
    from matplotlib.colors import LinearSegmentedColormap
    colors = [CRIMSON["dark"], CRIMSON["primary"], "#1a1a1a", EMERALD["dark"], EMERALD["primary"]]
    cmap = LinearSegmentedColormap.from_list("crimson_emerald", colors)
    
    sns.heatmap(
        pivot_table,
        annot=True,
        fmt=".2f",
        cmap=cmap,
        center=0,
        ax=ax,
        linewidths=0.3,
        linecolor=AMOLED_BG,
        cbar_kws={"label": "Average PnL (R)"},
    )
    ax.set_title(title, color=EMERALD["primary"], fontsize=13)
    ax.set_ylabel("UTC Hour")
    ax.set_xlabel("Weekday")
    ax.tick_params(colors=TEXT["secondary"])
    for spine in ax.spines.values():
        spine.set_color(AMOLED_BG)

    fig.patch.set_facecolor(AMOLED_BG)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info("Saved report %s", out_path)


# =============================================================================
# New Statistical Visualization Functions
# =============================================================================


def get_enhanced_equity_figure(
    trades_df: pl.DataFrame,
    title: str,
    confidence_levels: tuple[float, float] = (0.68, 0.95),
) -> go.Figure:
    """Generate enhanced equity curve with confidence intervals and rolling metrics."""
    if trades_df.is_empty():
        return _create_empty_figure_with_message("No trades data available")

    from mlfx.evaluation.backtest import calculate_confidence_intervals, calculate_rolling_sharpe

    pnl = trades_df["pnl_r"].to_numpy()
    pandas_df = trades_df.to_pandas()
    
    # Calculate confidence intervals
    ci = calculate_confidence_intervals(pnl, levels=confidence_levels, seed=42)
    
    # Calculate rolling Sharpe
    rolling_sharpe = calculate_rolling_sharpe(pnl, window=20)
    
    # Actual equity
    equity = np.cumsum(pnl)
    
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.5, 0.25, 0.25],
        vertical_spacing=0.03,
        subplot_titles=("Equity Curve with Confidence Intervals", "Rolling Sharpe (20-period)", "Trade PnL"),
    )
    
    # 95% CI band
    fig.add_trace(
        go.Scatter(
            x=pandas_df["exit_time"],
            y=ci["upper_95"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=pandas_df["exit_time"],
            y=ci["lower_95"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(16, 185, 129, 0.1)",
            name="95% CI",
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )
    
    # 68% CI band
    fig.add_trace(
        go.Scatter(
            x=pandas_df["exit_time"],
            y=ci["upper_68"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=pandas_df["exit_time"],
            y=ci["lower_68"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(16, 185, 129, 0.2)",
            name="68% CI",
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )
    
    # Actual equity line
    fig.add_trace(
        go.Scatter(
            x=pandas_df["exit_time"],
            y=equity,
            line=dict(color=EMERALD["primary"], width=2),
            name="Equity (R)",
            hovertemplate="Equity: %{y:.2f}R<br>%{x}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    
    # Rolling Sharpe
    fig.add_trace(
        go.Scatter(
            x=pandas_df["exit_time"],
            y=rolling_sharpe,
            line=dict(color=GOLD["primary"], width=1.5),
            name="Rolling Sharpe",
            hovertemplate="Sharpe: %{y:.2f}<br>%{x}<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_hline(y=0, line_dash="dot", line_color=TEXT["muted"], row=2, col=1)
    
    # Individual trade PnL
    colors = [EMERALD["primary"] if p > 0 else CRIMSON["primary"] for p in pnl]
    fig.add_trace(
        go.Bar(
            x=pandas_df["exit_time"],
            y=pnl,
            marker_color=colors,
            name="Trade PnL",
            hovertemplate="PnL: %{y:.2f}R<br>%{x}<extra></extra>",
        ),
        row=3,
        col=1,
    )
    
    # Apply AMOLED dark theme
    fig.update_layout(**_get_amoled_layout_kwargs(title, height=800))
    fig.update_yaxes(title_text="Equity (R)", row=1, col=1)
    fig.update_yaxes(title_text="Sharpe", row=2, col=1)
    fig.update_yaxes(title_text="PnL (R)", row=3, col=1)
    for row in range(1, 4):
        _apply_amoled_axis_styling(fig, row=row, col=1)
    _add_glass_card(fig)
    
    return fig


def get_drawdown_analysis_figure(trades_df: pl.DataFrame, title: str) -> go.Figure:
    """Generate detailed drawdown analysis with recovery periods."""
    if trades_df.is_empty():
        return _create_empty_figure_with_message("No trades data available")

    from mlfx.evaluation.backtest import analyze_drawdowns

    pnl = trades_df["pnl_r"].to_numpy()
    pandas_df = trades_df.to_pandas()
    
    equity = np.cumsum(pnl)
    dd_analysis = analyze_drawdowns(equity)
    
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.4],
        vertical_spacing=0.03,
        subplot_titles=("Underwater Equity Curve", "Drawdown Events"),
    )
    
    # Underwater equity (negative values)
    underwater = -dd_analysis["drawdowns"]
    
    fig.add_trace(
        go.Scatter(
            x=pandas_df["exit_time"],
            y=underwater,
            fill="tozeroy",
            fillcolor=CRIMSON["glow"],
            line=dict(color=CRIMSON["primary"], width=1),
            name="Drawdown",
            hovertemplate="Drawdown: %{y:.2f}R<br>%{x}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    
    # Mark major drawdown events
    for event in dd_analysis["events"][:10]:  # Top 10 events
        start_time = pandas_df["exit_time"].iloc[event["start_idx"]]
        trough_time = pandas_df["exit_time"].iloc[event["trough_idx"]]
        end_time = pandas_df["exit_time"].iloc[event["end_idx"]]
        
        # Drawdown period highlight
        fig.add_vrect(
            x0=start_time,
            x1=end_time,
            fillcolor="rgba(239, 68, 68, 0.1)",
            line_width=0,
            row=1,
            col=1,
        )
        
        # Trough marker
        fig.add_trace(
            go.Scatter(
                x=[trough_time],
                y=[-event["magnitude"]],
                mode="markers+text",
                marker=dict(color=CRIMSON["light"], size=8),
                text=[f"{event['magnitude']:.1f}R"],
                textposition="bottom center",
                textfont=dict(color=TEXT["secondary"], size=9),
                showlegend=False,
                hovertemplate=f"Duration: {event['duration']} bars<br>Recovery: {event['recovery']} bars<extra></extra>",
            ),
            row=1,
            col=1,
        )
    
    # Drawdown events bar chart (recovery time)
    if dd_analysis["events"]:
        event_names = [f"DD{i+1}" for i in range(min(10, len(dd_analysis["events"])))]
        durations = [e["duration"] for e in dd_analysis["events"][:10]]
        recoveries = [e["recovery"] for e in dd_analysis["events"][:10]]
        
        fig.add_trace(
            go.Bar(
                x=event_names,
                y=durations,
                name="Duration",
                marker_color=CRIMSON["primary"],
                hovertemplate="Duration: %{y} bars<extra></extra>",
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Bar(
                x=event_names,
                y=recoveries,
                name="Recovery",
                marker_color=EMERALD["primary"],
                hovertemplate="Recovery: %{y} bars<extra></extra>",
            ),
            row=2,
            col=1,
        )
    
    # Add statistics annotation
    stats_text = (
        f"Max DD: {dd_analysis['max_drawdown']:.2f}R<br>"
        f"Avg DD: {dd_analysis['avg_drawdown']:.2f}R<br>"
        f"Avg Recovery: {dd_analysis['avg_recovery']:.1f} bars"
    )
    fig.add_annotation(
        text=stats_text,
        xref="paper",
        yref="paper",
        x=0.02,
        y=0.98,
        showarrow=False,
        font=dict(color=TEXT["secondary"], size=11),
        bgcolor="rgba(0, 0, 0, 0.5)",
        bordercolor=GLASS_BORDER,
        borderwidth=1,
        align="left",
    )
    
    # Apply AMOLED dark theme
    fig.update_layout(**_get_amoled_layout_kwargs(title, height=700))
    fig.update_yaxes(title_text="Drawdown (R)", row=1, col=1)
    fig.update_yaxes(title_text="Bars", row=2, col=1)
    for row in range(1, 3):
        _apply_amoled_axis_styling(fig, row=row, col=1)
    _add_glass_card(fig)
    
    return fig


def get_trade_distribution_figure(trades_df: pl.DataFrame, title: str) -> go.Figure:
    """Generate trade distribution histograms with multiple metrics."""
    if trades_df.is_empty():
        return _create_empty_figure_with_message("No trades data available")

    pandas_df = trades_df.to_pandas()
    pnl = trades_df["pnl_r"].to_numpy()
    
    # Create subplots with proper specs for pie chart
    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "domain"}],  # domain for pie chart
        ],
        subplot_titles=("PnL Distribution", "Trade Duration", "Entry Hour Distribution", "Exit Reason"),
    )
    
    # PnL Distribution
    fig.add_trace(
        go.Histogram(
            x=pnl,
            nbinsx=30,
            marker_color=EMERALD["primary"],
            marker_line_color=EMERALD["dark"],
            marker_line_width=1,
            name="PnL",
            hovertemplate="PnL: %{x:.2f}R<br>Count: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    
    # Trade Duration
    fig.add_trace(
        go.Histogram(
            x=pandas_df["bars_held"],
            nbinsx=20,
            marker_color=GOLD["primary"],
            marker_line_color=GOLD["dark"],
            marker_line_width=1,
            name="Duration",
            hovertemplate="Duration: %{x} bars<br>Count: %{y}<extra></extra>",
        ),
        row=1,
        col=2,
    )
    
    # Entry Hour Distribution
    hour_counts = pandas_df.groupby("hour").size()
    fig.add_trace(
        go.Bar(
            x=hour_counts.index,
            y=hour_counts.values,
            marker_color=EMERALD["light"],
            marker_line_color=EMERALD["dark"],
            marker_line_width=1,
            name="Hour",
            hovertemplate="Hour: %{x}<br>Trades: %{y}<extra></extra>",
        ),
        row=2,
        col=1,
    )
    
    # Exit Reason Pie
    reason_counts = pandas_df["reason"].value_counts()
    colors_pie = [EMERALD["primary"] if r == "TP" else CRIMSON["primary"] if r == "SL" else GOLD["primary"] 
                  for r in reason_counts.index]
    fig.add_trace(
        go.Pie(
            labels=reason_counts.index,
            values=reason_counts.values,
            marker_colors=colors_pie,
            name="Exit",
            textinfo="label+percent",
            textfont=dict(color=TEXT["primary"]),
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        ),
        row=2,
        col=2,
    )
    
    # Apply AMOLED dark theme
    fig.update_layout(**_get_amoled_layout_kwargs(title, height=700))
    fig.update_xaxes(title_text="PnL (R)", row=1, col=1)
    fig.update_xaxes(title_text="Bars Held", row=1, col=2)
    fig.update_xaxes(title_text="UTC Hour", row=2, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=2)
    fig.update_yaxes(title_text="Trades", row=2, col=1)
    
    for row in range(1, 3):
        for col in range(1, 3):
            _apply_amoled_axis_styling(fig, row=row, col=col)
    _add_glass_card(fig)
    
    return fig


def get_pnl_heatmap_figure(trades_df: pl.DataFrame, title: str) -> go.Figure:
    """Generate profit/loss ratio heatmap by hour and weekday."""
    if trades_df.is_empty():
        return _create_empty_figure_with_message("No trades data available")

    pandas_df = trades_df.to_pandas()
    
    # Create pivot table with mean PnL
    pivot_pnl = pandas_df.pivot_table(
        index="hour",
        columns="weekday",
        values="pnl_r",
        aggfunc="mean",
        fill_value=0,
    )
    
    # Create pivot table with trade count
    pivot_count = pandas_df.pivot_table(
        index="hour",
        columns="weekday",
        values="pnl_r",
        aggfunc="count",
        fill_value=0,
    )
    
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    for day in range(5):
        if day not in pivot_pnl.columns:
            pivot_pnl[day] = 0.0
            pivot_count[day] = 0
    pivot_pnl = pivot_pnl[[0, 1, 2, 3, 4]]
    pivot_count = pivot_count[[0, 1, 2, 3, 4]]
    pivot_pnl.columns = day_labels
    pivot_count.columns = day_labels

    for hour in range(24):
        if hour not in pivot_pnl.index:
            pivot_pnl.loc[hour] = [0.0] * 5
            pivot_count.loc[hour] = [0] * 5
    pivot_pnl = pivot_pnl.sort_index()
    pivot_count = pivot_count.sort_index()

    # Custom colorscale: Crimson -> Black -> Emerald
    colorscale = [
        [0.0, CRIMSON["dark"]],
        [0.3, CRIMSON["primary"]],
        [0.5, "#1a1a1a"],
        [0.7, EMERALD["dark"]],
        [1.0, EMERALD["primary"]],
    ]

    # Create custom hover text
    hover_text = []
    for i, hour in enumerate(pivot_pnl.index):
        row_text = []
        for j, day in enumerate(day_labels):
            pnl_val = pivot_pnl.values[i, j]
            count_val = pivot_count.values[i, j]
            row_text.append(f"Hour: {hour}<br>Day: {day}<br>Avg PnL: {pnl_val:.2f}R<br>Trades: {count_val}")
        hover_text.append(row_text)

    fig = go.Figure(data=go.Heatmap(
        z=pivot_pnl.values,
        x=day_labels,
        y=pivot_pnl.index,
        colorscale=colorscale,
        zmid=0,
        colorbar=dict(
            title=dict(text="Avg PnL (R)", font=dict(color=TEXT["secondary"])),
            tickfont=dict(color=TEXT["secondary"]),
            thickness=15,
        ),
        hoverongaps=False,
        hovertext=hover_text,
        hoverinfo="text",
    ))

    # Apply AMOLED dark theme
    fig.update_layout(**_get_amoled_layout_kwargs(title, height=500))
    fig.update_layout(
        xaxis_title="Weekday",
        yaxis_title="UTC Hour",
    )
    _apply_amoled_axis_styling(fig)
    _add_glass_card(fig)
    
    return fig


def get_win_rate_figure(trades_df: pl.DataFrame, title: str) -> go.Figure:
    """Generate win rate analysis by hour and weekday."""
    if trades_df.is_empty():
        return _create_empty_figure_with_message("No trades data available")

    pandas_df = trades_df.to_pandas()
    
    # Calculate win rate by hour
    hour_stats = pandas_df.groupby("hour").agg(
        total=("pnl_r", "count"),
        wins=("pnl_r", lambda x: (x > 0).sum()),
    ).reset_index()
    hour_stats["win_rate"] = (hour_stats["wins"] / hour_stats["total"] * 100).fillna(0)
    
    # Calculate win rate by weekday
    day_stats = pandas_df.groupby("weekday").agg(
        total=("pnl_r", "count"),
        wins=("pnl_r", lambda x: (x > 0).sum()),
    ).reset_index()
    day_stats["win_rate"] = (day_stats["wins"] / day_stats["total"] * 100).fillna(0)
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    day_stats["day_name"] = day_stats["weekday"].map(dict(enumerate(day_labels)))
    
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Win Rate by Hour", "Win Rate by Weekday"),
    )
    
    # Win rate by hour
    colors_hour = [EMERALD["primary"] if wr >= 50 else CRIMSON["primary"] for wr in hour_stats["win_rate"]]
    fig.add_trace(
        go.Bar(
            x=hour_stats["hour"],
            y=hour_stats["win_rate"],
            marker_color=colors_hour,
            name="Win Rate",
            hovertemplate="Hour: %{x}<br>Win Rate: %{y:.1f}%<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_hline(y=50, line_dash="dot", line_color=TEXT["muted"], row=1, col=1)
    
    # Win rate by weekday
    colors_day = [EMERALD["primary"] if wr >= 50 else CRIMSON["primary"] for wr in day_stats["win_rate"]]
    fig.add_trace(
        go.Bar(
            x=day_stats["day_name"],
            y=day_stats["win_rate"],
            marker_color=colors_day,
            name="Win Rate",
            hovertemplate="Day: %{x}<br>Win Rate: %{y:.1f}%<extra></extra>",
        ),
        row=1,
        col=2,
    )
    fig.add_hline(y=50, line_dash="dot", line_color=TEXT["muted"], row=1, col=2)
    
    # Apply AMOLED dark theme
    fig.update_layout(**_get_amoled_layout_kwargs(title, height=400))
    fig.update_yaxes(title_text="Win Rate (%)", row=1, col=1)
    fig.update_yaxes(title_text="Win Rate (%)", row=1, col=2)
    fig.update_xaxes(title_text="UTC Hour", row=1, col=1)
    fig.update_xaxes(title_text="Weekday", row=1, col=2)
    
    for col in range(1, 3):
        _apply_amoled_axis_styling(fig, row=1, col=col)
    _add_glass_card(fig)
    
    return fig


def get_performance_attribution_figure(trades_df: pl.DataFrame, title: str) -> go.Figure:
    """Generate performance attribution charts showing returns breakdown."""
    if trades_df.is_empty():
        return _create_empty_figure_with_message("No trades data available")

    pandas_df = trades_df.to_pandas()
    
    # Attribution by signal type
    signal_pnl = pandas_df.groupby("signal")["pnl_r"].sum()
    
    # Attribution by weekday
    day_pnl = pandas_df.groupby("weekday")["pnl_r"].sum()
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    
    # Attribution by exit reason
    reason_pnl = pandas_df.groupby("reason")["pnl_r"].sum()
    
    # Attribution by session (simplified: London=8-16, NY=13-21, Asia=21-8)
    def get_session(hour):
        if 8 <= hour < 16:
            return "London"
        elif 13 <= hour < 21:
            return "New York"
        else:
            return "Asia"
    
    pandas_df["session"] = pandas_df["hour"].apply(get_session)
    session_pnl = pandas_df.groupby("session")["pnl_r"].sum()
    
    # Create subplots with proper specs for pie charts
    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[
            [{"type": "domain"}, {"type": "xy"}],
            [{"type": "domain"}, {"type": "xy"}],
        ],
        subplot_titles=("Returns by Signal", "Returns by Weekday", "Returns by Exit", "Returns by Session"),
    )
    
    # Pie: Signal type
    colors_signal = [EMERALD["primary"] if s == "LONG" else CRIMSON["primary"] for s in signal_pnl.index]
    fig.add_trace(
        go.Pie(
            labels=signal_pnl.index,
            values=signal_pnl.values,
            marker_colors=colors_signal,
            textinfo="label+percent",
            textfont=dict(color=TEXT["primary"]),
            hovertemplate="%{label}: %{value:.2f}R<extra></extra>",
        ),
        row=1,
        col=1,
    )
    
    # Bar: Weekday
    day_names = [day_labels[d] if d < len(day_labels) else str(d) for d in day_pnl.index]
    colors_day = [EMERALD["primary"] if p > 0 else CRIMSON["primary"] for p in day_pnl.values]
    fig.add_trace(
        go.Bar(
            x=day_names,
            y=day_pnl.values,
            marker_color=colors_day,
            hovertemplate="Day: %{x}<br>PnL: %{y:.2f}R<extra></extra>",
        ),
        row=1,
        col=2,
    )
    
    # Pie: Exit reason
    colors_reason = [EMERALD["primary"] if r == "TP" else CRIMSON["primary"] if r == "SL" else GOLD["primary"] 
                     for r in reason_pnl.index]
    fig.add_trace(
        go.Pie(
            labels=reason_pnl.index,
            values=reason_pnl.values,
            marker_colors=colors_reason,
            textinfo="label+percent",
            textfont=dict(color=TEXT["primary"]),
            hovertemplate="%{label}: %{value:.2f}R<extra></extra>",
        ),
        row=2,
        col=1,
    )
    
    # Bar: Session
    colors_session = [EMERALD["primary"] if p > 0 else CRIMSON["primary"] for p in session_pnl.values]
    fig.add_trace(
        go.Bar(
            x=session_pnl.index,
            y=session_pnl.values,
            marker_color=colors_session,
            hovertemplate="Session: %{x}<br>PnL: %{y:.2f}R<extra></extra>",
        ),
        row=2,
        col=2,
    )
    
    # Apply AMOLED dark theme
    fig.update_layout(**_get_amoled_layout_kwargs(title, height=700))
    fig.update_yaxes(title_text="PnL (R)", row=1, col=2)
    fig.update_yaxes(title_text="PnL (R)", row=2, col=2)
    
    for row in range(1, 3):
        for col in range(1, 3):
            _apply_amoled_axis_styling(fig, row=row, col=col)
    _add_glass_card(fig)
    
    return fig


# =============================================================================
# Plot Functions for New Visualizations (save to file)
# =============================================================================


def plot_enhanced_equity(trades_df: pl.DataFrame, title: str, out_path: Path) -> None:
    """Generate and save enhanced equity curve with confidence intervals."""
    fig = get_enhanced_equity_figure(trades_df, title)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path))
    logger.info("Saved report %s", out_path)


def plot_drawdown_analysis(trades_df: pl.DataFrame, title: str, out_path: Path) -> None:
    """Generate and save detailed drawdown analysis."""
    fig = get_drawdown_analysis_figure(trades_df, title)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path))
    logger.info("Saved report %s", out_path)


def plot_trade_distribution(trades_df: pl.DataFrame, title: str, out_path: Path) -> None:
    """Generate and save trade distribution histograms."""
    fig = get_trade_distribution_figure(trades_df, title)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path))
    logger.info("Saved report %s", out_path)


def plot_pnl_heatmap(trades_df: pl.DataFrame, title: str, out_path: Path) -> None:
    """Generate and save profit/loss ratio heatmap."""
    fig = get_pnl_heatmap_figure(trades_df, title)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path))
    logger.info("Saved report %s", out_path)


def plot_win_rate_analysis(trades_df: pl.DataFrame, title: str, out_path: Path) -> None:
    """Generate and save win rate analysis."""
    fig = get_win_rate_figure(trades_df, title)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path))
    logger.info("Saved report %s", out_path)


def plot_performance_attribution(trades_df: pl.DataFrame, title: str, out_path: Path) -> None:
    """Generate and save performance attribution charts."""
    fig = get_performance_attribution_figure(trades_df, title)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path))
    logger.info("Saved report %s", out_path)


def generate_full_report(
    symbol: str,
    tf: str,
    df: pl.DataFrame,
    trades: pl.DataFrame,
    label_name: str,
    out_dir: Path,
) -> None:
    """Generate the full report bundle for a backtest run with AMOLED dark theme."""
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = label_name

    # Existing reports (updated with glassmorphism styling)
    plot_interactive_candlestick(
        df=df,
        title=f"{symbol} {tf} - Trades ({label_name})",
        out_path=out_dir / f"{prefix}_candlestick.html",
        trades_df=trades,
    )
    plot_equity_curve(
        trades_df=trades,
        title=f"Equity Curve: {symbol} {tf} ({label_name})",
        out_path=out_dir / f"{prefix}_equity.png",
    )
    plot_session_performance(
        trades_df=trades,
        title=f"Avg PnL by Session: {symbol} {tf} ({label_name})",
        out_path=out_dir / f"{prefix}_heatmap.png",
    )
    
    # New enhanced reports
    plot_enhanced_equity(
        trades_df=trades,
        title=f"Enhanced Equity: {symbol} {tf} ({label_name})",
        out_path=out_dir / f"{prefix}_equity_enhanced.html",
    )
    plot_drawdown_analysis(
        trades_df=trades,
        title=f"Drawdown Analysis: {symbol} {tf} ({label_name})",
        out_path=out_dir / f"{prefix}_drawdown.html",
    )
    plot_trade_distribution(
        trades_df=trades,
        title=f"Trade Distribution: {symbol} {tf} ({label_name})",
        out_path=out_dir / f"{prefix}_distribution.html",
    )
    plot_pnl_heatmap(
        trades_df=trades,
        title=f"PnL Heatmap: {symbol} {tf} ({label_name})",
        out_path=out_dir / f"{prefix}_pnl_heatmap.html",
    )
    plot_win_rate_analysis(
        trades_df=trades,
        title=f"Win Rate Analysis: {symbol} {tf} ({label_name})",
        out_path=out_dir / f"{prefix}_win_rate.html",
    )
    plot_performance_attribution(
        trades_df=trades,
        title=f"Performance Attribution: {symbol} {tf} ({label_name})",
        out_path=out_dir / f"{prefix}_attribution.html",
    )
    
    trades.write_parquet(out_dir / f"{prefix}_trades.parquet")
    logger.info("All reports saved to %s", out_dir)


__all__ = [
    # Theme constants
    "AMOLED_BG",
    "AMOLED_PAPER",
    "AMOLED_PLOT",
    "GLASS_BG",
    "GLASS_BORDER",
    "EMERALD",
    "CRIMSON",
    "GOLD",
    "TEXT",
    "GRID_COLOR",
    # Existing functions
    "generate_full_report",
    "plot_equity_curve",
    "plot_interactive_candlestick",
    "plot_session_performance",
    "get_candlestick_figure",
    "get_equity_curve_figure",
    "get_session_heatmap_figure",
    # New visualization functions
    "get_enhanced_equity_figure",
    "get_drawdown_analysis_figure",
    "get_trade_distribution_figure",
    "get_pnl_heatmap_figure",
    "get_win_rate_figure",
    "get_performance_attribution_figure",
    # New plot functions
    "plot_enhanced_equity",
    "plot_drawdown_analysis",
    "plot_trade_distribution",
    "plot_pnl_heatmap",
    "plot_win_rate_analysis",
    "plot_performance_attribution",
]
