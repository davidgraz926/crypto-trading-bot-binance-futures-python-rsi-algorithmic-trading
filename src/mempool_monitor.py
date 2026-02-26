"""Blockchain mempool monitor — connects to an Ethereum/BSC node and streams pending DEX swaps."""

import logging
import threading
import time
from collections import deque
from typing import Optional

from web3 import Web3
from web3.exceptions import TransactionNotFound

from src.dex_abis import (
    DEX_ROUTERS,
    PANCAKESWAP_SWAP_ABI,
    STABLECOINS,
    TRACKED_ASSETS,
    UNISWAP_V2_SWAP_ABI,
    UNISWAP_V3_SWAP_ABI,
    token_symbol,
)
from src.mev_analyzer import PendingSwap
from src.token_price_cache import TokenPriceCache

logger = logging.getLogger("trading_bot")

# Map DEX name to its ABI fragments
_DEX_ABIS: dict[str, list[dict]] = {
    "uniswap_v2": UNISWAP_V2_SWAP_ABI,
    "uniswap_v3": UNISWAP_V3_SWAP_ABI,
    "pancakeswap": PANCAKESWAP_SWAP_ABI,
}


class MempoolMonitor:
    """Connects to a blockchain node and monitors pending swap transactions."""

    def __init__(
        self,
        rpc_url: str,
        chain: str = "ethereum",
        poll_interval: float = 5.0,
        price_cache: Optional[TokenPriceCache] = None,
    ) -> None:
        self._rpc_url = rpc_url
        self._chain = chain
        self._poll_interval = poll_interval
        self._price_cache = price_cache
        self._swaps: deque[PendingSwap] = deque(maxlen=1000)
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._w3: Optional[Web3] = None

    def _connect(self) -> Web3:
        """Create a Web3 connection using the configured RPC URL."""
        if self._rpc_url.startswith("ws"):
            provider = Web3.WebsocketProvider(self._rpc_url)
        else:
            provider = Web3.HTTPProvider(self._rpc_url)
        w3 = Web3(provider)
        if w3.is_connected():
            logger.info("Connected to %s node at %s", self._chain, self._rpc_url)
        else:
            logger.warning("Failed to connect to %s node", self._chain)
        return w3

    def start(self) -> None:
        """Begin listening for pending transactions in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Mempool monitor started (chain=%s)", self._chain)

    def stop(self) -> None:
        """Stop the monitoring loop."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=10)
        logger.info("Mempool monitor stopped")

    def get_pending_large_swaps(
        self, min_value_usd: float = 50_000.0
    ) -> list[PendingSwap]:
        """Return pending swap transactions above the minimum value threshold."""
        with self._lock:
            return [s for s in self._swaps if s.estimated_value_usd >= min_value_usd]

    def _run_loop(self) -> None:
        """Main monitoring loop with reconnection logic."""
        backoff = 1.0
        max_backoff = 60.0

        while self._running:
            try:
                self._w3 = self._connect()
                if not self._w3.is_connected():
                    raise ConnectionError("Node not reachable")

                backoff = 1.0  # reset on successful connect
                self._poll_pending_transactions()
            except Exception:
                logger.exception(
                    "Mempool monitor error, retrying in %.0fs", backoff
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)

    def _poll_pending_transactions(self) -> None:
        """Poll for pending transactions and process swap-like ones."""
        while self._running:
            try:
                block = self._w3.eth.get_block("pending", full_transactions=True)
                for tx in block.get("transactions", []):
                    self._process_transaction(tx)
            except Exception:
                logger.debug("Error fetching pending block, will retry")
                raise  # trigger reconnection in _run_loop

            time.sleep(self._poll_interval)

    def _process_transaction(self, tx: dict) -> None:
        """Check if a transaction is a DEX swap and record it."""
        to_addr = tx.get("to")
        if to_addr is None:
            return

        to_lower = to_addr.lower()
        dex_name = DEX_ROUTERS.get(to_lower)
        if dex_name is None:
            return

        input_data = tx.get("input", "0x")
        if len(input_data) < 10:
            return

        swap = self._decode_swap(tx, dex_name, input_data)
        if swap is not None:
            with self._lock:
                self._swaps.append(swap)

    def _decode_swap(
        self, tx: dict, dex_name: str, input_data: str
    ) -> Optional[PendingSwap]:
        """Attempt to decode a swap transaction's input data."""
        abi = _DEX_ABIS.get(dex_name, [])
        if not abi:
            return None

        try:
            contract = self._w3.eth.contract(abi=abi)
            func, params = contract.decode_function_input(input_data)
        except Exception:
            return None

        func_name = func.fn_name
        token_in_sym, token_out_sym, amount_raw = self._extract_swap_tokens(
            func_name, params, dex_name
        )

        if token_in_sym is None or token_out_sym is None:
            return None

        direction = self._determine_direction(token_in_sym, token_out_sym)
        if direction is None:
            return None

        estimated_usd = self._estimate_usd_value(
            token_in_sym, amount_raw, tx.get("value", 0)
        )

        gas_price_wei = tx.get("gasPrice", 0)
        gas_price_gwei = gas_price_wei / 1e9 if gas_price_wei else 0.0

        return PendingSwap(
            tx_hash=tx.get("hash", b"").hex() if isinstance(tx.get("hash"), bytes) else str(tx.get("hash", "")),
            chain=self._chain,
            dex=dex_name,
            token_in=token_in_sym,
            token_out=token_out_sym,
            amount_in_raw=amount_raw,
            estimated_value_usd=estimated_usd,
            direction=direction,
            gas_price_gwei=gas_price_gwei,
            timestamp=time.time(),
        )

    def _extract_swap_tokens(
        self, func_name: str, params: dict, dex_name: str
    ) -> tuple[Optional[str], Optional[str], int]:
        """Extract token symbols and amount from decoded swap parameters."""
        if dex_name in ("uniswap_v2", "pancakeswap"):
            path = params.get("path", [])
            if len(path) < 2:
                return None, None, 0
            token_in = token_symbol(path[0])
            token_out = token_symbol(path[-1])
            amount = params.get("amountIn", params.get("amountOut", 0))
            return token_in, token_out, int(amount)

        if dex_name == "uniswap_v3":
            p = params.get("params", params)
            token_in = token_symbol(str(p.get("tokenIn", "")))
            token_out = token_symbol(str(p.get("tokenOut", "")))
            amount = p.get("amountIn", p.get("amountOut", 0))
            return token_in, token_out, int(amount)

        return None, None, 0

    def _determine_direction(
        self, token_in: str, token_out: str
    ) -> Optional[str]:
        """Determine if this swap is a 'buy' or 'sell' of a tracked asset."""
        if token_out in TRACKED_ASSETS and token_in in STABLECOINS:
            return "buy"
        if token_in in TRACKED_ASSETS and token_out in STABLECOINS:
            return "sell"
        return None

    def _estimate_usd_value(
        self, token_in: str, amount_raw: int, tx_value: int
    ) -> float:
        """Estimate the USD value of the swap."""
        if token_in in STABLECOINS:
            return amount_raw / 1e6  # USDT/USDC use 6 decimals

        if tx_value > 0:
            eth_amount = tx_value / 1e18
            if self._price_cache:
                eth_price = self._price_cache.get_price_usd("WETH")
                if eth_price:
                    return eth_amount * eth_price
            return eth_amount * 3000.0  # rough fallback

        if self._price_cache:
            price = self._price_cache.get_price_usd(token_in)
            if price:
                decimals = 18 if token_in in ("WETH", "WBNB") else 8
                return (amount_raw / (10 ** decimals)) * price

        return 0.0
