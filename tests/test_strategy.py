"""Tests for trading strategies."""

import numpy as np
import pandas as pd
import pytest

from src.strategy import (
    GridStrategy,
    HybridStrategy,
    MarketRegime,
    Signal,
    TrendFollowStrategy,
)


@pytest.fixture
def uptrend_data():
    """Generate data with a clear uptrend."""
    np.random.seed(42)
    n = 300
    trend = np.linspace(40000, 55000, n)
    noise = np.random.randn(n) * 50
    close = trend + noise
    return pd.DataFrame({
        "open": close - np.random.randn(n) * 20,
        "high": close + np.abs(np.random.randn(n) * 40),
        "low": close - np.abs(np.random.randn(n) * 40),
        "close": close,
        "volume": np.abs(np.random.randn(n) * 1000) + 500,
    })


@pytest.fixture
def downtrend_data():
    """Generate data with a clear downtrend."""
    np.random.seed(42)
    n = 300
    trend = np.linspace(55000, 40000, n)
    noise = np.random.randn(n) * 50
    close = trend + noise
    return pd.DataFrame({
        "open": close - np.random.randn(n) * 20,
        "high": close + np.abs(np.random.randn(n) * 40),
        "low": close - np.abs(np.random.randn(n) * 40),
        "close": close,
        "volume": np.abs(np.random.randn(n) * 1000) + 500,
    })


@pytest.fixture
def ranging_data():
    """Generate data that oscillates in a very tight range."""
    np.random.seed(42)
    n = 300
    # Very tight oscillation around 50000 so EMAs stay nearly flat
    close = 50000 + np.sin(np.linspace(0, 20 * np.pi, n)) * 50 + np.random.randn(n) * 5
    return pd.DataFrame({
        "open": close - np.random.randn(n) * 3,
        "high": close + np.abs(np.random.randn(n) * 8),
        "low": close - np.abs(np.random.randn(n) * 8),
        "close": close,
        "volume": np.abs(np.random.randn(n) * 500) + 300,
    })


class TestTrendFollowStrategy:
    def test_produces_signal(self, uptrend_data):
        strategy = TrendFollowStrategy()
        signal = strategy.analyze(uptrend_data)
        assert signal is not None
        assert signal.signal in Signal
        assert signal.regime in MarketRegime
        assert 0.0 <= signal.confidence <= 1.0

    def test_uptrend_bullish_signal(self, uptrend_data):
        """In a strong uptrend, should produce bullish signals."""
        strategy = TrendFollowStrategy()
        signal = strategy.analyze(uptrend_data)
        assert signal.regime in (MarketRegime.UPTREND, MarketRegime.STRONG_UPTREND)

    def test_downtrend_bearish_signal(self, downtrend_data):
        """In a strong downtrend, should produce bearish signals."""
        strategy = TrendFollowStrategy()
        signal = strategy.analyze(downtrend_data)
        assert signal.regime in (MarketRegime.DOWNTREND, MarketRegime.STRONG_DOWNTREND)

    def test_stop_loss_set(self, uptrend_data):
        strategy = TrendFollowStrategy()
        signal = strategy.analyze(uptrend_data)
        assert signal.stop_loss > 0
        assert signal.take_profit > 0

    def test_reason_not_empty(self, uptrend_data):
        strategy = TrendFollowStrategy()
        signal = strategy.analyze(uptrend_data)
        assert len(signal.reason) > 0

    def test_name(self):
        assert TrendFollowStrategy().name() == "TrendFollow"


class TestGridStrategy:
    def test_calculate_grid_levels(self):
        strategy = GridStrategy()
        grid = strategy.calculate_grid(
            current_price=50000.0,
            levels=10,
            spacing_pct=0.5,
        )
        assert len(grid) == 10
        assert strategy.is_active

    def test_grid_buy_below_sell_above(self):
        """Buy orders should be below price, sell orders above."""
        strategy = GridStrategy()
        grid = strategy.calculate_grid(
            current_price=50000.0,
            levels=10,
            spacing_pct=0.5,
        )
        buys = [g for g in grid if g.side == "BUY"]
        sells = [g for g in grid if g.side == "SELL"]

        assert len(buys) == 5
        assert len(sells) == 5
        assert all(g.price < 50000.0 for g in buys)
        assert all(g.price > 50000.0 for g in sells)

    def test_grid_sorted_by_price(self):
        strategy = GridStrategy()
        grid = strategy.calculate_grid(current_price=50000.0, levels=10, spacing_pct=1.0)
        prices = [g.price for g in grid]
        assert prices == sorted(prices)

    def test_grid_analyze_produces_signal(self, ranging_data):
        strategy = GridStrategy()
        signal = strategy.analyze(ranging_data)
        assert signal is not None
        assert signal.signal == Signal.NEUTRAL  # Grid doesn't produce directional signals

    def test_name(self):
        assert GridStrategy().name() == "Grid"


class TestHybridStrategy:
    def test_uses_trend_in_uptrend(self, uptrend_data):
        strategy = HybridStrategy()
        signal = strategy.analyze(uptrend_data)
        assert strategy.active_strategy_name == "trend"

    def test_uses_trend_in_downtrend(self, downtrend_data):
        strategy = HybridStrategy()
        signal = strategy.analyze(downtrend_data)
        assert strategy.active_strategy_name == "trend"

    def test_uses_grid_in_ranging(self, ranging_data):
        strategy = HybridStrategy()
        signal = strategy.analyze(ranging_data)
        assert strategy.active_strategy_name == "grid"

    def test_name_reflects_active(self, uptrend_data):
        strategy = HybridStrategy()
        strategy.analyze(uptrend_data)
        assert "trend" in strategy.name() or "grid" in strategy.name()
