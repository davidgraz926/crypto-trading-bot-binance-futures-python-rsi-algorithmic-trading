"""
Trading strategy implementations.

Contains:
- TrendFollowStrategy: Multi-indicator trend following (RSI + MACD + EMA)
- GridStrategy: Grid trading for range-bound markets
- HybridStrategy: Combines both, switching based on market regime
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import pandas as pd

from config import settings
from src.indicators import add_all_indicators

logger = logging.getLogger("trading_bot.strategy")


class Signal(Enum):
    """Trading signal types."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class MarketRegime(Enum):
    """Detected market condition."""
    STRONG_UPTREND = "strong_uptrend"
    UPTREND = "uptrend"
    RANGING = "ranging"
    DOWNTREND = "downtrend"
    STRONG_DOWNTREND = "strong_downtrend"


@dataclass
class TradeSignal:
    """A trade recommendation from a strategy."""
    signal: Signal
    regime: MarketRegime
    confidence: float  # 0.0 to 1.0
    entry_price: float
    stop_loss: float
    take_profit: float
    reason: str


class BaseStrategy(ABC):
    """Abstract base class for all strategies."""

    @abstractmethod
    def analyze(self, df: pd.DataFrame) -> TradeSignal:
        """Analyze market data and produce a trade signal."""

    @abstractmethod
    def name(self) -> str:
        """Strategy name for logging."""


class TrendFollowStrategy(BaseStrategy):
    """
    Multi-indicator trend following strategy.

    Entry logic:
        BUY when: RSI < oversold AND MACD crosses above signal AND price > EMA_long
        SELL when: RSI > overbought AND MACD crosses below signal AND price < EMA_long

    Confirmation:
        - EMA crossover (short above long = bullish regime)
        - Volume above average (confirms conviction)
        - Bollinger Band position (near lower = buy zone, near upper = sell zone)

    Each confirming indicator adds to the confidence score.
    """

    def name(self) -> str:
        return "TrendFollow"

    def analyze(self, df: pd.DataFrame) -> TradeSignal:
        df = add_all_indicators(df)
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        regime = self._detect_regime(df)
        score = 0.0  # -1.0 (strong sell) to +1.0 (strong buy)
        reasons = []

        # --- RSI signal ---
        if latest["rsi"] < settings.RSI_OVERSOLD:
            score += 0.25
            reasons.append(f"RSI oversold ({latest['rsi']:.1f})")
        elif latest["rsi"] > settings.RSI_OVERBOUGHT:
            score -= 0.25
            reasons.append(f"RSI overbought ({latest['rsi']:.1f})")

        # --- MACD crossover ---
        macd_cross_up = prev["macd"] <= prev["macd_signal"] and latest["macd"] > latest["macd_signal"]
        macd_cross_down = prev["macd"] >= prev["macd_signal"] and latest["macd"] < latest["macd_signal"]

        if macd_cross_up:
            score += 0.25
            reasons.append("MACD bullish crossover")
        elif macd_cross_down:
            score -= 0.25
            reasons.append("MACD bearish crossover")
        elif latest["macd_hist"] > 0:
            score += 0.1
        else:
            score -= 0.1

        # --- EMA trend filter ---
        if latest["ema_short"] > latest["ema_long"]:
            score += 0.2
            reasons.append("EMA bullish (short > long)")
        else:
            score -= 0.2
            reasons.append("EMA bearish (short < long)")

        # --- Bollinger Band position ---
        bb_range = latest["bb_upper"] - latest["bb_lower"]
        if bb_range > 0:
            bb_position = (latest["close"] - latest["bb_lower"]) / bb_range
            if bb_position < 0.2:
                score += 0.15
                reasons.append("Price near lower Bollinger Band")
            elif bb_position > 0.8:
                score -= 0.15
                reasons.append("Price near upper Bollinger Band")

        # --- Volume confirmation ---
        if latest["volume_ratio"] > 1.5:
            # High volume amplifies the signal
            score *= 1.2
            reasons.append(f"High volume ({latest['volume_ratio']:.1f}x avg)")

        # Clamp score
        score = max(-1.0, min(1.0, score))

        # Convert score to signal
        signal = self._score_to_signal(score)
        confidence = abs(score)

        # Calculate stop-loss and take-profit using ATR
        atr = latest["atr"]
        entry = latest["close"]

        if score > 0:
            stop_loss = entry - (atr * 2.0)
            take_profit = entry + (atr * 3.0)
        elif score < 0:
            stop_loss = entry + (atr * 2.0)
            take_profit = entry - (atr * 3.0)
        else:
            stop_loss = entry
            take_profit = entry

        reason = " | ".join(reasons) if reasons else "No strong signals"

        return TradeSignal(
            signal=signal,
            regime=regime,
            confidence=confidence,
            entry_price=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=reason,
        )

    def _detect_regime(self, df: pd.DataFrame) -> MarketRegime:
        """Detect the current market regime from EMA relationship and slope."""
        latest = df.iloc[-1]
        lookback = df.tail(20)

        ema_short_slope = (lookback["ema_short"].iloc[-1] - lookback["ema_short"].iloc[0]) / lookback["ema_short"].iloc[0] * 100
        short_above_long = latest["ema_short"] > latest["ema_long"]

        # If EMAs are very close together and slope is flat, it's ranging
        ema_gap_pct = abs(latest["ema_short"] - latest["ema_long"]) / latest["ema_long"] * 100
        if ema_gap_pct < 0.5 and abs(ema_short_slope) < 1.0:
            return MarketRegime.RANGING

        if short_above_long and ema_short_slope > 2.0:
            return MarketRegime.STRONG_UPTREND
        elif short_above_long:
            return MarketRegime.UPTREND
        elif not short_above_long and ema_short_slope < -2.0:
            return MarketRegime.STRONG_DOWNTREND
        elif not short_above_long:
            return MarketRegime.DOWNTREND
        return MarketRegime.RANGING

    def _score_to_signal(self, score: float) -> Signal:
        if score >= 0.6:
            return Signal.STRONG_BUY
        elif score >= 0.25:
            return Signal.BUY
        elif score <= -0.6:
            return Signal.STRONG_SELL
        elif score <= -0.25:
            return Signal.SELL
        return Signal.NEUTRAL


