import logging
import math

from config import settings

logger = logging.getLogger("trading_bot")


class RiskManager:
    """Manages position sizing, stop-loss, and take-profit levels."""

    def __init__(
        self,
        max_position_pct: float = settings.MAX_POSITION_SIZE_PCT,
        stop_loss_pct: float = settings.STOP_LOSS_PCT,
        take_profit_pct: float = settings.TAKE_PROFIT_PCT,
        leverage: int = settings.LEVERAGE,
    ) -> None:
        self.max_position_pct = max_position_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.leverage = leverage

    def calculate_position_size(
        self, balance: float, price: float, precision: int = 3
    ) -> float:
        """Calculate the order quantity based on account balance and risk parameters.

        Args:
            balance: Available account balance in USDT.
            price: Current asset price.
            precision: Decimal precision for quantity rounding.

        Returns:
            The position size (quantity) to order.
        """
        risk_amount = balance * self.max_position_pct
        notional = risk_amount * self.leverage
        quantity = notional / price
        quantity = math.floor(quantity * 10**precision) / 10**precision

        logger.info(
            "Position size: %.{0}f (balance=%.2f, price=%.2f, risk_pct=%.2f%%, leverage=%dx)".format(
                precision
            ),
            quantity, balance, price, self.max_position_pct * 100, self.leverage,
        )
        return quantity

    def stop_loss_price(self, entry_price: float, side: str) -> float:
        """Calculate the stop-loss price for a position.

        Args:
            entry_price: The price at which the position was entered.
            side: 'BUY' for long positions, 'SELL' for short positions.

        Returns:
            The stop-loss trigger price.
        """
        if side == "BUY":
            sl = entry_price * (1 - self.stop_loss_pct)
        else:
            sl = entry_price * (1 + self.stop_loss_pct)
        logger.info("Stop-loss for %s at entry %.2f -> %.2f", side, entry_price, sl)
        return sl

    def take_profit_price(self, entry_price: float, side: str) -> float:
        """Calculate the take-profit price for a position.

        Args:
            entry_price: The price at which the position was entered.
            side: 'BUY' for long positions, 'SELL' for short positions.

        Returns:
            The take-profit trigger price.
        """
        if side == "BUY":
            tp = entry_price * (1 + self.take_profit_pct)
        else:
            tp = entry_price * (1 - self.take_profit_pct)
        logger.info("Take-profit for %s at entry %.2f -> %.2f", side, entry_price, tp)
        return tp

    def validate_trade(self, balance: float, quantity: float, price: float) -> bool:
        """Check whether a trade passes basic risk checks.

        Returns:
            True if the trade is within acceptable risk limits.
        """
        notional = quantity * price
        max_notional = balance * self.max_position_pct * self.leverage
        if notional > max_notional * 1.01:  # 1% tolerance for rounding
            logger.warning(
                "Trade rejected: notional %.2f exceeds max %.2f", notional, max_notional
            )
            return False
        if quantity <= 0:
            logger.warning("Trade rejected: quantity must be positive")
            return False
        return True
