from src.risk_manager import (
    calculate_position_size,
    can_open_position,
    compute_stop_loss,
    compute_take_profit,
)


class TestCalculatePositionSize:
    def test_basic_calculation(self) -> None:
        # balance=10000, entry=50000, SL=2%
        size = calculate_position_size(10000.0, 50000.0, stop_loss_pct=2.0)
        # risk = 10000 * 0.01 = 100, SL distance = 50000 * 0.02 = 1000
        # size = 100 / 1000 = 0.1
        assert abs(size - 0.1) < 1e-9

    def test_zero_balance_returns_zero(self) -> None:
        assert calculate_position_size(0.0, 50000.0) == 0.0

    def test_zero_price_returns_zero(self) -> None:
        assert calculate_position_size(10000.0, 0.0) == 0.0

    def test_zero_stop_loss_returns_zero(self) -> None:
        assert calculate_position_size(10000.0, 50000.0, stop_loss_pct=0.0) == 0.0


class TestComputeStopLoss:
    def test_buy_side(self) -> None:
        sl = compute_stop_loss(50000.0, "BUY")
        assert sl == 50000.0 * 0.98

    def test_sell_side(self) -> None:
        sl = compute_stop_loss(50000.0, "SELL")
        assert sl == 50000.0 * 1.02


class TestComputeTakeProfit:
    def test_buy_side(self) -> None:
        tp = compute_take_profit(50000.0, "BUY")
        assert tp == 50000.0 * 1.04

    def test_sell_side(self) -> None:
        tp = compute_take_profit(50000.0, "SELL")
        assert tp == 50000.0 * 0.96


class TestCanOpenPosition:
    def test_allowed_when_below_max(self) -> None:
        assert can_open_position(0) is True

    def test_blocked_when_at_max(self) -> None:
        assert can_open_position(1) is False
