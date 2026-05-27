"""Tests for technical indicator calculations."""

import numpy as np
import pandas as pd
import pytest

from src.indicators import (
    add_all_indicators,
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_volume_sma,
)


@pytest.fixture
def sample_ohlcv():
    """Generate realistic OHLCV data for testing."""
    np.random.seed(42)
    n = 300
    close = 50000 + np.cumsum(np.random.randn(n) * 100)
    high = close + np.abs(np.random.randn(n) * 50)
    low = close - np.abs(np.random.randn(n) * 50)
    open_ = close + np.random.randn(n) * 30
    volume = np.abs(np.random.randn(n) * 1000) + 500

    return pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


class TestRSI:
    def test_rsi_range(self, sample_ohlcv):
        """RSI should be between 0 and 100."""
        rsi = calculate_rsi(sample_ohlcv, period=14)
        valid = rsi.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_rsi_length(self, sample_ohlcv):
        """RSI series should be same length as input."""
        rsi = calculate_rsi(sample_ohlcv, period=14)
        assert len(rsi) == len(sample_ohlcv)

    def test_rsi_with_uptrend(self):
        """RSI should be high in a strong uptrend."""
        # Need enough data points and some noise for EWM to produce non-NaN values
        np.random.seed(99)
        base = np.linspace(100, 300, 200)
        noise = np.random.randn(200) * 0.5
        prices = pd.DataFrame({"close": base + noise})
        rsi = calculate_rsi(prices, period=14)
        assert rsi.iloc[-1] > 70

    def test_rsi_with_downtrend(self):
        """RSI should be low in a strong downtrend."""
        prices = pd.DataFrame({"close": np.linspace(200, 100, 100)})
        rsi = calculate_rsi(prices, period=14)
        assert rsi.iloc[-1] < 30


class TestMACD:
    def test_macd_returns_three_series(self, sample_ohlcv):
        macd, signal, hist = calculate_macd(sample_ohlcv)
        assert len(macd) == len(sample_ohlcv)
        assert len(signal) == len(sample_ohlcv)
        assert len(hist) == len(sample_ohlcv)

    def test_histogram_is_difference(self, sample_ohlcv):
        """Histogram should be MACD line minus signal line."""
        macd, signal, hist = calculate_macd(sample_ohlcv)
        valid_idx = macd.dropna().index
        diff = (macd[valid_idx] - signal[valid_idx] - hist[valid_idx]).abs()
        assert (diff < 1e-10).all()

    def test_macd_crossover_detection(self):
        """MACD should cross signal line in a trend reversal."""
        # Create data that goes up then down
        prices = np.concatenate([
            np.linspace(100, 200, 100),
            np.linspace(200, 100, 100),
        ])
        df = pd.DataFrame({"close": prices})
        macd, signal, hist = calculate_macd(df, fast=12, slow=26, signal=9)
        # Histogram should change sign somewhere during reversal
        signs = np.sign(hist.dropna().values)
        assert not np.all(signs == signs[0])  # Should not all be the same sign


class TestEMA:
    def test_ema_follows_price(self, sample_ohlcv):
        ema = calculate_ema(sample_ohlcv, period=50)
        assert len(ema) == len(sample_ohlcv)
        # EMA should be close to price (not wildly different)
        ratio = (ema.dropna() / sample_ohlcv["close"].loc[ema.dropna().index])
        assert (ratio > 0.9).all()
        assert (ratio < 1.1).all()

    def test_shorter_ema_more_responsive(self):
        """Shorter EMA should track a sudden move faster than longer EMA."""
        # Flat then sudden jump - short EMA should catch up faster
        flat = [100.0] * 100
        jump = [200.0] * 20
        prices = pd.DataFrame({"close": flat + jump})
        ema_short = calculate_ema(prices, period=10)
        ema_long = calculate_ema(prices, period=50)
        latest = prices["close"].iloc[-1]
        assert abs(ema_short.iloc[-1] - latest) < abs(ema_long.iloc[-1] - latest)


class TestBollingerBands:
    def test_bands_structure(self, sample_ohlcv):
        upper, middle, lower = calculate_bollinger_bands(sample_ohlcv)
        valid = upper.dropna().index
        assert (upper[valid] >= middle[valid]).all()
        assert (middle[valid] >= lower[valid]).all()

    def test_price_within_bands_mostly(self, sample_ohlcv):
        """Most prices should fall within the bands."""
        upper, middle, lower = calculate_bollinger_bands(sample_ohlcv, period=20, std_dev=2.0)
        valid = upper.dropna().index
        close = sample_ohlcv["close"][valid]
        within = ((close >= lower[valid]) & (close <= upper[valid])).mean()
        assert within > 0.85  # At least 85% within 2 std dev bands


class TestATR:
    def test_atr_positive(self, sample_ohlcv):
        atr = calculate_atr(sample_ohlcv)
        valid = atr.dropna()
        assert (valid > 0).all()

    def test_atr_length(self, sample_ohlcv):
        atr = calculate_atr(sample_ohlcv)
        assert len(atr) == len(sample_ohlcv)


class TestVolumeSMA:
    def test_volume_sma(self, sample_ohlcv):
        vol_sma = calculate_volume_sma(sample_ohlcv, period=20)
        valid = vol_sma.dropna()
        assert (valid > 0).all()


class TestAddAllIndicators:
    def test_all_columns_added(self, sample_ohlcv):
        result = add_all_indicators(sample_ohlcv)
        expected_cols = [
            "rsi", "macd", "macd_signal", "macd_hist",
            "ema_short", "ema_long",
            "bb_upper", "bb_middle", "bb_lower",
            "atr", "volume_sma", "volume_ratio",
        ]
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_original_not_modified(self, sample_ohlcv):
        """add_all_indicators should not modify the original DataFrame."""
        original_cols = set(sample_ohlcv.columns)
        add_all_indicators(sample_ohlcv)
        assert set(sample_ohlcv.columns) == original_cols
