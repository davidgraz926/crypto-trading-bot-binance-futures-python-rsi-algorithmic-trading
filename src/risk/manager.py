"""Risk management module."""

import logging

logger = logging.getLogger("trading_bot")


class RiskManager:
    """Enforces risk limits on trading activity.

    Args:
        max_position_size: Maximum position size (in base asset).
        stop_loss_pct: Stop-loss distance as a percentage of entry price.
        take_profit_pct: Take-profit distance as a percentage of entry price.
        max_drawdown_pct: Maximum allowed drawdown percentage before
            halting trading.
    """

    def __init__(
        self,
        max_position_size: float = 0.01,
        stop_loss_pct: float = 2.0,
        take_profit_pct: float = 4.0,
        max_drawdown_pct: float = 10.0,
    ) -> None:
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_drawdown_pct = max_drawdown_pct
        self._initial_balance: float | None = None

    def set_initial_balance(self, balance: float) -> None:
        """Record the starting balance for drawdown tracking."""
        self._initial_balance = balance
        logger.info("Initial balance recorded: %.4f", balance)

    def check_drawdown(self, current_balance: float) -> bool:
        """Return True if current drawdown exceeds the allowed limit."""
        if self._initial_balance is None or self._initial_balance == 0:
            return False
        drawdown = (
            (self._initial_balance - current_balance) / self._initial_balance
        ) * 100.0
        if drawdown >= self.max_drawdown_pct:
            logger.warning(
                "Max drawdown reached: %.2f%% (limit %.2f%%)",
                drawdown,
                self.max_drawdown_pct,
            )
            return True
        return False

    def compute_position_size(
        self, balance: float, price: float, leverage: int = 1
    ) -> float:
        """Calculate a safe position size.

        Returns the smaller of the risk-based size and the configured
        maximum position size.

        Args:
            balance: Available account balance (quote asset).
            price: Current mark / entry price.
            leverage: Active leverage multiplier.

        Returns:
            Position size in the base asset.
        """
        if price <= 0:
            return 0.0
        risk_based_size = (balance * leverage) / price
        size = min(risk_based_size, self.max_position_size)
        logger.debug(
            "Position size: %.6f (risk-based=%.6f, max=%.6f)",
            size,
            risk_based_size,
            self.max_position_size,
        )
        return size

    def stop_loss_price(self, entry_price: float, side: str) -> float:
        """Calculate the stop-loss price.

        Args:
            entry_price: Position entry price.
            side: "BUY" (long) or "SELL" (short).

        Returns:
            Trigger price for the stop-loss order.
        """
        offset = entry_price * (self.stop_loss_pct / 100.0)
        if side == "BUY":
            return entry_price - offset
        return entry_price + offset

    def take_profit_price(self, entry_price: float, side: str) -> float:
        """Calculate the take-profit price.

        Args:
            entry_price: Position entry price.
            side: "BUY" (long) or "SELL" (short).

        Returns:
            Trigger price for the take-profit order.
        """
        offset = entry_price * (self.take_profit_pct / 100.0)
        if side == "BUY":
            return entry_price + offset
        return entry_price - offset
