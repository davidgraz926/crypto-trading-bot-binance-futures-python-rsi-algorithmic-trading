import numpy as np
import pandas as pd
import pytest

from src.backtester import Backtester, BacktestResult, Trade
from src.strategy import RSIStrategy


def _make_ohlcv(closes: list[float], spread: float = 0.5) -> pd.DataFrame:
    """Build a minimal OHLCV DataFrame from a list of close prices."""
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c + spread for c in closes],
            "low": [c - spread for c in closes],
            "close": closes,
            "volume": [100.0] * len(closes),
        }
    )


def _trending_up(n: int = 100, start: float = 100.0) -> pd.DataFrame:
    """Strongly rising prices — should trigger BUY early, then profit."""
    closes = [start + i * 1.5 for i in range(n)]
    return _make_ohlcv(closes)


def _trending_down(n: int = 100, start: float = 300.0) -> pd.DataFrame:
    """Strongly falling prices — should trigger SELL early."""
    closes = [start - i * 1.5 for i in range(n)]
    return _make_ohlcv(closes)


def _sideways(n: int = 100, base: float = 100.0) -> pd.DataFrame:
    """Oscillating prices that stay in a tight range (RSI stays neutral)."""
    np.random.seed(99)
    noise = np.random.randn(n) * 0.3
    closes = [base + noise[i] for i in range(n)]
    return _make_ohlcv(closes, spread=0.2)


def _volatile(n: int = 200, base: float = 100.0) -> pd.DataFrame:
    """Prices with big swings that cross RSI thresholds repeatedly."""
    np.random.seed(7)
    prices = np.cumsum(np.random.randn(n) * 3) + base
    closes = prices.tolist()
    highs = [c + abs(np.random.randn() * 2) for c in closes]
    lows = [c - abs(np.random.randn() * 2) for c in closes]
    return pd.DataFrame(
        {
            "open": closes,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": [100.0] * n,
        }
    )


@pytest.fixture
def default_bt() -> Backtester:
    return Backtester(
        strategy=RSIStrategy(period=14, overbought=70, oversold=30),
        initial_balance=10_000.0,
        max_position_pct=0.02,
        stop_loss_pct=0.02,
        take_profit_pct=0.04,
        leverage=1,
        commission_pct=0.0004,
    )


class TestBacktestResult:
    def test_result_fields_populated(self, default_bt: Backtester) -> None:
        result = default_bt.run(_volatile())
        assert isinstance(result, BacktestResult)
        assert result.initial_balance == 10_000.0
        assert isinstance(result.final_balance, float)
        assert isinstance(result.total_return_pct, float)
        assert isinstance(result.win_rate, float)
        assert isinstance(result.total_trades, int)
        assert isinstance(result.max_drawdown_pct, float)
        assert isinstance(result.sharpe_ratio, float)

    def test_equity_curve_length_matches_data(self, default_bt: Backtester) -> None:
        df = _volatile()
        result = default_bt.run(df)
        assert len(result.equity_curve) == len(df)

    def test_few_trades_on_sideways_market(self, default_bt: Backtester) -> None:
        result = default_bt.run(_sideways())
        # RSI stays near 50 in a mostly flat market -> very few trades
        assert result.total_trades <= 2
        # Impact on balance is negligible
        assert abs(result.total_return_pct) < 1.0


