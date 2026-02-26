"""Tests for mempool monitor (mocked Web3 connections)."""

import time
from unittest.mock import MagicMock, patch

from src.dex_abis import UNISWAP_V2_ROUTER
from src.mempool_monitor import MempoolMonitor


class TestMempoolMonitorInit:
    def test_init_sets_chain(self) -> None:
        monitor = MempoolMonitor(rpc_url="http://localhost:8545", chain="bsc")
        assert monitor._chain == "bsc"

    def test_init_defaults_to_ethereum(self) -> None:
        monitor = MempoolMonitor(rpc_url="http://localhost:8545")
        assert monitor._chain == "ethereum"


class TestGetPendingLargeSwaps:
    def test_returns_empty_when_no_data(self) -> None:
        monitor = MempoolMonitor(rpc_url="http://localhost:8545")
        result = monitor.get_pending_large_swaps(min_value_usd=50_000)
        assert result == []

    def test_filters_by_min_value(self) -> None:
        from src.mev_analyzer import PendingSwap

        monitor = MempoolMonitor(rpc_url="http://localhost:8545")
        small_swap = PendingSwap(
            tx_hash="0x1",
            chain="ethereum",
            dex="uniswap_v2",
            token_in="USDT",
            token_out="WETH",
            amount_in_raw=10_000_000_000,
            estimated_value_usd=10_000,
            direction="buy",
            gas_price_gwei=30.0,
            timestamp=time.time(),
        )
        large_swap = PendingSwap(
            tx_hash="0x2",
            chain="ethereum",
            dex="uniswap_v2",
            token_in="USDT",
            token_out="WETH",
            amount_in_raw=100_000_000_000,
            estimated_value_usd=100_000,
            direction="buy",
            gas_price_gwei=30.0,
            timestamp=time.time(),
        )
        monitor._swaps.append(small_swap)
        monitor._swaps.append(large_swap)

        result = monitor.get_pending_large_swaps(min_value_usd=50_000)
        assert len(result) == 1
        assert result[0].tx_hash == "0x2"


class TestDetermineDirection:
    def test_stablecoin_to_tracked_is_buy(self) -> None:
        monitor = MempoolMonitor(rpc_url="http://localhost:8545")
        assert monitor._determine_direction("USDT", "WETH") == "buy"

    def test_tracked_to_stablecoin_is_sell(self) -> None:
        monitor = MempoolMonitor(rpc_url="http://localhost:8545")
        assert monitor._determine_direction("WETH", "USDT") == "sell"

    def test_unknown_pair_returns_none(self) -> None:
        monitor = MempoolMonitor(rpc_url="http://localhost:8545")
        assert monitor._determine_direction("LINK", "UNI") is None

    def test_stablecoin_to_stablecoin_returns_none(self) -> None:
        monitor = MempoolMonitor(rpc_url="http://localhost:8545")
        assert monitor._determine_direction("USDT", "USDC") is None


class TestEstimateUsdValue:
    def test_stablecoin_input_uses_6_decimals(self) -> None:
        monitor = MempoolMonitor(rpc_url="http://localhost:8545")
        value = monitor._estimate_usd_value("USDT", 100_000_000, 0)
        assert value == 100.0

    def test_eth_value_with_no_cache_uses_fallback(self) -> None:
        monitor = MempoolMonitor(rpc_url="http://localhost:8545")
        # 1 ETH = 1e18 wei, fallback price 3000
        value = monitor._estimate_usd_value("WETH", 0, 10**18)
        assert value == 3000.0
