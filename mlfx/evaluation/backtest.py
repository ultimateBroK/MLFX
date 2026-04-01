"""Walk-forward backtesting engine for evaluating trading signals."""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

logger = logging.getLogger(__name__)

def map_ordinal_to_signal(col: pl.Expr) -> pl.Expr:
    """Map ordinal labels -2,-1,0,1,2 to signal 1 (LONG), -1 (SHORT), 0 (skip)."""
    return (
        pl.when(col.is_in([1, 2]))
        .then(1)
        .when(col.is_in([-1, -2]))
        .then(-1)
        .otherwise(0)
    )


def simulate_trades(
    df: pl.DataFrame,
    signal_col: str,
    tp_r: float = 2.0,
    sl_r: float = 1.0,
    horizon_limit: int = 10,
    atr_col: str = "atr_14",
    atr_mult: float = 0.5,
    commission: float = 0.0,
    slippage: float = 0.0,
) -> pl.DataFrame:
    """Simulate sequential, non-overlapping trades from signal labels."""
    if signal_col not in df.columns or atr_col not in df.columns:
        logger.error("Missing required columns (%s or %s) in DataFrame.", signal_col, atr_col)
        return pl.DataFrame()

    records = df.to_dicts()
    trades: list[dict[str, object]] = []
    in_trade = False
    entry_price = 0.0
    entry_tag = ""
    entry_idx = 0
    sl_price = 0.0
    tp_price = 0.0
    risk_dist = 0.0
    entry_timestamp = None

    for index in range(len(records) - 1):
        row = records[index]

        if in_trade:
            next_row = records[index + 1]
            high, low = next_row["high"], next_row["low"]
            bars_held = (index + 1) - entry_idx

            exit_price = None
            pnl_r = 0.0
            reason = ""

            if entry_tag == "LONG":
                if low <= sl_price:
                    exit_price = sl_price
                    pnl_r = -sl_r
                    reason = "SL"
                elif high >= tp_price:
                    exit_price = tp_price
                    pnl_r = tp_r
                    reason = "TP"
            else:
                if high >= sl_price:
                    exit_price = sl_price
                    pnl_r = -sl_r
                    reason = "SL"
                elif low <= tp_price:
                    exit_price = tp_price
                    pnl_r = tp_r
                    reason = "TP"

            if exit_price is None and bars_held >= horizon_limit:
                exit_price = next_row["close"]
                if risk_dist > 0:
                    if entry_tag == "LONG":
                        pnl_r = (exit_price - entry_price) / risk_dist
                    else:
                        pnl_r = (entry_price - exit_price) / risk_dist
                reason = "TIME"

            if exit_price is not None:
                if risk_dist > 0:
                    cost_r = (commission + 2 * slippage) / risk_dist
                    pnl_r -= cost_r
                trades.append(
                    {
                        "entry_time": entry_timestamp,
                        "exit_time": next_row["timestamp"],
                        "signal": entry_tag,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "bars_held": bars_held,
                        "pnl_r": pnl_r,
                        "reason": reason,
                        "weekday": entry_timestamp.weekday() if entry_timestamp else 0,
                        "hour": entry_timestamp.hour if entry_timestamp else 0,
                    }
                )
                in_trade = False
                continue

        if not in_trade:
            signal = row[signal_col]
            if signal in (1, -1) and row[atr_col] is not None:
                next_row = records[index + 1]
                in_trade = True
                entry_idx = index + 1
                entry_timestamp = next_row["timestamp"]
                entry_price = next_row["open"]
                risk_dist = row[atr_col] * atr_mult

                if signal == 1:
                    entry_tag = "LONG"
                    sl_price = entry_price - (risk_dist * sl_r)
                    tp_price = entry_price + (risk_dist * tp_r)
                else:
                    entry_tag = "SHORT"
                    sl_price = entry_price + (risk_dist * sl_r)
                    tp_price = entry_price - (risk_dist * tp_r)

    return pl.DataFrame(trades)


