"""RSI-based trading strategy."""

import logging

import pandas as pd

from src.indicators.rsi import calculate_rsi
from src.strategies.base import BaseStrategy, Signal, SignalType

logger = logging.getLogger("trading_bot")


class RSIStrategy(BaseStrategy):
    """Trading strategy based on RSI crossovers.

    Opens a long position when RSI crosses above the oversold threshold
    and a short position when RSI crosses below the overbought threshold.
    Signals to close positions when RSI reaches the opposite extreme.

    Args:
        period: RSI lookback period.
        overbought: RSI level considered overbought.
        oversold: RSI level considered oversold.
    """

    def __init__(
        self,
        period: int = 14,
        overbought: float = 70.0,
        oversold: float = 30.0,
    ) -> None:
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """Generate a trading signal from OHLCV data.

        Expects *data* to contain a ``close`` column with at least
        ``period + 1`` rows.
        """
        rsi_values = calculate_rsi(data["close"], self.period)

        current_rsi = rsi_values.iloc[-1]
        prev_rsi = rsi_values.iloc[-2]

        if pd.isna(current_rsi) or pd.isna(prev_rsi):
            return Signal(SignalType.HOLD, "Insufficient data for RSI")

        logger.debug("RSI: current=%.2f  prev=%.2f", current_rsi, prev_rsi)

        # Long entry: RSI crosses above oversold level
        if prev_rsi <= self.oversold < current_rsi:
            return Signal(
                SignalType.LONG,
                f"RSI crossed above oversold ({self.oversold}): {current_rsi:.2f}",
            )

        # Short entry: RSI crosses below overbought level
        if prev_rsi >= self.overbought > current_rsi:
            return Signal(
                SignalType.SHORT,
                f"RSI crossed below overbought ({self.overbought}): {current_rsi:.2f}",
            )

        # Close long: RSI reaches overbought
        if current_rsi >= self.overbought:
            return Signal(
                SignalType.CLOSE_LONG,
                f"RSI reached overbought ({self.overbought}): {current_rsi:.2f}",
            )

        # Close short: RSI reaches oversold
        if current_rsi <= self.oversold:
            return Signal(
                SignalType.CLOSE_SHORT,
                f"RSI reached oversold ({self.oversold}): {current_rsi:.2f}",
            )

        return Signal(SignalType.HOLD, f"RSI neutral: {current_rsi:.2f}")
