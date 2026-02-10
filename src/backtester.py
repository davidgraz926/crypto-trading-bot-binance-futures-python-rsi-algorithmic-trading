import logging
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
import pandas as pd

from src.indicators import compute_rsi
from src.strategy import RSIStrategy, Signal

logger = logging.getLogger("trading_bot")


@dataclass
class Trade:
    """Record of a single completed trade."""

    entry_index: int
    exit_index: int
    side: str  # "BUY" (long) or "SELL" (short)
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    exit_reason: str  # "signal", "stop_loss", "take_profit"


@dataclass
class BacktestResult:
    """Summary of a backtest run."""

    trades: List[Trade]
    initial_balance: float
    final_balance: float
    total_return_pct: float
    win_rate: float
    total_trades: int
    max_drawdown_pct: float
    sharpe_ratio: float
    equity_curve: List[float]


@dataclass
class _Position:
    """Internal representation of an open position during simulation."""

    side: str
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    entry_index: int


class Backtester:
    """Simulates a trading strategy against historical OHLCV data.

    Walks through the data bar-by-bar, evaluates the strategy, sizes
    positions using risk parameters, and enforces stop-loss / take-profit
    exits using intra-bar high/low prices.
    """

    def __init__(
        self,
        strategy: RSIStrategy,
        initial_balance: float = 10_000.0,
        max_position_pct: float = 0.02,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.04,
        leverage: int = 1,
        commission_pct: float = 0.0004,  # 0.04% taker fee
    ) -> None:
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.max_position_pct = max_position_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.leverage = leverage
        self.commission_pct = commission_pct

    def run(self, df: pd.DataFrame) -> BacktestResult:
        """Execute the backtest on a DataFrame with OHLCV columns.

        The DataFrame must contain at least 'open', 'high', 'low', 'close'
        columns with numeric values.

        Args:
            df: Historical OHLCV data (one row per bar).

        Returns:
            A BacktestResult with performance metrics and trade log.
        """
        closes: pd.Series = df["close"]
        highs: pd.Series = df["high"]
        lows: pd.Series = df["low"]

        balance = self.initial_balance
        position: Optional[_Position] = None
        trades: List[Trade] = []
        equity_curve: List[float] = []

        min_bars = self.strategy.period + 1

        for i in range(len(df)):
            current_close = closes.iloc[i]

            # -- check stop-loss / take-profit on open positions --
            if position is not None:
                bar_low = lows.iloc[i]
                bar_high = highs.iloc[i]
                exit_price: Optional[float] = None
                exit_reason = ""

                if position.side == "BUY":
                    if bar_low <= position.stop_loss:
                        exit_price = position.stop_loss
                        exit_reason = "stop_loss"
                    elif bar_high >= position.take_profit:
                        exit_price = position.take_profit
                        exit_reason = "take_profit"
                else:  # SHORT
                    if bar_high >= position.stop_loss:
                        exit_price = position.stop_loss
                        exit_reason = "stop_loss"
                    elif bar_low <= position.take_profit:
                        exit_price = position.take_profit
                        exit_reason = "take_profit"

                if exit_price is not None:
                    trade = self._close_position(position, exit_price, i, exit_reason)
                    balance += trade.pnl - (exit_price * trade.quantity * self.commission_pct)
                    trades.append(trade)
                    position = None

            # -- evaluate strategy signal --
            if i >= min_bars and position is None:
                history = closes.iloc[: i + 1]
                signal = self.strategy.evaluate(history)

                if signal in (Signal.BUY, Signal.SELL):
                    entry_price = current_close
                    quantity = (balance * self.max_position_pct * self.leverage) / entry_price
                    if quantity > 0:
                        side = signal.value
                        sl = self._calc_sl(entry_price, side)
                        tp = self._calc_tp(entry_price, side)
                        commission = entry_price * quantity * self.commission_pct
                        balance -= commission
                        position = _Position(
                            side=side,
                            entry_price=entry_price,
                            quantity=quantity,
                            stop_loss=sl,
                            take_profit=tp,
                            entry_index=i,
                        )

            # -- handle opposing signal while in position --
            if i >= min_bars and position is not None:
                history = closes.iloc[: i + 1]
                signal = self.strategy.evaluate(history)

                if (position.side == "BUY" and signal == Signal.SELL) or (
                    position.side == "SELL" and signal == Signal.BUY
                ):
                    trade = self._close_position(position, current_close, i, "signal")
                    balance += trade.pnl - (current_close * trade.quantity * self.commission_pct)
                    trades.append(trade)
                    position = None

            # -- record equity --
            mark_to_market = balance
            if position is not None:
                unrealised = self._unrealised_pnl(position, current_close)
                mark_to_market += unrealised
            equity_curve.append(mark_to_market)

        # close any remaining position at last close
        if position is not None:
            trade = self._close_position(
                position, closes.iloc[-1], len(df) - 1, "end_of_data"
            )
            balance += trade.pnl - (closes.iloc[-1] * trade.quantity * self.commission_pct)
            trades.append(trade)
            equity_curve[-1] = balance

        return self._build_result(trades, balance, equity_curve)

    # -- private helpers --

    def _calc_sl(self, entry_price: float, side: str) -> float:
        if side == "BUY":
            return entry_price * (1 - self.stop_loss_pct)
        return entry_price * (1 + self.stop_loss_pct)

    def _calc_tp(self, entry_price: float, side: str) -> float:
        if side == "BUY":
            return entry_price * (1 + self.take_profit_pct)
        return entry_price * (1 - self.take_profit_pct)

    def _unrealised_pnl(self, pos: _Position, current_price: float) -> float:
        if pos.side == "BUY":
            return (current_price - pos.entry_price) * pos.quantity
        return (pos.entry_price - current_price) * pos.quantity

    @staticmethod
    def _close_position(
        pos: _Position, exit_price: float, exit_index: int, reason: str
    ) -> Trade:
        if pos.side == "BUY":
            pnl = (exit_price - pos.entry_price) * pos.quantity
        else:
            pnl = (pos.entry_price - exit_price) * pos.quantity
        pnl_pct = (exit_price / pos.entry_price - 1) * 100
        if pos.side == "SELL":
            pnl_pct = -pnl_pct
        return Trade(
            entry_index=pos.entry_index,
            exit_index=exit_index,
            side=pos.side,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            quantity=pos.quantity,
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason=reason,
        )

    def _build_result(
        self,
        trades: List[Trade],
        final_balance: float,
        equity_curve: List[float],
    ) -> BacktestResult:
        total_trades = len(trades)
        wins = sum(1 for t in trades if t.pnl > 0)
        win_rate = wins / total_trades if total_trades > 0 else 0.0
        total_return_pct = (
            (final_balance - self.initial_balance) / self.initial_balance * 100
        )
        max_drawdown_pct = self._max_drawdown(equity_curve)
        sharpe = self._sharpe_ratio(equity_curve)

        return BacktestResult(
            trades=trades,
            initial_balance=self.initial_balance,
            final_balance=round(final_balance, 2),
            total_return_pct=round(total_return_pct, 2),
            win_rate=round(win_rate, 4),
            total_trades=total_trades,
            max_drawdown_pct=round(max_drawdown_pct, 2),
            sharpe_ratio=round(sharpe, 4),
            equity_curve=equity_curve,
        )

    @staticmethod
    def _max_drawdown(equity_curve: List[float]) -> float:
        if len(equity_curve) < 2:
            return 0.0
        peak = equity_curve[0]
        max_dd = 0.0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return max_dd

    @staticmethod
    def _sharpe_ratio(equity_curve: List[float], periods_per_year: int = 252) -> float:
        if len(equity_curve) < 2:
            return 0.0
        eq = np.array(equity_curve)
        returns = np.diff(eq) / eq[:-1]
        if np.std(returns) == 0:
            return 0.0
        return float(np.mean(returns) / np.std(returns) * np.sqrt(periods_per_year))
