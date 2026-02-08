import numpy as np
import pandas as pd
import pytest

from src.indicators import compute_rsi, latest_rsi


def _make_closes(values: list[float]) -> pd.Series:
    return pd.Series(values, dtype=float)


class TestComputeRSI:
    def test_returns_series_of_same_length(self) -> None:
        closes = _make_closes([45 + i * 0.5 for i in range(30)])
        rsi = compute_rsi(closes, period=14)
        assert len(rsi) == len(closes)

    def test_rsi_bounded_between_0_and_100(self) -> None:
        np.random.seed(42)
        prices = list(np.cumsum(np.random.randn(100)) + 100)
        closes = _make_closes(prices)
        rsi = compute_rsi(closes, period=14).dropna()
        assert (rsi >= 0).all()
        assert (rsi <= 100).all()

    def test_monotonically_rising_prices_give_high_rsi(self) -> None:
        closes = _make_closes([100 + i for i in range(30)])
        rsi = compute_rsi(closes, period=14)
        assert rsi.iloc[-1] > 90

    def test_monotonically_falling_prices_give_low_rsi(self) -> None:
        closes = _make_closes([200 - i for i in range(30)])
        rsi = compute_rsi(closes, period=14)
        assert rsi.iloc[-1] < 10

    def test_insufficient_data_returns_nan(self) -> None:
        closes = _make_closes([100, 101, 102])
        rsi = compute_rsi(closes, period=14)
        assert rsi.isna().all()

    def test_custom_period(self) -> None:
        # Use noisy data so RSI doesn't saturate to 100 for both periods
        np.random.seed(123)
        noise = np.random.randn(50) * 2
        prices = [50 + i * 0.3 + noise[i] for i in range(50)]
        closes = _make_closes(prices)
        rsi_7 = compute_rsi(closes, period=7)
        rsi_21 = compute_rsi(closes, period=21)
        # Both should be valid (non-NaN) and different
        assert not pd.isna(rsi_7.iloc[-1])
        assert not pd.isna(rsi_21.iloc[-1])
        assert rsi_7.iloc[-1] != rsi_21.iloc[-1]


class TestLatestRSI:
    def test_returns_float_with_sufficient_data(self) -> None:
        closes = _make_closes([50 + i * 0.5 for i in range(30)])
        result = latest_rsi(closes, period=14)
        assert isinstance(result, float)

    def test_returns_none_with_insufficient_data(self) -> None:
        closes = _make_closes([100, 101])
        result = latest_rsi(closes, period=14)
        assert result is None

    def test_matches_last_value_of_compute_rsi(self) -> None:
        closes = _make_closes([80 + i * 0.2 for i in range(40)])
        full = compute_rsi(closes, period=14)
        single = latest_rsi(closes, period=14)
        assert single == pytest.approx(full.iloc[-1])
