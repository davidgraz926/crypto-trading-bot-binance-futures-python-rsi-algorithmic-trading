"""
Technical indicator calculations.
All indicators operate on pandas DataFrames with OHLCV columns.
"""

import logging

import numpy as np
import pandas as pd

from config import settings

logger = logging.getLogger("trading_bot.indicators")


def calculate_rsi(df: pd.DataFrame, period: int = 0, column: str = "close") -> pd.Series:
    """
    Calculate Relative Strength Index.

    RSI = 100 - (100 / (1 + RS))
    RS = average gain / average loss over the period
    """
    period = period or settings.RSI_PERIOD
    delta = df[column].diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    # Use exponential moving average (Wilder's smoothing)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))

    return rsi


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 0,
    slow: int = 0,
    signal: int = 0,
    column: str = "close",
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Returns:
        (macd_line, signal_line, histogram)
    """
    fast = fast or settings.MACD_FAST
    slow = slow or settings.MACD_SLOW
    signal = signal or settings.MACD_SIGNAL

    ema_fast = df[column].ewm(span=fast, adjust=False).mean()
    ema_slow = df[column].ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_ema(
    df: pd.DataFrame,
    period: int = 50,
    column: str = "close",
) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return df[column].ewm(span=period, adjust=False).mean()


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 0,
    std_dev: float = 0.0,
    column: str = "close",
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.

    Returns:
        (upper_band, middle_band, lower_band)
    """
    period = period or settings.BOLLINGER_PERIOD
    std_dev = std_dev or settings.BOLLINGER_STD_DEV

    middle = df[column].rolling(window=period).mean()
    rolling_std = df[column].rolling(window=period).std()

    upper = middle + (rolling_std * std_dev)
    lower = middle - (rolling_std * std_dev)

    return upper, middle, lower


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (used for stop-loss placement and volatility).
    """
    high = df["high"]
    low = df["low"]
    close = df["close"].shift(1)

    tr1 = high - low
    tr2 = (high - close).abs()
    tr3 = (low - close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.ewm(alpha=1.0 / period, min_periods=period).mean()

    return atr


def calculate_volume_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Calculate Simple Moving Average of volume for volume confirmation."""
    return df["volume"].rolling(window=period).mean()


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all indicators and add them as columns to the DataFrame.
    This is the main function strategies should call.
    """
    df = df.copy()

    # RSI
    df["rsi"] = calculate_rsi(df)

    # MACD
    df["macd"], df["macd_signal"], df["macd_hist"] = calculate_macd(df)

    # EMAs
    df["ema_short"] = calculate_ema(df, period=settings.EMA_SHORT)
    df["ema_long"] = calculate_ema(df, period=settings.EMA_LONG)

    # Bollinger Bands
    df["bb_upper"], df["bb_middle"], df["bb_lower"] = calculate_bollinger_bands(df)

    # ATR for volatility-based stops
    df["atr"] = calculate_atr(df)

    # Volume SMA for volume confirmation
    df["volume_sma"] = calculate_volume_sma(df)
    df["volume_ratio"] = df["volume"] / df["volume_sma"]

    logger.debug("All indicators calculated (%d rows)", len(df))
    return df
