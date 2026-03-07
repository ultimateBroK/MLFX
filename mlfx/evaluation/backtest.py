"""Walk-forward backtesting engine for evaluating trading signals."""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

logger = logging.getLogger(__name__)


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


__all__ = ["compute_metrics", "simulate_trades"]
