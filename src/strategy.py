import logging
from enum import Enum
from typing import Optional

import pandas as pd

from config import settings
from src.indicators import latest_rsi

logger = logging.getLogger("trading_bot")


class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class RSIStrategy:
    """RSI-based trading strategy.

    Generates a BUY signal when RSI falls below the oversold threshold and a
    SELL signal when RSI rises above the overbought threshold.
    """

    def __init__(
        self,
        period: int = settings.RSI_PERIOD,
        overbought: float = settings.RSI_OVERBOUGHT,
        oversold: float = settings.RSI_OVERSOLD,
    ) -> None:
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def evaluate(self, closes: pd.Series) -> Signal:
        """Evaluate the strategy against a series of closing prices.

        Returns:
            A Signal indicating the recommended action.
        """
        rsi: Optional[float] = latest_rsi(closes, self.period)
        if rsi is None:
            logger.warning("Insufficient data for RSI calculation")
            return Signal.HOLD

        logger.info("Current RSI: %.2f", rsi)

        if rsi < self.oversold:
            logger.info("RSI %.2f < %.2f (oversold) -> BUY signal", rsi, self.oversold)
            return Signal.BUY

        if rsi > self.overbought:
            logger.info(
                "RSI %.2f > %.2f (overbought) -> SELL signal", rsi, self.overbought
            )
            return Signal.SELL

        logger.info("RSI %.2f in neutral zone -> HOLD", rsi)
        return Signal.HOLD
