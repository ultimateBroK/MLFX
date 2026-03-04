"""
eval/backtest.py
================
Walk-forward backtesting engine for evaluating trading signals.

Uses R-multiples (Risk/Reward) to evaluate strategy performance
without requiring absolute dollar amounts.

Output: Trade log DataFrame and summary performance metrics.
"""

from __future__ import annotations

import logging

import polars as pl
import numpy as np

logger = logging.getLogger(__name__)


def simulate_trades(
    df: pl.DataFrame,
    signal_col: str,
    tp_r: float = 2.0,
    sl_r: float = 1.0,
    horizon_limit: int = 10,
    atr_col: str = "atr_14",
    atr_mult: float = 0.5,
) -> pl.DataFrame:
    """
    Simulate trades sequentially based on signals.
    A trade triggers on signal=+1 (LONG) or -1 (SHORT).

    Rules:
      - Entry price is the OPEN of the NEXT bar.
      - SL/TP distances are derived from the ATR of the signal bar.
      - Trade closes if high/low hits TP/SL, or if `horizon_limit` is reached.
      - Sequential non-overlapping: ignores new signals while in a trade.

    Args:
        df:            OHLCV DataFrame containing signals and ATR.
        signal_col:    The column containing -1 (SHORT), 0 (NEUTRAL), 1 (LONG).
        tp_r:          Take Profit multiplier (e.g., 2.0 for 1:2 Risk/Reward).
        sl_r:          Stop Loss multiplier (e.g., 1.0).
        horizon_limit: Maximum bars to hold trade.
        atr_col:       ATR column for setting SL/TP distances.
        atr_mult:      ATR risk basis. Base risk distance = `atr_mult * atr`.

    Returns:
        DataFrame of completed trades with PnL.
    """
    if signal_col not in df.columns or atr_col not in df.columns:
        logger.error(
            f"Missing required columns ({signal_col} or {atr_col}) in DataFrame."
        )
        return pl.DataFrame()

    records = df.to_dicts()
    n = len(records)

    trades = []
    in_trade = False
    entry_price = 0.0
    entry_tag = ""
    entry_idx = 0
    sl_price = 0.0
    tp_price = 0.0
    risk_dist = 0.0
    entry_timestamp = None

    for i in range(n - 1):
        row = records[i]

        # 1. Check if we should exit an active trade
        if in_trade:
            next_row = records[i + 1]
            high, low = next_row["high"], next_row["low"]
            bars_held = (i + 1) - entry_idx

            exit_price = None
            pnl_r = 0.0
            reason = ""

            # Check SL/TP hits
            if entry_tag == "LONG":
                if low <= sl_price:
                    exit_price = sl_price
                    pnl_r = -sl_r
                    reason = "SL"
                elif high >= tp_price:
                    exit_price = tp_price
                    pnl_r = tp_r
                    reason = "TP"
            else:  # SHORT
                if high >= sl_price:
                    exit_price = sl_price
                    pnl_r = -sl_r
                    reason = "SL"
                elif low <= tp_price:
                    exit_price = tp_price
                    pnl_r = tp_r
                    reason = "TP"

            # Time limit exit
            if exit_price is None and bars_held >= horizon_limit:
                exit_price = next_row["close"]
                # Calculate actual R multiple based on closing price vs risk
                if risk_dist > 0:
                    if entry_tag == "LONG":
                        pnl_r = (exit_price - entry_price) / risk_dist
                    else:
                        pnl_r = (entry_price - exit_price) / risk_dist
                reason = "TIME"

            if exit_price is not None:
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
                        # Context for heatmap
                        "weekday": entry_timestamp.weekday()
                        if entry_timestamp
                        else 0,  # 0=Mon
                        "hour": entry_timestamp.hour if entry_timestamp else 0,
                    }
                )
                in_trade = False
                continue

        # 2. Open new trade
        if not in_trade:
            sig = row[signal_col]
            if sig in (1, -1) and row[atr_col] is not None:
                next_row = records[i + 1]  # enter next open
                in_trade = True
                entry_idx = i + 1
                entry_timestamp = next_row["timestamp"]
                entry_price = next_row["open"]

                risk_dist = row[atr_col] * atr_mult

                if sig == 1:
                    entry_tag = "LONG"
                    sl_price = entry_price - (risk_dist * sl_r)
                    tp_price = entry_price + (risk_dist * tp_r)
                else:
                    entry_tag = "SHORT"
                    sl_price = entry_price + (risk_dist * sl_r)
                    tp_price = entry_price - (risk_dist * tp_r)

    tdf = pl.DataFrame(trades)
    return tdf


def compute_metrics(trades_df: pl.DataFrame) -> dict:
    """Calculate performance metrics from a trades DataFrame."""
    if trades_df.is_empty():
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "total_r": 0.0,
            "max_drawdown_r": 0.0,
            "profit_factor": 0.0,
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
    max_dd = np.max(drawdown) if len(drawdown) > 0 else 0.0

    return {
        "total_trades": total_trades,
        "win_rate": float(win_rate),
        "total_r": float(equity[-1] if len(equity) > 0 else 0.0),
        "max_drawdown_r": float(max_dd),
        "profit_factor": float(profit_factor),
    }
