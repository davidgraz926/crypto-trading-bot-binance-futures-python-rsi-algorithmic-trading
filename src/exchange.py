import logging
from typing import Any, Optional

import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException

from config.settings import (
    BINANCE_API_KEY,
    BINANCE_API_SECRET,
    BINANCE_TESTNET,
    LEVERAGE,
    SYMBOL,
)

logger = logging.getLogger("trading_bot")


class ExchangeClient:
    """Wrapper around the Binance Futures API client."""

    def __init__(self) -> None:
        self.client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=BINANCE_TESTNET)
        logger.info("Exchange client initialised (testnet=%s)", BINANCE_TESTNET)
        self._configure_leverage()

    def _configure_leverage(self) -> None:
        try:
            self.client.futures_change_leverage(symbol=SYMBOL, leverage=LEVERAGE)
            logger.info("Leverage set to %dx for %s", LEVERAGE, SYMBOL)
        except BinanceAPIException as exc:
            logger.error("Failed to set leverage: %s", exc)

    def fetch_candles(
        self, symbol: str, interval: str, limit: int = 100
    ) -> pd.DataFrame:
        """Fetch recent kline/candle data and return as a DataFrame."""
        try:
            raw = self.client.futures_klines(
                symbol=symbol, interval=interval, limit=limit
            )
        except BinanceAPIException as exc:
            logger.error("Failed to fetch candles: %s", exc)
            return pd.DataFrame()

        df = pd.DataFrame(
            raw,
            columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades",
                "taker_buy_base", "taker_buy_quote", "ignore",
            ],
        )
        for col in ("open", "high", "low", "close", "volume"):
            df[col] = df[col].astype(float)
        return df

    def get_balance(self) -> float:
        """Return the available USDT balance on the futures account."""
        try:
            balances = self.client.futures_account_balance()
            for b in balances:
                if b["asset"] == "USDT":
                    return float(b["availableBalance"])
        except BinanceAPIException as exc:
            logger.error("Failed to fetch balance: %s", exc)
        return 0.0

    def get_open_positions(self, symbol: str) -> list[dict[str, Any]]:
        """Return any open positions for the given symbol."""
        try:
            positions = self.client.futures_position_information(symbol=symbol)
            return [p for p in positions if float(p["positionAmt"]) != 0]
        except BinanceAPIException as exc:
            logger.error("Failed to fetch positions: %s", exc)
            return []

    def get_symbol_info(self, symbol: str) -> Optional[dict[str, Any]]:
        """Return exchange info for a symbol (tick size, step size, etc.)."""
        try:
            info = self.client.futures_exchange_info()
            for s in info["symbols"]:
                if s["symbol"] == symbol:
                    return s
        except BinanceAPIException as exc:
            logger.error("Failed to fetch symbol info: %s", exc)
        return None

    def place_market_order(
        self, symbol: str, side: str, quantity: float
    ) -> Optional[dict[str, Any]]:
        """Place a futures market order."""
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity,
            )
            logger.info(
                "Market %s order placed: %s qty=%s", side, symbol, quantity
            )
            return order
        except BinanceAPIException as exc:
            logger.error("Order failed: %s", exc)
            return None

    def place_stop_loss(
        self, symbol: str, side: str, stop_price: float, quantity: float
    ) -> Optional[dict[str, Any]]:
        """Place a stop-market order for stop-loss."""
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="STOP_MARKET",
                stopPrice=stop_price,
                quantity=quantity,
                closePosition=False,
            )
            logger.info("Stop-loss set at %.2f for %s", stop_price, symbol)
            return order
        except BinanceAPIException as exc:
            logger.error("Stop-loss order failed: %s", exc)
            return None

    def place_take_profit(
        self, symbol: str, side: str, stop_price: float, quantity: float
    ) -> Optional[dict[str, Any]]:
        """Place a take-profit-market order."""
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="TAKE_PROFIT_MARKET",
                stopPrice=stop_price,
                quantity=quantity,
                closePosition=False,
            )
            logger.info("Take-profit set at %.2f for %s", stop_price, symbol)
            return order
        except BinanceAPIException as exc:
            logger.error("Take-profit order failed: %s", exc)
            return None
