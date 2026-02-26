import logging
from enum import Enum
from typing import Optional

import pandas as pd

from config.settings import RSI_OVERBOUGHT, RSI_OVERSOLD, RSI_PERIOD, MEV_PRESSURE_WEIGHT
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


# Combined signal thresholds (on the -100 to +100 scale)
_BUY_THRESHOLD = 40.0
_SELL_THRESHOLD = -40.0


def evaluate_with_mev(
    candles: pd.DataFrame,
    mev_pressure: Optional[float] = None,
    mev_weight: float = MEV_PRESSURE_WEIGHT,
) -> tuple[Signal, Optional[float], Optional[float]]:
    """Evaluate combined RSI + MEV pressure strategy.

    Args:
        candles: DataFrame with at least a 'close' column, oldest first.
        mev_pressure: MEV pressure score from -100 to +100. None if unavailable.
        mev_weight: Weight of MEV signal in combined score (0.0 to 1.0).

    Returns:
        A tuple of (Signal, rsi_value, combined_score).
    """
    if "close" not in candles.columns:
        logger.error("Candle data missing 'close' column")
        return Signal.HOLD, None, None

    rsi = compute_rsi(candles["close"], period=RSI_PERIOD)
    if rsi is None:
        logger.info("RSI not available yet, holding")
        return Signal.HOLD, None, None

    # Map RSI (0-100) to directional score (-100 to +100)
    # RSI 0 (extremely oversold) -> +100 (strong buy signal)
    # RSI 50 (neutral) -> 0
    # RSI 100 (extremely overbought) -> -100 (strong sell signal)
    rsi_score = -1.0 * (rsi - 50.0) * 2.0

    if mev_pressure is not None:
        combined = (1.0 - mev_weight) * rsi_score + mev_weight * mev_pressure
    else:
        combined = rsi_score

    combined = max(-100.0, min(100.0, combined))

    logger.info(
        "RSI=%.2f score=%.2f, MEV=%s, combined=%.2f",
        rsi,
        rsi_score,
        f"{mev_pressure:.2f}" if mev_pressure is not None else "N/A",
        combined,
    )

    if combined > _BUY_THRESHOLD:
        return Signal.BUY, rsi, combined
    if combined < _SELL_THRESHOLD:
        return Signal.SELL, rsi, combined
    return Signal.HOLD, rsi, combined
