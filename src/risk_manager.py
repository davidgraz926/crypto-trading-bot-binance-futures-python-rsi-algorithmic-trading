"""
Risk management layer.
Sits between strategy signals and order execution.
Every trade proposal must pass through here before reaching the exchange.
"""

import logging
from dataclasses import dataclass

from config import settings
from src.strategy import Signal, TradeSignal

logger = logging.getLogger("trading_bot.risk")


@dataclass
class OrderProposal:
    """An order that has been approved by risk management."""
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: float
    entry_price: float
    stop_loss: float
    take_profit: float
    reduce_only: bool = False
    reason: str = ""


class RiskManager:
    """
    Gatekeeper that validates every trade against risk rules.

    Checks:
    - Position size limits
    - Maximum drawdown
    - Maximum number of open positions
    - Stop-loss and take-profit are set
    - Minimum confidence threshold
    """

    def __init__(
        self,
        max_position_pct: float = 0.0,
        stop_loss_pct: float = 0.0,
        take_profit_pct: float = 0.0,
        max_drawdown_pct: float = 0.0,
        max_positions: int = 0,
    ):
        self.max_position_pct = max_position_pct or settings.MAX_POSITION_SIZE_PCT
        self.stop_loss_pct = stop_loss_pct or settings.STOP_LOSS_PCT
        self.take_profit_pct = take_profit_pct or settings.TAKE_PROFIT_PCT
        self.max_drawdown_pct = max_drawdown_pct or settings.MAX_DRAWDOWN_PCT
        self.max_positions = max_positions or settings.MAX_OPEN_POSITIONS

        self.starting_balance: float = 0.0
        self.peak_balance: float = 0.0
        self.min_confidence: float = 0.3

    def set_initial_balance(self, balance: float) -> None:
        """Set the starting and peak balance for drawdown tracking."""
        self.starting_balance = balance
        self.peak_balance = balance
        logger.info("Risk manager initialized with balance: %.2f USDT", balance)

    def update_balance(self, current_balance: float) -> None:
        """Update peak balance tracking."""
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance

    def check_drawdown(self, current_balance: float) -> bool:
        """
        Check if we've exceeded maximum drawdown.
        Returns True if drawdown is within limits, False if exceeded.
        """
        if self.peak_balance == 0:
            return True

        drawdown = ((self.peak_balance - current_balance) / self.peak_balance) * 100.0

        if drawdown >= self.max_drawdown_pct:
            logger.warning(
                "MAX DRAWDOWN EXCEEDED: %.2f%% (limit: %.2f%%). Trading halted.",
                drawdown, self.max_drawdown_pct,
            )
            return False

        if drawdown > self.max_drawdown_pct * 0.8:
            logger.warning(
                "Drawdown warning: %.2f%% (limit: %.2f%%)",
                drawdown, self.max_drawdown_pct,
            )
        return True

    def evaluate_signal(
        self,
        signal: TradeSignal,
        current_balance: float,
        open_positions: list[dict],
        symbol: str = "",
    ) -> OrderProposal | None:
        """
        Evaluate a trade signal and return an OrderProposal if approved.
        Returns None if the trade is rejected.
        """
        symbol = symbol or settings.TRADING_SYMBOL

        # --- Check: is the signal actionable? ---
        if signal.signal == Signal.NEUTRAL:
            logger.debug("Signal is NEUTRAL, no action")
            return None

        # --- Check: minimum confidence ---
        if signal.confidence < self.min_confidence:
            logger.info(
                "Signal rejected: confidence %.2f below minimum %.2f",
                signal.confidence, self.min_confidence,
            )
            return None

        # --- Check: drawdown limit ---
        self.update_balance(current_balance)
        if not self.check_drawdown(current_balance):
            logger.warning("Signal rejected: max drawdown exceeded")
            return None

        # --- Check: max open positions ---
        if len(open_positions) >= self.max_positions:
            # Allow if this is reducing an existing position
            existing = self._find_position(open_positions, symbol)
            if not existing:
                logger.info(
                    "Signal rejected: max positions reached (%d/%d)",
                    len(open_positions), self.max_positions,
                )
                return None

        # --- Determine order side ---
        is_buy = signal.signal in (Signal.BUY, Signal.STRONG_BUY)
        side = "BUY" if is_buy else "SELL"

        # --- Check for conflicting position ---
        existing = self._find_position(open_positions, symbol)
        reduce_only = False

        if existing:
            existing_is_long = existing["side"] == "LONG"
            if (is_buy and not existing_is_long) or (not is_buy and existing_is_long):
                # Signal is opposite to current position - close it first
                reduce_only = True
                logger.info("Signal will reduce existing %s position", existing["side"])

        # --- Calculate position size ---
        quantity = self.calculate_position_size(
            balance=current_balance,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
        )

        if quantity <= 0:
            logger.info("Signal rejected: calculated quantity is 0")
            return None

        # --- Validate stop-loss distance ---
        sl_distance_pct = abs(signal.entry_price - signal.stop_loss) / signal.entry_price * 100
        if sl_distance_pct < 0.1:
            logger.info("Signal rejected: stop-loss too tight (%.2f%%)", sl_distance_pct)
            return None

        proposal = OrderProposal(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            reduce_only=reduce_only,
            reason=signal.reason,
        )

        logger.info(
            "APPROVED: %s %s %.6f @ %.2f | SL: %.2f | TP: %.2f | %s",
            side, symbol, quantity, signal.entry_price,
            signal.stop_loss, signal.take_profit, signal.reason,
        )
        return proposal

    def calculate_position_size(
        self,
        balance: float,
        entry_price: float,
        stop_loss: float,
    ) -> float:
        """
        Calculate position size based on risk per trade.

        Uses the fixed-percentage method:
        - Risk at most max_position_pct of balance per trade
        - Size = (balance * risk_pct) / (entry - stop_loss)
        """
        if entry_price <= 0 or balance <= 0:
            return 0.0

        risk_amount = balance * (self.max_position_pct / 100.0)
        price_risk = abs(entry_price - stop_loss)

        if price_risk == 0:
            return 0.0

        quantity = risk_amount / price_risk

        # Cap at max position value
        max_value = balance * (self.max_position_pct / 100.0) * settings.TRADING_LEVERAGE
        max_qty = max_value / entry_price
        quantity = min(quantity, max_qty)

        return quantity

    def calculate_grid_position_size(
        self,
        balance: float,
        grid_levels: int,
        entry_price: float,
    ) -> float:
        """
        Calculate per-level position size for grid trading.
        Distributes the allocated capital evenly across grid levels.
        """
        if entry_price <= 0 or balance <= 0 or grid_levels <= 0:
            return 0.0

        total_allocation = balance * (self.max_position_pct / 100.0) * settings.TRADING_LEVERAGE
        per_level_value = total_allocation / grid_levels
        return per_level_value / entry_price

    def _find_position(self, positions: list[dict], symbol: str) -> dict | None:
        """Find an existing position for a symbol."""
        for pos in positions:
            if pos["symbol"] == symbol:
                return pos
        return None
