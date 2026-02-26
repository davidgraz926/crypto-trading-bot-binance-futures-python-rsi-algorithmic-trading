"""Tests for the combined RSI + MEV strategy evaluation."""

import pandas as pd

from src.strategy import Signal, evaluate, evaluate_with_mev


def _make_declining_candles(n: int = 30) -> pd.DataFrame:
    """Create candles with steadily declining prices (oversold RSI)."""
    closes = [float(100 - i) for i in range(n)]
    return pd.DataFrame({"close": closes})


def _make_rising_candles(n: int = 30) -> pd.DataFrame:
    """Create candles with steadily rising prices (overbought RSI)."""
    closes = [float(50 + i) for i in range(n)]
    return pd.DataFrame({"close": closes})


class TestEvaluateWithMev:
    def test_mev_none_falls_back_to_rsi_only(self) -> None:
        candles = _make_declining_candles()
        signal, rsi, combined = evaluate_with_mev(candles, mev_pressure=None)
        # Should behave like RSI-only
        signal_rsi, _ = evaluate(candles)
        assert signal == signal_rsi

    def test_mev_confirms_rsi_buy(self) -> None:
        candles = _make_declining_candles()
        signal, rsi, combined = evaluate_with_mev(candles, mev_pressure=60.0)
        assert signal == Signal.BUY
        assert combined is not None and combined > 40

    def test_mev_confirms_rsi_sell(self) -> None:
        candles = _make_rising_candles()
        signal, rsi, combined = evaluate_with_mev(candles, mev_pressure=-60.0)
        assert signal == Signal.SELL
        assert combined is not None and combined < -40

    def test_mev_weight_zero_ignores_mev(self) -> None:
        candles = _make_declining_candles()
        signal_mev, _, _ = evaluate_with_mev(
            candles, mev_pressure=-100.0, mev_weight=0.0
        )
        signal_rsi, _ = evaluate(candles)
        assert signal_mev == signal_rsi

    def test_mev_weight_one_ignores_rsi(self) -> None:
        candles = _make_declining_candles()
        # RSI is oversold (would be BUY), but MEV says strong sell with weight=1.0
        signal, _, combined = evaluate_with_mev(
            candles, mev_pressure=-80.0, mev_weight=1.0
        )
        assert signal == Signal.SELL
        assert combined is not None and combined < -40

    def test_combined_score_clamped(self) -> None:
        candles = _make_declining_candles()
        _, _, combined = evaluate_with_mev(candles, mev_pressure=100.0)
        assert combined is not None
        assert -100 <= combined <= 100

    def test_missing_close_column_returns_hold(self) -> None:
        candles = pd.DataFrame({"open": [1.0, 2.0, 3.0]})
        signal, rsi, combined = evaluate_with_mev(candles, mev_pressure=50.0)
        assert signal == Signal.HOLD
        assert rsi is None
        assert combined is None

    def test_insufficient_data_returns_hold(self) -> None:
        candles = pd.DataFrame({"close": [100.0, 99.0]})
        signal, rsi, combined = evaluate_with_mev(candles, mev_pressure=50.0)
        assert signal == Signal.HOLD
        assert rsi is None
