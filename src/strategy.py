import logging
from enum import Enum
from typing import Optional

import pandas as pd

from config.settings import RSI_OVERBOUGHT, RSI_OVERSOLD, RSI_PERIOD
from src.indicators import compute_rsi

logger = logging.getLogger("trading_bot")


class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


def evaluate(candles: pd.DataFrame) -> tuple[Signal, Optional[float]]:
    """Evaluate the RSI strategy against recent candle data.

    Args:
        candles: DataFrame with at least a 'close' column, oldest first.

    Returns:
        A tuple of (Signal, rsi_value).
    """
    if "close" not in candles.columns:
        logger.error("Candle data missing 'close' column")
        return Signal.HOLD, None

    rsi = compute_rsi(candles["close"], period=RSI_PERIOD)
    if rsi is None:
        logger.info("RSI not available yet, holding")
        return Signal.HOLD, None

    logger.info("RSI=%.2f (oversold=<%d, overbought=>%d)", rsi, RSI_OVERSOLD, RSI_OVERBOUGHT)

    if rsi < RSI_OVERSOLD:
        return Signal.BUY, rsi
    if rsi > RSI_OVERBOUGHT:
        return Signal.SELL, rsi
    return Signal.HOLD, rsi
