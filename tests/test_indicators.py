import numpy as np
import pandas as pd

from src.indicators import compute_rsi


def _make_closes(values: list[float]) -> pd.Series:
    return pd.Series(values, dtype=float)


class TestComputeRSI:
    def test_returns_none_when_insufficient_data(self) -> None:
        closes = _make_closes([100.0] * 5)
        assert compute_rsi(closes, period=14) is None

    def test_returns_float_with_enough_data(self) -> None:
        np.random.seed(42)
        prices = list(np.cumsum(np.random.randn(50)) + 100)
        result = compute_rsi(_make_closes(prices), period=14)
        assert result is not None
        assert 0 <= result <= 100

    def test_monotonic_up_gives_high_rsi(self) -> None:
        closes = _make_closes([float(i) for i in range(1, 30)])
        rsi = compute_rsi(closes, period=14)
        assert rsi is not None
        assert rsi > 70

    def test_monotonic_down_gives_low_rsi(self) -> None:
        closes = _make_closes([float(100 - i) for i in range(30)])
        rsi = compute_rsi(closes, period=14)
        assert rsi is not None
        assert rsi < 30

    def test_flat_prices_return_none(self) -> None:
        # All same price -> zero gains and zero losses -> RS is NaN
        closes = _make_closes([50.0] * 20)
        rsi = compute_rsi(closes, period=14)
        assert rsi is None
