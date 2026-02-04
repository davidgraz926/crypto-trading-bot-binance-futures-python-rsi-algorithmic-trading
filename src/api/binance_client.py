"""Binance Futures API client wrapper."""

import logging
import time

import pandas as pd
from binance.um_futures import UMFutures
from binance.error import ClientError, ServerError

logger = logging.getLogger("trading_bot")

TESTNET_URL = "https://testnet.binancefuture.com"
LIVE_URL = "https://fapi.binance.com"


class BinanceClient:
    """Wrapper for Binance Futures API with error handling and retry logic."""

    def __init__(
        self, api_key: str, api_secret: str, testnet: bool = True
    ) -> None:
        base_url = TESTNET_URL if testnet else LIVE_URL
        self.client = UMFutures(
            key=api_key, secret=api_secret, base_url=base_url
        )
        self.testnet = testnet
        logger.info(
            "BinanceClient initialized (testnet=%s)", testnet
        )

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
    ) -> pd.DataFrame:
        """Fetch candlestick data and return as a DataFrame.

        Args:
            symbol: Trading pair symbol (e.g. "BTCUSDT").
            interval: Kline interval (e.g. "1m", "5m", "1h", "1d").
            limit: Number of klines to fetch (max 1500).

        Returns:
            DataFrame with columns: open_time, open, high, low, close,
            volume, close_time.
        """
        data = self._retry(
            self.client.klines, symbol=symbol, interval=interval, limit=limit
        )
        df = pd.DataFrame(
            data,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_volume",
                "trades",
                "taker_buy_base",
                "taker_buy_quote",
                "ignore",
            ],
        )
        for col in ("open", "high", "low", "close", "volume"):
            df[col] = df[col].astype(float)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
        return df

    def get_mark_price(self, symbol: str) -> float:
        """Get the current mark price for a symbol."""
        data = self._retry(self.client.mark_price, symbol=symbol)
        return float(data["markPrice"])

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    def get_account_balance(self, asset: str = "USDT") -> float:
        """Get available balance for an asset.

        Args:
            asset: Asset symbol (default "USDT").

        Returns:
            Available balance as float.
        """
        balances = self._retry(self.client.balance)
        for b in balances:
            if b["asset"] == asset:
                return float(b["availableBalance"])
        return 0.0

    def get_position(self, symbol: str) -> dict | None:
        """Get current position for a symbol.

        Returns:
            Position dict or None if no open position.
        """
        positions = self._retry(self.client.get_position_risk, symbol=symbol)
        for p in positions:
            if p["symbol"] == symbol and float(p["positionAmt"]) != 0:
                return p
        return None

    def set_leverage(self, symbol: str, leverage: int) -> None:
        """Set leverage for a symbol."""
        self._retry(
            self.client.change_leverage,
            symbol=symbol,
            leverage=leverage,
        )
        logger.info("Leverage set to %dx for %s", leverage, symbol)

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def place_market_order(
        self, symbol: str, side: str, quantity: float
    ) -> dict:
        """Place a market order.

        Args:
            symbol: Trading pair symbol.
            side: "BUY" or "SELL".
            quantity: Order quantity.

        Returns:
            Order response dict.
        """
        order = self._retry(
            self.client.new_order,
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=quantity,
        )
        logger.info(
            "Market %s %s %s filled (orderId=%s)",
            side,
            quantity,
            symbol,
            order.get("orderId"),
        )
        return order

    def place_stop_loss(
        self, symbol: str, side: str, stop_price: float, quantity: float
    ) -> dict:
        """Place a stop-market order for stop-loss.

        Args:
            symbol: Trading pair symbol.
            side: "BUY" or "SELL".
            stop_price: Trigger price.
            quantity: Order quantity.

        Returns:
            Order response dict.
        """
        return self._retry(
            self.client.new_order,
            symbol=symbol,
            side=side,
            type="STOP_MARKET",
            stopPrice=stop_price,
            quantity=quantity,
            reduceOnly=True,
        )

    def place_take_profit(
        self, symbol: str, side: str, stop_price: float, quantity: float
    ) -> dict:
        """Place a take-profit market order.

        Args:
            symbol: Trading pair symbol.
            side: "BUY" or "SELL".
            stop_price: Trigger price.
            quantity: Order quantity.

        Returns:
            Order response dict.
        """
        return self._retry(
            self.client.new_order,
            symbol=symbol,
            side=side,
            type="TAKE_PROFIT_MARKET",
            stopPrice=stop_price,
            quantity=quantity,
            reduceOnly=True,
        )

    def cancel_all_orders(self, symbol: str) -> None:
        """Cancel all open orders for a symbol."""
        self._retry(self.client.cancel_open_orders, symbol=symbol)
        logger.info("All open orders cancelled for %s", symbol)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _retry(func, retries: int = 3, delay: float = 1.0, **kwargs):
        """Call *func* with retries on transient errors."""
        for attempt in range(1, retries + 1):
            try:
                return func(**kwargs)
            except (ClientError, ServerError) as exc:
                if attempt == retries:
                    logger.error(
                        "API call failed after %d attempts: %s", retries, exc
                    )
                    raise
                logger.warning(
                    "API error (attempt %d/%d): %s – retrying in %.1fs",
                    attempt,
                    retries,
                    exc,
                    delay,
                )
                time.sleep(delay)
                delay *= 2
