"""Shared pytest fixtures."""

import numpy as np
import pandas as pd
import pytest

from config.settings import Settings


@pytest.fixture
def settings() -> Settings:
    """Return a Settings instance with testnet defaults."""
    return Settings(
        binance_api_key="test_key",
        binance_api_secret="test_secret",
        use_testnet=True,
    )


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    """Return a simple OHLCV DataFrame with 30 rows."""
    np.random.seed(42)
    n = 30
    close = 50000 + np.cumsum(np.random.randn(n) * 100)
    return pd.DataFrame(
        {
            "open_time": pd.date_range("2025-01-01", periods=n, freq="h"),
            "open": close - np.random.rand(n) * 50,
            "high": close + np.random.rand(n) * 50,
            "low": close - np.random.rand(n) * 50,
            "close": close,
            "volume": np.random.rand(n) * 1000,
        }
    )


@pytest.fixture
def oversold_data() -> pd.DataFrame:
    """Return OHLCV data engineered to produce oversold RSI (< 30)."""
    n = 30
    # Steady decline to push RSI below 30
    close = np.linspace(50000, 45000, n)
    # Add a slight uptick at the end so RSI crosses above oversold
    close[-1] = close[-2] + 200
    return pd.DataFrame(
        {
            "open_time": pd.date_range("2025-01-01", periods=n, freq="h"),
            "open": close,
            "high": close + 10,
            "low": close - 10,
            "close": close,
            "volume": np.full(n, 100.0),
        }
    )


@pytest.fixture
def overbought_data() -> pd.DataFrame:
    """Return OHLCV data engineered to produce overbought RSI (> 70)."""
    n = 30
    # Steady rise to push RSI above 70
    close = np.linspace(45000, 50000, n)
    # Add a slight downtick at the end so RSI crosses below overbought
    close[-1] = close[-2] - 200
    return pd.DataFrame(
        {
            "open_time": pd.date_range("2025-01-01", periods=n, freq="h"),
            "open": close,
            "high": close + 10,
            "low": close - 10,
            "close": close,
            "volume": np.full(n, 100.0),
        }
    )
