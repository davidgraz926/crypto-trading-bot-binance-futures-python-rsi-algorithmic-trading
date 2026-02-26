"""Lightweight cache for converting on-chain token amounts to USD values."""

import logging
import time
from typing import Optional

logger = logging.getLogger("trading_bot")


class TokenPriceCache:
    """Caches token prices fetched from Binance for USD conversion."""

    def __init__(self, client: object, ttl_seconds: float = 30.0) -> None:
        """Initialise with a binance Client instance and cache TTL."""
        self._client = client
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, float]] = {}  # symbol -> (price, timestamp)

    def get_price_usd(self, token_symbol: str) -> Optional[float]:
        """Get the latest USD price for a token, using cache if fresh.

        Tries the USDT trading pair on Binance (e.g. ETHUSDT).
        Returns None if the price cannot be resolved.
        """
        symbol_map = {
            "WETH": "ETHUSDT",
            "WBTC": "BTCUSDT",
            "WBNB": "BNBUSDT",
            "BTCB": "BTCUSDT",
            "ETH": "ETHUSDT",
            "BTC": "BTCUSDT",
            "BNB": "BNBUSDT",
        }

        ticker = symbol_map.get(token_symbol)
        if ticker is None:
            # Try direct USDT pair
            ticker = f"{token_symbol}USDT"

        now = time.time()
        cached = self._cache.get(ticker)
        if cached and (now - cached[1]) < self._ttl:
            return cached[0]

        try:
            result = self._client.get_symbol_ticker(symbol=ticker)
            price = float(result["price"])
            self._cache[ticker] = (price, now)
            return price
        except Exception as exc:
            logger.debug("Failed to fetch price for %s: %s", ticker, exc)
            return None
