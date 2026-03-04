"""
viz/charts.py
=============
Generate comprehensive visualizing reports for backtests.
Interactive Candlestick (Plotly), Equity Curve (Matplotlib), Session Heatmap (Seaborn).
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import polars as pl
import seaborn as sns

logger = logging.getLogger(__name__)

# Dark theme for matplotlib
plt.style.use("dark_background")


def plot_interactive_candlestick(
    df: pl.DataFrame, title: str, out_path: Path, trades_df: pl.DataFrame | None = None
) -> None:
    """Generate interactive Plotly candlestick chart with signals."""
    pd_df = df.to_pandas()

    # 2 rows for Candle + RSI
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.02
    )

    fig.add_trace(
        go.Candlestick(
            x=pd_df["timestamp"],
            open=pd_df["open"],
            high=pd_df["high"],
            low=pd_df["low"],
            close=pd_df["close"],
            increasing_line_color="#00C896",
            decreasing_line_color="#FF4C4C",
            name="XAUUSD",
        ),
        row=1,
        col=1,
    )

    # Plot RSI if available
    if "rsi_14" in pd_df.columns:
        fig.add_trace(
            go.Scatter(
                x=pd_df["timestamp"],
                y=pd_df["rsi_14"],
                line=dict(color="#FFD700", width=1.2),
                name="RSI 14",
            ),
            row=2,
            col=1,
        )

    # Overly trades as markers
    if trades_df is not None and not trades_df.is_empty():
        td_df = trades_df.to_pandas()

        longs = td_df[td_df["signal"] == "LONG"]
        shorts = td_df[td_df["signal"] == "SHORT"]

        fig.add_trace(
            go.Scatter(
                x=longs["entry_time"],
                y=longs["entry_price"],
                mode="markers",
                marker=dict(
                    symbol="triangle-up",
                    color="lime",
                    size=12,
                    line=dict(width=1, color="black"),
                ),
                name="LONG Entry",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=shorts["entry_time"],
                y=shorts["entry_price"],
                mode="markers",
                marker=dict(
                    symbol="triangle-down",
                    color="fuchsia",
                    size=12,
                    line=dict(width=1, color="black"),
                ),
                name="SHORT Entry",
            ),
            row=1,
            col=1,
        )

    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=700,
        xaxis_rangeslider_visible=False,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path))
    logger.info("✓ %s", out_path)


def plot_equity_curve(trades_df: pl.DataFrame, title: str, out_path: Path) -> None:
    """Generate static Matplotlib equity & drawdown curve."""
    if trades_df.is_empty():
        return

    equity = trades_df["pnl_r"].cum_sum().to_list()

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(14, 8),
        facecolor="#1a1a2e",
        gridspec_kw={"height_ratios": [3, 1]},
    )
    ax1.set_facecolor("#0d0d1a")
    ax2.set_facecolor("#0d0d1a")

    ax1.plot(equity, color="#FFD700", linewidth=1.5, label="Equity (R)")
    ax1.fill_between(range(len(equity)), equity, alpha=0.1, color="#FFD700")
    ax1.axhline(0, color="#888", linewidth=0.5)
    ax1.set_title(title, color="#FFD700", fontsize=13)
    ax1.set_ylabel("Cumulative R", color="#888")
    ax1.legend(facecolor="#1a1a2e", labelcolor="white")

    # Underwater equity (drawdown)
    peak = 0
    drawdown = []
    for v in equity:
        if v > peak:
            peak = v
        drawdown.append(v - peak)

    ax2.fill_between(range(len(drawdown)), drawdown, 0, color="#FF4C4C", alpha=0.6)
    ax2.set_ylabel("Drawdown (R)", color="#888")

    for ax in [ax1, ax2]:
        ax.tick_params(colors="#888")
        for spine in ax.spines.values():
            spine.set_color("#888")

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        str(out_path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor()
    )
    plt.close(fig)
    logger.info("✓ %s", out_path)


def plot_session_performance(
    trades_df: pl.DataFrame, title: str, out_path: Path
) -> None:
    """Generate a heatmap of avg PnL by UTC Hour and Weekday using Seaborn."""
    if trades_df.is_empty():
        return

    # Create pivot table
    pt = trades_df.to_pandas().pivot_table(
        index="hour", columns="weekday", values="pnl_r", aggfunc="mean", fill_value=0
    )

    # Ensure all days 0-4 (Mon-Fri) are present and correct order
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    for i in range(5):
        if i not in pt.columns:
            pt[i] = 0.0
    pt = pt[[0, 1, 2, 3, 4]]
    pt.columns = days

    # Ensure all hours 0-23 are present
    for i in range(24):
        if i not in pt.index:
            pt.loc[i] = [0.0] * 5
    pt = pt.sort_index()

    fig, ax = plt.subplots(figsize=(9, 10), facecolor="#1a1a2e")
    sns.heatmap(
        pt,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        center=0,
        ax=ax,
        linewidths=0.3,
        linecolor="#1a1a2e",
        cbar_kws={"label": "Average PnL (R)"},
    )
    ax.set_title(title, color="#FFD700", fontsize=13)
    ax.set_ylabel("UTC Hour")
    ax.set_xlabel("Weekday")

    for spine in ax.spines.values():
        spine.set_color("#1a1a2e")

    fig.patch.set_facecolor("#1a1a2e")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        str(out_path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor()
    )
    plt.close(fig)
    logger.info("✓ %s", out_path)


def generate_full_report(
    symbol: str,
    tf: str,
    df: pl.DataFrame,
    trades: pl.DataFrame,
    label_name: str,
    out_dir: Path,
) -> None:
    """Generate all 3 backtest reports at once."""
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{symbol}_{tf}_{label_name}"

    logger.info("Generating reports for %s", prefix)

    # Generate Candlestick pattern
    plot_interactive_candlestick(
        df=df,
        title=f"{symbol} {tf} - Trades ({label_name})",
        out_path=out_dir / f"{prefix}_candlestick.html",
        trades_df=trades,
    )

    # Generate Equity Curve
    plot_equity_curve(
        trades_df=trades,
        title=f"Equity Curve: {symbol} {tf} ({label_name})",
        out_path=out_dir / f"{prefix}_equity.png",
    )

    # Generate Heatmap
    plot_session_performance(
        trades_df=trades,
        title=f"Avg PnL by Session: {symbol} {tf} ({label_name})",
        out_path=out_dir / f"{prefix}_heatmap.png",
    )
    logger.info("All reports saved to %s", out_dir)
