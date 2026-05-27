"""
Binance Futures API client wrapper.
Handles all direct communication with the exchange.
"""

import logging
import time
from typing import Optional

import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException

from config import settings

logger = logging.getLogger("trading_bot.exchange")


class ExchangeClient:
    """Wrapper around the Binance Futures API."""

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = True,
    ):
        self.api_key = api_key or settings.BINANCE_API_KEY
        self.api_secret = api_secret or settings.BINANCE_API_SECRET
        self.testnet = testnet if api_key else settings.BINANCE_TESTNET
        self.client: Optional[Client] = None
        self._symbol_info_cache: dict = {}

    def connect(self) -> None:
        """Establish connection to Binance."""
        self.client = Client(
            self.api_key,
            self.api_secret,
            testnet=self.testnet,
        )
        if self.testnet:
            self.client.API_URL = "https://testnet.binancefuture.com"
        logger.info(
            "Connected to Binance %s", "Testnet" if self.testnet else "Live"
        )

    def _ensure_connected(self) -> Client:
        """Return the client, connecting if necessary."""
        if self.client is None:
            self.connect()
        assert self.client is not None
        return self.client

    def get_klines(
        self,
        symbol: str = "",
        interval: str = "",
        limit: int = 500,
    ) -> pd.DataFrame:
        """
        Fetch historical klines (candlestick data) and return as DataFrame.

        Returns DataFrame with columns:
            open_time, open, high, low, close, volume, close_time
        """
        client = self._ensure_connected()
        symbol = symbol or settings.TRADING_SYMBOL
        interval = interval or settings.TIMEFRAME_MAP.get(
            settings.TRADING_TIMEFRAME, settings.TRADING_TIMEFRAME
        )

        raw = self._api_call_with_retry(
            client.futures_klines,
            symbol=symbol,
            interval=interval,
            limit=limit,
        )

        df = pd.DataFrame(raw, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades",
            "taker_buy_base", "taker_buy_quote", "ignore",
        ])

        for col in ("open", "high", "low", "close", "volume"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)

        return df[["open_time", "open", "high", "low", "close", "volume", "close_time"]]

    def get_symbol_info(self, symbol: str = "") -> dict:
        """Get trading rules for a symbol (tick size, lot size, etc.)."""
        symbol = symbol or settings.TRADING_SYMBOL
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]

        client = self._ensure_connected()
        info = self._api_call_with_retry(client.futures_exchange_info)

        for s in info.get("symbols", []):
            if s["symbol"] == symbol:
                self._symbol_info_cache[symbol] = s
                return s

        raise ValueError(f"Symbol {symbol} not found on exchange")

    def get_ticker_price(self, symbol: str = "") -> float:
        """Get the current mark price for a symbol."""
        client = self._ensure_connected()
        symbol = symbol or settings.TRADING_SYMBOL
        result = self._api_call_with_retry(
            client.futures_mark_price, symbol=symbol
        )
        return float(result["markPrice"])

    def get_account_balance(self) -> float:
        """Get the total USDT balance available for trading."""
        client = self._ensure_connected()
        account = self._api_call_with_retry(client.futures_account)
        for asset in account.get("assets", []):
            if asset["asset"] == "USDT":
                return float(asset["availableBalance"])
        return 0.0

    def get_open_positions(self, symbol: str = "") -> list[dict]:
        """Get currently open positions."""
        client = self._ensure_connected()
        positions = self._api_call_with_retry(client.futures_position_information)
        result = []
        for pos in positions:
            amt = float(pos.get("positionAmt", 0))
            if amt != 0:
                if symbol and pos["symbol"] != symbol:
                    continue
                result.append({
                    "symbol": pos["symbol"],
                    "side": "LONG" if amt > 0 else "SHORT",
                    "size": abs(amt),
                    "entry_price": float(pos["entryPrice"]),
                    "unrealized_pnl": float(pos["unRealizedProfit"]),
                    "leverage": int(pos.get("leverage", 1)),
                })
        return result

    def set_leverage(self, symbol: str = "", leverage: int = 0) -> None:
        """Set leverage for a symbol."""
        client = self._ensure_connected()
        symbol = symbol or settings.TRADING_SYMBOL
        leverage = leverage or settings.TRADING_LEVERAGE
        self._api_call_with_retry(
            client.futures_change_leverage,
            symbol=symbol,
            leverage=leverage,
        )
        logger.info("Leverage set to %dx for %s", leverage, symbol)

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        reduce_only: bool = False,
    ) -> dict:
        """
        Place a market order on futures.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: "BUY" or "SELL"
            quantity: Order quantity
            reduce_only: If True, only reduces existing position
        """
        client = self._ensure_connected()
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity,
        }
        if reduce_only:
            params["reduceOnly"] = "true"

        result = self._api_call_with_retry(client.futures_create_order, **params)
        logger.info(
            "Market %s order placed: %s %s @ market (ID: %s)",
            side, quantity, symbol, result.get("orderId"),
        )
        return result

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        reduce_only: bool = False,
    ) -> dict:
        """Place a limit order on futures."""
        client = self._ensure_connected()
        params = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "quantity": quantity,
            "price": price,
            "timeInForce": "GTC",
        }
        if reduce_only:
            params["reduceOnly"] = "true"

        result = self._api_call_with_retry(client.futures_create_order, **params)
        logger.info(
            "Limit %s order placed: %s %s @ %s (ID: %s)",
            side, quantity, symbol, price, result.get("orderId"),
        )
        return result

    def cancel_all_orders(self, symbol: str = "") -> None:
        """Cancel all open orders for a symbol."""
        client = self._ensure_connected()
        symbol = symbol or settings.TRADING_SYMBOL
        self._api_call_with_retry(
            client.futures_cancel_all_open_orders, symbol=symbol
        )
        logger.info("All open orders cancelled for %s", symbol)

    def get_open_orders(self, symbol: str = "") -> list[dict]:
        """Get all open orders for a symbol."""
        client = self._ensure_connected()
        symbol = symbol or settings.TRADING_SYMBOL
        return self._api_call_with_retry(
            client.futures_get_open_orders, symbol=symbol
        )

    def _api_call_with_retry(self, func, max_retries: int = 3, **kwargs):
        """Execute an API call with retry logic for rate limits and network errors."""
        for attempt in range(max_retries):
            try:
                return func(**kwargs)
            except BinanceAPIException as e:
                if e.code == -1003:  # Rate limit
                    wait = 2 ** (attempt + 1)
                    logger.warning(
                        "Rate limited, waiting %ds before retry (%d/%d)",
                        wait, attempt + 1, max_retries,
                    )
                    time.sleep(wait)
                elif attempt == max_retries - 1:
                    logger.error("API call failed after %d retries: %s", max_retries, e)
                    raise
                else:
                    wait = 2 ** attempt
                    logger.warning(
                        "API error %s, retrying in %ds (%d/%d)",
                        e.code, wait, attempt + 1, max_retries,
                    )
                    time.sleep(wait)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error("Unexpected error after %d retries: %s", max_retries, e)
                    raise
                wait = 2 ** attempt
                logger.warning(
                    "Network error, retrying in %ds (%d/%d): %s",
                    wait, attempt + 1, max_retries, e,
                )
                time.sleep(wait)
        return None
