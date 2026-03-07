"""Reporting utilities for backtest artifacts."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import polars as pl
import seaborn as sns

logger = logging.getLogger(__name__)
plt.style.use("dark_background")


def plot_interactive_candlestick(
    df: pl.DataFrame,
    title: str,
    out_path: Path,
    trades_df: pl.DataFrame | None = None,
) -> None:
    """Generate an interactive Plotly candlestick chart with optional trade markers."""
    pandas_df = df.to_pandas()
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.02,
    )
    fig.add_trace(
        go.Candlestick(
            x=pandas_df["timestamp"],
            open=pandas_df["open"],
            high=pandas_df["high"],
            low=pandas_df["low"],
            close=pandas_df["close"],
            increasing_line_color="#00C896",
            decreasing_line_color="#FF4C4C",
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
                line={"color": "#FFD700", "width": 1.2},
                name="RSI 14",
            ),
            row=2,
            col=1,
        )

    if trades_df is not None and not trades_df.is_empty():
        trade_df = trades_df.to_pandas()
        longs = trade_df[trade_df["signal"] == "LONG"]
        shorts = trade_df[trade_df["signal"] == "SHORT"]

        fig.add_trace(
            go.Scatter(
                x=longs["entry_time"],
                y=longs["entry_price"],
                mode="markers",
                marker={
                    "symbol": "triangle-up",
                    "color": "lime",
                    "size": 12,
                    "line": {"width": 1, "color": "black"},
                },
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
                marker={
                    "symbol": "triangle-down",
                    "color": "fuchsia",
                    "size": 12,
                    "line": {"width": 1, "color": "black"},
                },
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
    logger.info("Saved report %s", out_path)


def plot_equity_curve(trades_df: pl.DataFrame, title: str, out_path: Path) -> None:
    """Generate a static equity and drawdown chart."""
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

    peak = 0
    drawdown: list[float] = []
    for value in equity:
        if value > peak:
            peak = value
        drawdown.append(value - peak)

    ax2.fill_between(range(len(drawdown)), drawdown, 0, color="#FF4C4C", alpha=0.6)
    ax2.set_ylabel("Drawdown (R)", color="#888")

    for axis in (ax1, ax2):
        axis.tick_params(colors="#888")
        for spine in axis.spines.values():
            spine.set_color("#888")

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info("Saved report %s", out_path)


def plot_session_performance(trades_df: pl.DataFrame, title: str, out_path: Path) -> None:
    """Generate a heatmap of average PnL by UTC hour and weekday."""
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

    fig, ax = plt.subplots(figsize=(9, 10), facecolor="#1a1a2e")
    sns.heatmap(
        pivot_table,
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
    fig.savefig(str(out_path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info("Saved report %s", out_path)


def generate_full_report(
    symbol: str,
    tf: str,
    df: pl.DataFrame,
    trades: pl.DataFrame,
    label_name: str,
    out_dir: Path,
) -> None:
    """Generate the full report bundle for a backtest run."""
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = label_name

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
    logger.info("All reports saved to %s", out_dir)


__all__ = [
    "generate_full_report",
    "plot_equity_curve",
    "plot_interactive_candlestick",
    "plot_session_performance",
]