def calculate_rolling_sharpe(
    returns: np.ndarray,
    window: int = 20,
    annualization_factor: float = 252.0,
) -> np.ndarray:
    """Calculate rolling Sharpe ratio from returns array.

    Args:
        returns: Array of period returns (in R-multiples).
        window: Rolling window size.
        annualization_factor: Factor to annualize (default 252 for daily).

    Returns:
        Array of rolling Sharpe ratios (NaN for insufficient data).
    """
    if len(returns) < window:
        return np.full(len(returns), np.nan)

    rolling_sharpe = np.full(len(returns), np.nan)

    for i in range(window - 1, len(returns)):
        window_returns = returns[i - window + 1 : i + 1]
        mean_ret = np.mean(window_returns)
        std_ret = np.std(window_returns)

        if std_ret > 0:
            rolling_sharpe[i] = (mean_ret / std_ret) * np.sqrt(annualization_factor)

    return rolling_sharpe


def analyze_drawdowns(equity_curve: np.ndarray) -> dict[str, object]:
    """Analyze drawdown events from equity curve.

    Args:
        equity_curve: Array of cumulative equity values.

    Returns:
        Dictionary with drawdown analysis including:
        - drawdowns: Array of drawdown values at each point
        - peak_indices: Indices where new peaks were reached
        - trough_indices: Indices of drawdown troughs
        - events: List of drawdown event dicts with start, trough, end, magnitude, duration, recovery
        - max_drawdown: Maximum drawdown value
        - avg_drawdown: Average drawdown during drawdown periods
        - avg_recovery: Average recovery time in bars
    """
    if len(equity_curve) == 0:
        return {
            "drawdowns": np.array([]),
            "peak_indices": np.array([]),
            "trough_indices": np.array([]),
            "events": [],
            "max_drawdown": 0.0,
            "avg_drawdown": 0.0,
            "avg_recovery": 0.0,
        }

    # Calculate running peak and drawdown
    peak = np.maximum.accumulate(equity_curve)
    drawdowns = peak - equity_curve

    # Find peak indices (where equity equals running peak)
    peak_indices = np.where(equity_curve == peak)[0]

    # Find drawdown events
    events: list[dict] = []
    in_drawdown = False
    dd_start = 0
    dd_trough_idx = 0
    dd_trough_val = 0.0

    for i in range(len(equity_curve)):
        if drawdowns[i] > 0 and not in_drawdown:
            # Start of new drawdown
            in_drawdown = True
            dd_start = i
            dd_trough_idx = i
            dd_trough_val = equity_curve[i]
        elif drawdowns[i] > 0 and in_drawdown:
            # Continue drawdown, track trough
            if equity_curve[i] < dd_trough_val:
                dd_trough_idx = i
                dd_trough_val = equity_curve[i]
        elif drawdowns[i] == 0 and in_drawdown:
            # End of drawdown (recovery)
            dd_magnitude = peak[dd_start] - dd_trough_val
            if dd_magnitude > 0:
                events.append({
                    "start_idx": dd_start,
                    "trough_idx": dd_trough_idx,
                    "end_idx": i,
                    "magnitude": dd_magnitude,
                    "duration": dd_trough_idx - dd_start,
                    "recovery": i - dd_trough_idx,
                    "total_bars": i - dd_start,
                })
            in_drawdown = False

    # Handle case where still in drawdown at end
    if in_drawdown and dd_trough_idx > dd_start:
        dd_magnitude = peak[dd_start] - dd_trough_val
        events.append({
            "start_idx": dd_start,
            "trough_idx": dd_trough_idx,
            "end_idx": len(equity_curve) - 1,
            "magnitude": dd_magnitude,
            "duration": dd_trough_idx - dd_start,
            "recovery": len(equity_curve) - 1 - dd_trough_idx,
            "total_bars": len(equity_curve) - dd_start,
            "ongoing": True,
        })

    # Find trough indices
    trough_indices = np.array([e["trough_idx"] for e in events]) if events else np.array([])

    # Calculate statistics
    max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0
    dd_values = drawdowns[drawdowns > 0]
    avg_drawdown = float(np.mean(dd_values)) if len(dd_values) > 0 else 0.0
    recoveries = [e["recovery"] for e in events if e.get("recovery", 0) > 0 and not e.get("ongoing", False)]
    avg_recovery = float(np.mean(recoveries)) if recoveries else 0.0

    return {
        "drawdowns": drawdowns,
        "peak_indices": peak_indices,
        "trough_indices": trough_indices,
        "events": events,
        "max_drawdown": max_drawdown,
        "avg_drawdown": avg_drawdown,
        "avg_recovery": avg_recovery,
    }


