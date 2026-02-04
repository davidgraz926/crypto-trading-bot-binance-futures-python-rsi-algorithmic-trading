"""Order lifecycle management."""

import logging

from src.api.binance_client import BinanceClient
from src.risk.manager import RiskManager
from src.utils.helpers import round_step_size, round_price

logger = logging.getLogger("trading_bot")


class OrderManager:
    """Manages order placement, stop-loss, and take-profit lifecycle.

    Args:
        client: Initialised Binance API client.
        risk_manager: Risk manager instance.
        symbol: Trading pair symbol.
    """

    def __init__(
        self,
        client: BinanceClient,
        risk_manager: RiskManager,
        symbol: str,
    ) -> None:
        self.client = client
        self.risk = risk_manager
        self.symbol = symbol

    def open_long(self, quantity: float, entry_price: float) -> dict:
        """Open a long position with stop-loss and take-profit.

        Args:
            quantity: Position size in base asset.
            entry_price: Current / expected entry price.

        Returns:
            Market order response dict.
        """
        order = self.client.place_market_order(
            self.symbol, "BUY", quantity
        )
        self._place_exit_orders("BUY", quantity, entry_price)
        return order

    def open_short(self, quantity: float, entry_price: float) -> dict:
        """Open a short position with stop-loss and take-profit.

        Args:
            quantity: Position size in base asset.
            entry_price: Current / expected entry price.

        Returns:
            Market order response dict.
        """
        order = self.client.place_market_order(
            self.symbol, "SELL", quantity
        )
        self._place_exit_orders("SELL", quantity, entry_price)
        return order

    def close_position(self, side: str, quantity: float) -> dict:
        """Close an existing position.

        Args:
            side: The *closing* side ("BUY" to close short, "SELL" to close
                  long).
            quantity: Absolute position quantity to close.

        Returns:
            Market order response dict.
        """
        self.client.cancel_all_orders(self.symbol)
        order = self.client.place_market_order(self.symbol, side, quantity)
        logger.info("Position closed for %s", self.symbol)
        return order

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _place_exit_orders(
        self, entry_side: str, quantity: float, entry_price: float
    ) -> None:
        """Place stop-loss and take-profit orders for a new position."""
        sl_price = self.risk.stop_loss_price(entry_price, entry_side)
        tp_price = self.risk.take_profit_price(entry_price, entry_side)

        # Exit side is the opposite of the entry side
        exit_side = "SELL" if entry_side == "BUY" else "BUY"

        self.client.place_stop_loss(
            self.symbol, exit_side, sl_price, quantity
        )
        logger.info("Stop-loss placed at %.2f", sl_price)

        self.client.place_take_profit(
            self.symbol, exit_side, tp_price, quantity
        )
        logger.info("Take-profit placed at %.2f", tp_price)
