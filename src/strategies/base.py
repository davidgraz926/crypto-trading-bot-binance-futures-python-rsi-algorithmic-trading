"""Base class for trading strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import pandas as pd


class SignalType(Enum):
    """Possible trading signal types."""

    LONG = "LONG"
    SHORT = "SHORT"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"
    HOLD = "HOLD"


@dataclass
class Signal:
    """Trading signal produced by a strategy."""

    signal_type: SignalType
    reason: str = ""


class BaseStrategy(ABC):
    """Abstract base class for trading strategies.

    Subclasses must implement ``generate_signal`` to evaluate market data
    and return a ``Signal``.
    """

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """Analyse *data* and produce a trading signal.

        Args:
            data: DataFrame of OHLCV candle data with at least a ``close``
                  column.

        Returns:
            A ``Signal`` indicating the recommended action.
        """