def calculate_confidence_intervals(
    returns: np.ndarray,
    levels: tuple[float, float] = (0.68, 0.95),
    n_bootstrap: int = 1000,
    seed: int | None = None,
) -> dict[str, np.ndarray]:
    """Calculate confidence intervals for equity curve using bootstrap.

    Args:
        returns: Array of period returns (in R-multiples).
        levels: Confidence levels (default 68% and 95%).
        n_bootstrap: Number of bootstrap samples.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary with:
        - equity_mean: Mean equity curve
        - lower_68, upper_68: 68% CI bounds
        - lower_95, upper_95: 95% CI bounds
    """
    if len(returns) == 0:
        return {
            "equity_mean": np.array([]),
            "lower_68": np.array([]),
            "upper_68": np.array([]),
            "lower_95": np.array([]),
            "upper_95": np.array([]),
        }

    if seed is not None:
        np.random.seed(seed)

    n = len(returns)

    # Generate bootstrap samples
    bootstrap_equities = np.zeros((n_bootstrap, n))
    for i in range(n_bootstrap):
        sample_idx = np.random.choice(n, size=n, replace=True)
        sample_returns = returns[sample_idx]
        bootstrap_equities[i] = np.cumsum(sample_returns)

    # Calculate statistics
    equity_mean = np.mean(bootstrap_equities, axis=0)

    # Calculate percentiles for each level
    lower_68 = np.percentile(bootstrap_equities, (1 - 0.68) / 2 * 100, axis=0)
    upper_68 = np.percentile(bootstrap_equities, (1 + 0.68) / 2 * 100, axis=0)
    lower_95 = np.percentile(bootstrap_equities, (1 - 0.95) / 2 * 100, axis=0)
    upper_95 = np.percentile(bootstrap_equities, (1 + 0.95) / 2 * 100, axis=0)

    return {
        "equity_mean": equity_mean,
        "lower_68": lower_68,
        "upper_68": upper_68,
        "lower_95": lower_95,
        "upper_95": upper_95,
    }


def compute_metrics(
    trades_df: pl.DataFrame,
    initial_capital: float = 10000.0,
    risk_pct: float = 1.0,
) -> dict[str, float]:
    """Calculate performance metrics from a trades dataframe."""
    if trades_df.is_empty():
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "total_r": 0.0,
            "max_drawdown_r": 0.0,
            "profit_factor": 0.0,
            "net_profit_dollar": 0.0,
            "final_capital": initial_capital,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "calmar_ratio": 0.0,
        }

    pnl = trades_df["pnl_r"].to_numpy()
    total_trades = len(pnl)
    wins = np.sum(pnl > 0)
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

    gross_profit = np.sum(pnl[pnl > 0])
    gross_loss = np.abs(np.sum(pnl[pnl < 0]))
    profit_factor = (gross_profit / gross_loss) if gross_loss != 0 else float("inf")

    equity = np.cumsum(pnl)
    peak = np.maximum.accumulate(equity)
    drawdown = peak - equity
    max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0.0

    risk_dollar = initial_capital * (risk_pct / 100.0)
    net_profit_dollar = float(equity[-1] * risk_dollar) if len(equity) > 0 else 0.0
    final_capital = initial_capital + net_profit_dollar

    mean_pnl = np.mean(pnl) if total_trades > 0 else 0.0
    std_pnl = np.std(pnl) if total_trades > 0 else 0.0
    sharpe = mean_pnl / std_pnl if std_pnl > 0 else 0.0

    downside_pnl = pnl[pnl < 0]
    std_downside = np.std(downside_pnl) if len(downside_pnl) > 0 else 0.0
    sortino = mean_pnl / std_downside if std_downside > 0 else 0.0
    calmar = float(equity[-1] / max_drawdown) if max_drawdown > 0 else 0.0

    return {
        "total_trades": total_trades,
        "win_rate": float(win_rate),
        "total_r": float(equity[-1] if len(equity) > 0 else 0.0),
        "max_drawdown_r": float(max_drawdown),
        "profit_factor": float(profit_factor),
        "net_profit_dollar": float(net_profit_dollar),
        "final_capital": float(final_capital),
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
        "calmar_ratio": float(calmar),
    }


__all__ = [
    "compute_metrics",
    "map_ordinal_to_signal",
    "simulate_trades",
    "calculate_rolling_sharpe",
    "analyze_drawdowns",
    "calculate_confidence_intervals",
]
