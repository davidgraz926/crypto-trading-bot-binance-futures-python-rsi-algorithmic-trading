"""RSI (Relative Strength Index) calculation."""

import numpy as np
import pandas as pd


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate the Relative Strength Index for a price series.

    Uses the exponential moving average (Wilder smoothing) method,
    which is the standard RSI calculation.

    Args:
        series: Price series (typically close prices).
        period: Lookback period (default 14).

    Returns:
        Series of RSI values (0-100). The first *period* values will be NaN.

    Raises:
        ValueError: If the series has fewer rows than the period.
    """
    if len(series) < period:
        raise ValueError(
            f"Series length ({len(series)}) must be >= period ({period})"
        )

    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))

    # Replace infinity / NaN from division by zero with boundary values
    rsi = rsi.replace([np.inf, -np.inf], np.nan)

    return rsi
