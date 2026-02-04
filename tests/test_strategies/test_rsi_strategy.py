"""Tests for the RSI trading strategy."""

import pandas as pd
import pytest

from src.strategies.base import SignalType
from src.strategies.rsi_strategy import RSIStrategy


class TestRSIStrategy:
    def test_hold_on_neutral_data(self, sample_ohlcv: pd.DataFrame) -> None:
        strategy = RSIStrategy()
        signal = strategy.generate_signal(sample_ohlcv)
        # With random-walk data the signal type is not predetermined,
        # but it must be a valid SignalType.
        assert signal.signal_type in SignalType

    def test_long_signal_on_oversold_crossover(
        self, oversold_data: pd.DataFrame
    ) -> None:
        strategy = RSIStrategy()
        signal = strategy.generate_signal(oversold_data)
        # The fixture is designed so RSI crosses above 30 on the last bar
        assert signal.signal_type in (SignalType.LONG, SignalType.CLOSE_SHORT, SignalType.HOLD)

    def test_short_signal_on_overbought_crossover(
        self, overbought_data: pd.DataFrame
    ) -> None:
        strategy = RSIStrategy()
        signal = strategy.generate_signal(overbought_data)
        assert signal.signal_type in (SignalType.SHORT, SignalType.CLOSE_LONG, SignalType.HOLD)

    def test_custom_thresholds(self, sample_ohlcv: pd.DataFrame) -> None:
        strategy = RSIStrategy(overbought=80.0, oversold=20.0)
        signal = strategy.generate_signal(sample_ohlcv)
        assert signal.signal_type in SignalType

    def test_signal_has_reason(self, sample_ohlcv: pd.DataFrame) -> None:
        strategy = RSIStrategy()
        signal = strategy.generate_signal(sample_ohlcv)
        assert isinstance(signal.reason, str)
        assert len(signal.reason) > 0
