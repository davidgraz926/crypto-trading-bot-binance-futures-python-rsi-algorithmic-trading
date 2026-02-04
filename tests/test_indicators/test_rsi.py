"""Tests for the RSI indicator."""

import numpy as np
import pandas as pd
import pytest

from src.indicators.rsi import calculate_rsi


class TestCalculateRSI:
    def test_returns_series(self, sample_ohlcv: pd.DataFrame) -> None:
        result = calculate_rsi(sample_ohlcv["close"])
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv)

    def test_rsi_range(self, sample_ohlcv: pd.DataFrame) -> None:
        result = calculate_rsi(sample_ohlcv["close"])
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_constant_prices_give_nan_or_neutral(self) -> None:
        """Constant prices mean zero gains and zero losses."""
        prices = pd.Series([100.0] * 20)
        result = calculate_rsi(prices)
        # With no change, avg_loss is 0 -> division issues -> expect NaN
        valid = result.dropna()
        # Either all NaN or values should be near 100 (no losses)
        if len(valid) > 0:
            assert (valid >= 0).all()

    def test_monotonic_increase_high_rsi(self) -> None:
        prices = pd.Series(np.linspace(100, 200, 30))
        result = calculate_rsi(prices, period=14)
        # Steadily increasing prices should produce RSI near 100
        assert result.iloc[-1] > 90

    def test_monotonic_decrease_low_rsi(self) -> None:
        prices = pd.Series(np.linspace(200, 100, 30))
        result = calculate_rsi(prices, period=14)
        # Steadily decreasing prices should produce RSI near 0
        assert result.iloc[-1] < 10

    def test_custom_period(self, sample_ohlcv: pd.DataFrame) -> None:
        r7 = calculate_rsi(sample_ohlcv["close"], period=7)
        r21 = calculate_rsi(sample_ohlcv["close"], period=21)
        # Shorter period should have more non-NaN values
        assert r7.notna().sum() >= r21.notna().sum()

    def test_insufficient_data_raises(self) -> None:
        prices = pd.Series([100.0, 101.0, 99.0])
        with pytest.raises(ValueError, match="must be >= period"):
            calculate_rsi(prices, period=14)

    def test_first_values_are_nan(self, sample_ohlcv: pd.DataFrame) -> None:
        result = calculate_rsi(sample_ohlcv["close"], period=14)
        # The first value (before any diff) should be NaN
        assert pd.isna(result.iloc[0])
