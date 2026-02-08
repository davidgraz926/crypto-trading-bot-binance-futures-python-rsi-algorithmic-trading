import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("trading_bot")


def compute_rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    """Compute the Relative Strength Index for a series of closing prices.

    Uses the exponential (Wilder's) smoothing method.

    Args:
        closes: Series of closing prices.
        period: Look-back period for the RSI calculation.

    Returns:
        A pandas Series containing RSI values (0-100).
    """
    if len(closes) < period + 1:
        return pd.Series(np.nan, index=closes.index)

    delta = closes.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))

    return rsi


def latest_rsi(closes: pd.Series, period: int = 14) -> Optional[float]:
    """Return the most recent RSI value, or None if insufficient data."""
    rsi_series = compute_rsi(closes, period)
    if rsi_series.empty or pd.isna(rsi_series.iloc[-1]):
        return None
    return float(rsi_series.iloc[-1])