@dataclass
class GridLevel:
    """A single price level in the grid."""
    price: float
    side: str  # "BUY" or "SELL"
    order_id: str = ""
    filled: bool = False


class GridStrategy(BaseStrategy):
    """
    Grid trading strategy for range-bound markets.

    Places a ladder of buy orders below current price and sell orders above.
    Profits from price oscillation within the grid range.
    """

    def __init__(self):
        self.grid_levels: list[GridLevel] = []
        self.is_active: bool = False

    def name(self) -> str:
        return "Grid"

    def analyze(self, df: pd.DataFrame) -> TradeSignal:
        """
        Grid strategy analysis - determines if conditions are right for grid trading.
        The actual grid order management happens in the bot engine.
        """
        df = add_all_indicators(df)
        latest = df.iloc[-1]
        regime = self._assess_grid_conditions(df)

        # Grid trading works best in ranging markets
        is_ranging = regime == MarketRegime.RANGING
        confidence = 0.8 if is_ranging else 0.3

        return TradeSignal(
            signal=Signal.NEUTRAL,  # Grid doesn't produce directional signals
            regime=regime,
            confidence=confidence,
            entry_price=latest["close"],
            stop_loss=latest["bb_lower"],
            take_profit=latest["bb_upper"],
            reason=f"Grid conditions: {regime.value} (confidence: {confidence:.0%})",
        )

    def calculate_grid(
        self,
        current_price: float,
        levels: int = 0,
        spacing_pct: float = 0.0,
    ) -> list[GridLevel]:
        """
        Calculate grid levels around the current price.

        Returns a list of GridLevel objects with buy orders below
        and sell orders above the current price.
        """
        levels = levels or settings.GRID_LEVELS
        spacing_pct = spacing_pct or settings.GRID_SPACING_PCT

        grid = []
        half = levels // 2

        for i in range(1, half + 1):
            # Buy levels below current price
            buy_price = current_price * (1 - (spacing_pct / 100.0) * i)
            grid.append(GridLevel(price=round(buy_price, 2), side="BUY"))

        for i in range(1, half + 1):
            # Sell levels above current price
            sell_price = current_price * (1 + (spacing_pct / 100.0) * i)
            grid.append(GridLevel(price=round(sell_price, 2), side="SELL"))

        grid.sort(key=lambda g: g.price)
        self.grid_levels = grid
        self.is_active = True

        logger.info(
            "Grid calculated: %d levels around %.2f (%.1f%% spacing)",
            len(grid), current_price, spacing_pct,
        )
        return grid

    def _assess_grid_conditions(self, df: pd.DataFrame) -> MarketRegime:
        """Assess whether market is suitable for grid trading using Bollinger Band width."""
        latest = df.iloc[-1]
        lookback = df.tail(50)

        bb_width = (latest["bb_upper"] - latest["bb_lower"]) / latest["bb_middle"] * 100

        ema_short_slope = (
            (lookback["ema_short"].iloc[-1] - lookback["ema_short"].iloc[0])
            / lookback["ema_short"].iloc[0] * 100
        )

        # Narrow bands + flat EMAs = ranging market = good for grid
        if bb_width < 4.0 and abs(ema_short_slope) < 1.5:
            return MarketRegime.RANGING
        elif ema_short_slope > 2.0:
            return MarketRegime.UPTREND
        elif ema_short_slope < -2.0:
            return MarketRegime.DOWNTREND
        return MarketRegime.RANGING


class HybridStrategy(BaseStrategy):
    """
    Hybrid strategy that switches between trend following and grid trading
    based on detected market regime.

    - Trending market -> use TrendFollowStrategy
    - Ranging market  -> use GridStrategy
    """

    def __init__(self):
        self.trend_strategy = TrendFollowStrategy()
        self.grid_strategy = GridStrategy()
        self._active_strategy: str = "trend"

    def name(self) -> str:
        return f"Hybrid({self._active_strategy})"

    @property
    def active_strategy_name(self) -> str:
        return self._active_strategy

    @property
    def grid(self) -> GridStrategy:
        return self.grid_strategy

    def analyze(self, df: pd.DataFrame) -> TradeSignal:
        """
        Analyze with both strategies, use the one appropriate for current regime.
        """
        trend_signal = self.trend_strategy.analyze(df)
        grid_signal = self.grid_strategy.analyze(df)

        regime = trend_signal.regime

        if regime in (MarketRegime.STRONG_UPTREND, MarketRegime.STRONG_DOWNTREND,
                      MarketRegime.UPTREND, MarketRegime.DOWNTREND):
            self._active_strategy = "trend"
            logger.info(
                "Hybrid: using TREND strategy (regime: %s)", regime.value
            )
            return trend_signal
        else:
            self._active_strategy = "grid"
            logger.info(
                "Hybrid: using GRID strategy (regime: %s)", regime.value
            )
            return grid_signal