class TestTradeExecution:
    def test_trending_up_triggers_trades(self, default_bt: Backtester) -> None:
        result = default_bt.run(_trending_up())
        assert result.total_trades >= 1

    def test_trending_down_triggers_trades(self, default_bt: Backtester) -> None:
        result = default_bt.run(_trending_down())
        assert result.total_trades >= 1

    def test_trade_records_have_valid_fields(self, default_bt: Backtester) -> None:
        result = default_bt.run(_volatile())
        for trade in result.trades:
            assert isinstance(trade, Trade)
            assert trade.side in ("BUY", "SELL")
            assert trade.entry_price > 0
            assert trade.exit_price > 0
            assert trade.quantity > 0
            assert trade.exit_reason in (
                "signal", "stop_loss", "take_profit", "end_of_data"
            )

    def test_stop_loss_exit(self) -> None:
        """Ensure a position that immediately drops hits stop-loss."""
        # Build data: rises to trigger BUY, then crashes
        rises = [100 + i * 2 for i in range(20)]  # RSI will go very high then...
        falls = [rises[-1] - i * 0.5 for i in range(20)]  # ... we need oversold first

        # Actually: we need RSI < 30 to trigger BUY, then price drops to SL.
        # Start with falling prices (oversold), then a small bounce, then crash.
        falling = [200 - i * 2 for i in range(20)]
        crash = [falling[-1] - i * 5 for i in range(30)]
        closes = falling + crash
        df = _make_ohlcv(closes, spread=0.3)

        bt = Backtester(
            strategy=RSIStrategy(period=14, overbought=70, oversold=30),
            initial_balance=10_000.0,
            stop_loss_pct=0.02,
            take_profit_pct=0.50,  # very wide TP so SL hits first
        )
        result = bt.run(df)
        sl_trades = [t for t in result.trades if t.exit_reason == "stop_loss"]
        assert len(sl_trades) >= 1

    def test_take_profit_exit(self) -> None:
        """Ensure a position that keeps rising hits take-profit."""
        # Falling prices to get oversold, then a strong rally
        falling = [200 - i * 2 for i in range(20)]
        rally = [falling[-1] + i * 3 for i in range(40)]
        closes = falling + rally
        highs = [c + 2 for c in closes]
        lows = [c - 0.1 for c in closes]
        df = pd.DataFrame(
            {
                "open": closes,
                "high": highs,
                "low": lows,
                "close": closes,
                "volume": [100.0] * len(closes),
            }
        )

        bt = Backtester(
            strategy=RSIStrategy(period=14, overbought=70, oversold=30),
            initial_balance=10_000.0,
            stop_loss_pct=0.50,  # very wide SL so TP hits first
            take_profit_pct=0.04,
        )
        result = bt.run(df)
        tp_trades = [t for t in result.trades if t.exit_reason == "take_profit"]
        assert len(tp_trades) >= 1


class TestRiskAndMetrics:
    def test_win_rate_between_0_and_1(self, default_bt: Backtester) -> None:
        result = default_bt.run(_volatile())
        assert 0.0 <= result.win_rate <= 1.0

    def test_max_drawdown_non_negative(self, default_bt: Backtester) -> None:
        result = default_bt.run(_volatile())
        assert result.max_drawdown_pct >= 0.0

    def test_leverage_increases_position_size(self) -> None:
        df = _volatile()
        bt_1x = Backtester(
            strategy=RSIStrategy(period=14, overbought=70, oversold=30),
            initial_balance=10_000.0,
            leverage=1,
        )
        bt_3x = Backtester(
            strategy=RSIStrategy(period=14, overbought=70, oversold=30),
            initial_balance=10_000.0,
            leverage=3,
        )
        r1 = bt_1x.run(df)
        r3 = bt_3x.run(df)

        if r1.total_trades > 0 and r3.total_trades > 0:
            # 3x leverage should produce larger position quantities
            avg_qty_1x = sum(t.quantity for t in r1.trades) / len(r1.trades)
            avg_qty_3x = sum(t.quantity for t in r3.trades) / len(r3.trades)
            assert avg_qty_3x > avg_qty_1x

    def test_commission_reduces_balance(self) -> None:
        df = _volatile()
        bt_no_fee = Backtester(
            strategy=RSIStrategy(period=14, overbought=70, oversold=30),
            initial_balance=10_000.0,
            commission_pct=0.0,
        )
        bt_with_fee = Backtester(
            strategy=RSIStrategy(period=14, overbought=70, oversold=30),
            initial_balance=10_000.0,
            commission_pct=0.001,
        )
        r_no = bt_no_fee.run(df)
        r_yes = bt_with_fee.run(df)

        if r_no.total_trades > 0:
            assert r_yes.final_balance < r_no.final_balance


class TestEdgeCases:
    def test_empty_dataframe(self, default_bt: Backtester) -> None:
        df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        result = default_bt.run(df)
        assert result.total_trades == 0
        assert result.final_balance == result.initial_balance

    def test_very_short_data(self, default_bt: Backtester) -> None:
        df = _make_ohlcv([100.0, 101.0, 99.0])
        result = default_bt.run(df)
        assert result.total_trades == 0

    def test_constant_prices_no_trades(self, default_bt: Backtester) -> None:
        closes = [100.0] * 50
        df = _make_ohlcv(closes)
        result = default_bt.run(df)
        assert result.total_trades == 0
