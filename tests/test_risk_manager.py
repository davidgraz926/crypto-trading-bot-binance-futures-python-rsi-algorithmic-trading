"""Tests for the risk management module."""

import pytest

from src.risk.manager import RiskManager


class TestRiskManager:
    def test_drawdown_below_limit(self) -> None:
        rm = RiskManager(max_drawdown_pct=10.0)
        rm.set_initial_balance(10000.0)
        assert rm.check_drawdown(9500.0) is False  # 5% drawdown

    def test_drawdown_at_limit(self) -> None:
        rm = RiskManager(max_drawdown_pct=10.0)
        rm.set_initial_balance(10000.0)
        assert rm.check_drawdown(9000.0) is True  # 10% drawdown

    def test_drawdown_above_limit(self) -> None:
        rm = RiskManager(max_drawdown_pct=10.0)
        rm.set_initial_balance(10000.0)
        assert rm.check_drawdown(8000.0) is True  # 20% drawdown

    def test_drawdown_no_initial_balance(self) -> None:
        rm = RiskManager()
        assert rm.check_drawdown(5000.0) is False

    def test_position_size_respects_max(self) -> None:
        rm = RiskManager(max_position_size=0.01)
        # With enough balance this would be > 0.01
        size = rm.compute_position_size(
            balance=100000.0, price=50000.0, leverage=1
        )
        assert size == 0.01

    def test_position_size_risk_limited(self) -> None:
        rm = RiskManager(max_position_size=10.0)
        size = rm.compute_position_size(
            balance=1000.0, price=50000.0, leverage=1
        )
        assert size == pytest.approx(0.02)

    def test_position_size_with_leverage(self) -> None:
        rm = RiskManager(max_position_size=10.0)
        size = rm.compute_position_size(
            balance=1000.0, price=50000.0, leverage=5
        )
        assert size == pytest.approx(0.1)

    def test_position_size_zero_price(self) -> None:
        rm = RiskManager()
        assert rm.compute_position_size(1000.0, 0.0) == 0.0

    def test_stop_loss_long(self) -> None:
        rm = RiskManager(stop_loss_pct=2.0)
        sl = rm.stop_loss_price(50000.0, "BUY")
        assert sl == pytest.approx(49000.0)

    def test_stop_loss_short(self) -> None:
        rm = RiskManager(stop_loss_pct=2.0)
        sl = rm.stop_loss_price(50000.0, "SELL")
        assert sl == pytest.approx(51000.0)

    def test_take_profit_long(self) -> None:
        rm = RiskManager(take_profit_pct=4.0)
        tp = rm.take_profit_price(50000.0, "BUY")
        assert tp == pytest.approx(52000.0)

    def test_take_profit_short(self) -> None:
        rm = RiskManager(take_profit_pct=4.0)
        tp = rm.take_profit_price(50000.0, "SELL")
        assert tp == pytest.approx(48000.0)
