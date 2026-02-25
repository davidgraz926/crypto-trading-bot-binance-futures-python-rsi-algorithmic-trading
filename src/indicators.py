import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("trading_bot")


def compute_rsi(
    closes: pd.Series, period: int = 14
) -> Optional[float]:
    """Compute the latest RSI value from a series of closing prices.

    Args:
        closes: Series of closing prices (oldest first).
        period: Look-back window for RSI calculation.

    Returns:
        The most recent RSI value, or None if insufficient data.
    """
    if len(closes) < period + 1:
        logger.warning(
            "Not enough data to compute RSI: need %d candles, got %d",
            period + 1,
            len(closes),
        )
        return None

    deltas = closes.diff().dropna()
    gains = deltas.clip(lower=0)
    losses = -deltas.clip(upper=0)

    avg_gain = gains.rolling(window=period, min_periods=period).mean()
    avg_loss = losses.rolling(window=period, min_periods=period).mean()

    latest_gain = avg_gain.iloc[-1]
    latest_loss = avg_loss.iloc[-1]

    if pd.isna(latest_gain) or pd.isna(latest_loss):
        return None
    if latest_loss == 0:
        return 100.0 if latest_gain > 0 else None
    rs = latest_gain / latest_loss
    return 100.0 - (100.0 / (1.0 + rs))
