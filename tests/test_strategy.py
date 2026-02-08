import pandas as pd

from src.strategy import RSIStrategy, Signal


def _oversold_closes() -> pd.Series:
    """Generate a series of prices that produce an RSI well below 30."""
    return pd.Series([200 - i for i in range(30)], dtype=float)


def _overbought_closes() -> pd.Series:
    """Generate a series of prices that produce an RSI well above 70."""
    return pd.Series([100 + i for i in range(30)], dtype=float)


def _neutral_closes() -> pd.Series:
    """Generate a series of prices that produce an RSI near 50."""
    # Alternating up/down around a base keeps RSI near the midpoint
    return pd.Series([100 + (i % 2) for i in range(30)], dtype=float)


class TestRSIStrategy:
    def test_buy_signal_when_oversold(self) -> None:
        strategy = RSIStrategy(period=14, overbought=70, oversold=30)
        signal = strategy.evaluate(_oversold_closes())
        assert signal == Signal.BUY

    def test_sell_signal_when_overbought(self) -> None:
        strategy = RSIStrategy(period=14, overbought=70, oversold=30)
        signal = strategy.evaluate(_overbought_closes())
        assert signal == Signal.SELL

    def test_hold_signal_when_neutral(self) -> None:
        strategy = RSIStrategy(period=14, overbought=70, oversold=30)
        signal = strategy.evaluate(_neutral_closes())
        assert signal == Signal.HOLD

    def test_hold_with_insufficient_data(self) -> None:
        strategy = RSIStrategy(period=14)
        closes = pd.Series([100.0, 101.0], dtype=float)
        signal = strategy.evaluate(closes)
        assert signal == Signal.HOLD

    def test_custom_thresholds(self) -> None:
        # With very wide thresholds (0, 100), everything is HOLD
        strategy = RSIStrategy(period=14, overbought=100, oversold=0)
        assert strategy.evaluate(_overbought_closes()) == Signal.HOLD
        assert strategy.evaluate(_oversold_closes()) == Signal.HOLD

    def test_signal_enum_values(self) -> None:
        assert Signal.BUY.value == "BUY"
        assert Signal.SELL.value == "SELL"
        assert Signal.HOLD.value == "HOLD"
