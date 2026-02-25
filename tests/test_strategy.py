import pandas as pd

from src.strategy import Signal, evaluate


def _candles_from_closes(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"close": closes})


class TestEvaluate:
    def test_buy_signal_when_oversold(self) -> None:
        # Rapidly dropping prices produce RSI < 30
        closes = [float(100 - i) for i in range(30)]
        signal, rsi = evaluate(_candles_from_closes(closes))
        assert signal == Signal.BUY
        assert rsi is not None and rsi < 30

    def test_sell_signal_when_overbought(self) -> None:
        # Steadily rising prices produce RSI > 70
        closes = [float(i) for i in range(1, 30)]
        signal, rsi = evaluate(_candles_from_closes(closes))
        assert signal == Signal.SELL
        assert rsi is not None and rsi > 70

    def test_hold_when_missing_close_column(self) -> None:
        df = pd.DataFrame({"price": [1.0, 2.0, 3.0]})
        signal, rsi = evaluate(df)
        assert signal == Signal.HOLD
        assert rsi is None

    def test_hold_when_insufficient_data(self) -> None:
        closes = [50.0] * 5
        signal, rsi = evaluate(_candles_from_closes(closes))
        assert signal == Signal.HOLD
        assert rsi is None
