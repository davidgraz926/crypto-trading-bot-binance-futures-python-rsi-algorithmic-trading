import pytest

from src.risk_manager import RiskManager


@pytest.fixture
def rm() -> RiskManager:
    return RiskManager(
        max_position_pct=0.02,
        stop_loss_pct=0.02,
        take_profit_pct=0.04,
        leverage=1,
    )


class TestCalculatePositionSize:
    def test_basic_position_size(self, rm: RiskManager) -> None:
        # balance=10000, price=50000 -> risk_amount=200, qty=200/50000=0.004
        qty = rm.calculate_position_size(balance=10000, price=50000, precision=3)
        assert qty == 0.004

    def test_respects_leverage(self) -> None:
        rm = RiskManager(max_position_pct=0.02, leverage=10)
        qty = rm.calculate_position_size(balance=10000, price=50000, precision=3)
        # risk=200, notional=2000, qty=2000/50000=0.04
        assert qty == 0.04

    def test_precision_truncation(self, rm: RiskManager) -> None:
        qty = rm.calculate_position_size(balance=10000, price=33333, precision=4)
        # risk=200, qty=200/33333≈0.00600006 -> truncated to 0.006
        assert qty == 0.006

    def test_zero_balance_returns_zero(self, rm: RiskManager) -> None:
        qty = rm.calculate_position_size(balance=0, price=50000)
        assert qty == 0.0


class TestStopLossPrice:
    def test_long_stop_loss_below_entry(self, rm: RiskManager) -> None:
        sl = rm.stop_loss_price(entry_price=50000, side="BUY")
        assert sl == pytest.approx(49000.0)  # 50000 * (1 - 0.02)

    def test_short_stop_loss_above_entry(self, rm: RiskManager) -> None:
        sl = rm.stop_loss_price(entry_price=50000, side="SELL")
        assert sl == pytest.approx(51000.0)  # 50000 * (1 + 0.02)


class TestTakeProfitPrice:
    def test_long_take_profit_above_entry(self, rm: RiskManager) -> None:
        tp = rm.take_profit_price(entry_price=50000, side="BUY")
        assert tp == pytest.approx(52000.0)  # 50000 * (1 + 0.04)

    def test_short_take_profit_below_entry(self, rm: RiskManager) -> None:
        tp = rm.take_profit_price(entry_price=50000, side="SELL")
        assert tp == pytest.approx(48000.0)  # 50000 * (1 - 0.04)


class TestValidateTrade:
    def test_valid_trade_passes(self, rm: RiskManager) -> None:
        assert rm.validate_trade(balance=10000, quantity=0.004, price=50000) is True

    def test_oversized_trade_rejected(self, rm: RiskManager) -> None:
        assert rm.validate_trade(balance=10000, quantity=1.0, price=50000) is False

    def test_zero_quantity_rejected(self, rm: RiskManager) -> None:
        assert rm.validate_trade(balance=10000, quantity=0, price=50000) is False

    def test_negative_quantity_rejected(self, rm: RiskManager) -> None:
        assert rm.validate_trade(balance=10000, quantity=-0.01, price=50000) is False
