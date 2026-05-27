"""Tests for the risk management layer."""

import pytest

from src.risk_manager import RiskManager
from src.strategy import MarketRegime, Signal, TradeSignal


@pytest.fixture
def risk_manager():
    rm = RiskManager(
        max_position_pct=10.0,
        stop_loss_pct=2.0,
        take_profit_pct=4.0,
        max_drawdown_pct=15.0,
        max_positions=3,
    )
    rm.set_initial_balance(10000.0)
    return rm


def make_signal(
    signal=Signal.BUY,
    confidence=0.7,
    entry=50000.0,
    sl=49000.0,
    tp=52000.0,
) -> TradeSignal:
    return TradeSignal(
        signal=signal,
        regime=MarketRegime.UPTREND,
        confidence=confidence,
        entry_price=entry,
        stop_loss=sl,
        take_profit=tp,
        reason="test signal",
    )


class TestRiskManagerEvaluation:
    def test_approves_valid_buy(self, risk_manager):
        proposal = risk_manager.evaluate_signal(
            signal=make_signal(),
            current_balance=10000.0,
            open_positions=[],
        )
        assert proposal is not None
        assert proposal.side == "BUY"
        assert proposal.quantity > 0

    def test_approves_valid_sell(self, risk_manager):
        proposal = risk_manager.evaluate_signal(
            signal=make_signal(signal=Signal.SELL, sl=51000.0, tp=48000.0),
            current_balance=10000.0,
            open_positions=[],
        )
        assert proposal is not None
        assert proposal.side == "SELL"

    def test_rejects_neutral_signal(self, risk_manager):
        proposal = risk_manager.evaluate_signal(
            signal=make_signal(signal=Signal.NEUTRAL),
            current_balance=10000.0,
            open_positions=[],
        )
        assert proposal is None

    def test_rejects_low_confidence(self, risk_manager):
        proposal = risk_manager.evaluate_signal(
            signal=make_signal(confidence=0.1),
            current_balance=10000.0,
            open_positions=[],
        )
        assert proposal is None

    def test_rejects_max_positions_reached(self, risk_manager):
        positions = [
            {"symbol": "ETHUSDT", "side": "LONG", "size": 1.0},
            {"symbol": "SOLUSDT", "side": "SHORT", "size": 10.0},
            {"symbol": "ADAUSDT", "side": "LONG", "size": 100.0},
        ]
        proposal = risk_manager.evaluate_signal(
            signal=make_signal(),
            current_balance=10000.0,
            open_positions=positions,
        )
        assert proposal is None

    def test_allows_reduce_existing_at_max_positions(self, risk_manager):
        """Should allow closing an existing position even at max positions."""
        positions = [
            {"symbol": "BTCUSDT", "side": "SHORT", "size": 0.1},
            {"symbol": "ETHUSDT", "side": "LONG", "size": 1.0},
            {"symbol": "SOLUSDT", "side": "LONG", "size": 10.0},
        ]
        # BUY signal against existing SHORT = reduce
        proposal = risk_manager.evaluate_signal(
            signal=make_signal(signal=Signal.BUY),
            current_balance=10000.0,
            open_positions=positions,
        )
        assert proposal is not None
        assert proposal.reduce_only is True


class TestDrawdownProtection:
    def test_blocks_trade_on_max_drawdown(self, risk_manager):
        # Peak was 10000, now balance dropped 20% (exceeds 15% limit)
        proposal = risk_manager.evaluate_signal(
            signal=make_signal(),
            current_balance=8000.0,
            open_positions=[],
        )
        assert proposal is None

    def test_allows_trade_within_drawdown(self, risk_manager):
        # 5% drawdown is within 15% limit
        proposal = risk_manager.evaluate_signal(
            signal=make_signal(),
            current_balance=9500.0,
            open_positions=[],
        )
        assert proposal is not None

    def test_peak_balance_updates(self, risk_manager):
        risk_manager.update_balance(12000.0)
        assert risk_manager.peak_balance == 12000.0

    def test_peak_balance_does_not_decrease(self, risk_manager):
        risk_manager.update_balance(12000.0)
        risk_manager.update_balance(11000.0)
        assert risk_manager.peak_balance == 12000.0


class TestPositionSizing:
    def test_basic_position_size(self, risk_manager):
        qty = risk_manager.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss=49000.0,
        )
        # Risk 10% of 10000 = 1000; price risk = 1000; uncapped qty = 1.0
        # But max position value = 10000 * 10% * 5x = 5000; max qty = 5000/50000 = 0.1
        # Capped at 0.1
        assert qty == pytest.approx(0.1, rel=0.01)

    def test_zero_balance_returns_zero(self, risk_manager):
        qty = risk_manager.calculate_position_size(
            balance=0.0,
            entry_price=50000.0,
            stop_loss=49000.0,
        )
        assert qty == 0.0

    def test_zero_price_risk_returns_zero(self, risk_manager):
        qty = risk_manager.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss=50000.0,
        )
        assert qty == 0.0

    def test_grid_position_size(self, risk_manager):
        qty = risk_manager.calculate_grid_position_size(
            balance=10000.0,
            grid_levels=10,
            entry_price=50000.0,
        )
        assert qty > 0
        # Total value = 10000 * 10% * 5x leverage = 5000
        # Per level = 5000 / 10 = 500
        # Qty = 500 / 50000 = 0.01
        assert qty == pytest.approx(0.01, rel=0.01)

    def test_grid_zero_levels_returns_zero(self, risk_manager):
        qty = risk_manager.calculate_grid_position_size(
            balance=10000.0,
            grid_levels=0,
            entry_price=50000.0,
        )
        assert qty == 0.0


class TestStopLossValidation:
    def test_rejects_too_tight_stop_loss(self, risk_manager):
        """Stop-loss within 0.1% of entry should be rejected."""
        proposal = risk_manager.evaluate_signal(
            signal=make_signal(entry=50000.0, sl=49990.0),  # 0.02% distance
            current_balance=10000.0,
            open_positions=[],
        )
        assert proposal is None
