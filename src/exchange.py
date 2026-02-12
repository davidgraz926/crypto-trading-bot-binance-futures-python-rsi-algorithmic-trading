import logging
from typing import Any, Dict, List, Optional

import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException

from config import settings

logger = logging.getLogger("trading_bot")


class ExchangeClient:
    """Wrapper around the Binance Futures API client."""

    def __init__(
        self,
        api_key: str = settings.BINANCE_API_KEY,
        api_secret: str = settings.BINANCE_API_SECRET,
        testnet: bool = settings.BINANCE_TESTNET,
    ) -> None:
        self.client = Client(api_key, api_secret, testnet=testnet)
        logger.info("Exchange client initialised (testnet=%s)", testnet)

    def get_klines(
        self,
        symbol: str = settings.SYMBOL,
        interval: str = settings.TIMEFRAME,
        limit: int = settings.KLINE_LIMIT,
    ) -> pd.DataFrame:
        """Fetch historical kline/candlestick data and return as a DataFrame."""
        raw: List[List[Any]] = self.client.futures_klines(
            symbol=symbol, interval=interval, limit=limit
        )
        df = pd.DataFrame(
            raw,
            columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades",
                "taker_buy_base", "taker_buy_quote", "ignore",
            ],
        )
        for col in ("open", "high", "low", "close", "volume"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df.set_index("open_time", inplace=True)
        return df

    def get_account_balance(self) -> float:
        """Return the available USDT balance on the futures account."""
        balances: List[Dict[str, Any]] = self.client.futures_account_balance()
        for b in balances:
            if b["asset"] == "USDT":
                return float(b["availableBalance"])
        return 0.0

    def get_symbol_price(self, symbol: str = settings.SYMBOL) -> float:
        """Return the current mark price for the symbol."""
        ticker = self.client.futures_mark_price(symbol=symbol)
        return float(ticker["markPrice"])

    def set_leverage(
        self, symbol: str = settings.SYMBOL, leverage: int = settings.LEVERAGE
    ) -> None:
        """Set the leverage for a symbol."""
        try:
            self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            logger.info("Leverage set to %dx for %s", leverage, symbol)
        except BinanceAPIException as exc:
            logger.error("Failed to set leverage: %s", exc)
            raise

    def place_market_order(
        self, symbol: str, side: str, quantity: float
    ) -> Dict[str, Any]:
        """Place a futures market order.

        Args:
            symbol: Trading pair, e.g. 'BTCUSDT'.
            side: 'BUY' or 'SELL'.
            quantity: Order quantity.

        Returns:
            The order response dict from Binance.
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol, side=side, type="MARKET", quantity=quantity
            )
            logger.info(
                "Market order placed: %s %s %s (orderId=%s)",
                side, quantity, symbol, order.get("orderId"),
            )
            return order
        except BinanceAPIException as exc:
            logger.error("Order failed: %s", exc)
            raise

    def get_open_positions(
        self, symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return open positions, optionally filtered by symbol."""
        positions: List[Dict[str, Any]] = self.client.futures_position_information(
            **({"symbol": symbol} if symbol else {})
        )
        return [p for p in positions if float(p.get("positionAmt", 0)) != 0]
