"""Tests for the Binance API client (mocked)."""

from unittest.mock import MagicMock, patch

import pytest

from src.api.binance_client import BinanceClient, TESTNET_URL, LIVE_URL


class TestBinanceClientInit:
    @patch("src.api.binance_client.UMFutures")
    def test_testnet_url(self, mock_futures: MagicMock) -> None:
        BinanceClient("key", "secret", testnet=True)
        mock_futures.assert_called_once_with(
            key="key", secret="secret", base_url=TESTNET_URL
        )

    @patch("src.api.binance_client.UMFutures")
    def test_live_url(self, mock_futures: MagicMock) -> None:
        BinanceClient("key", "secret", testnet=False)
        mock_futures.assert_called_once_with(
            key="key", secret="secret", base_url=LIVE_URL
        )


class TestGetAccountBalance:
    @patch("src.api.binance_client.UMFutures")
    def test_returns_balance(self, mock_futures: MagicMock) -> None:
        instance = mock_futures.return_value
        instance.balance.return_value = [
            {"asset": "USDT", "availableBalance": "1234.56"},
            {"asset": "BTC", "availableBalance": "0.5"},
        ]
        client = BinanceClient("key", "secret")
        assert client.get_account_balance("USDT") == 1234.56

    @patch("src.api.binance_client.UMFutures")
    def test_returns_zero_for_missing_asset(
        self, mock_futures: MagicMock
    ) -> None:
        instance = mock_futures.return_value
        instance.balance.return_value = [
            {"asset": "USDT", "availableBalance": "100"},
        ]
        client = BinanceClient("key", "secret")
        assert client.get_account_balance("ETH") == 0.0


class TestGetPosition:
    @patch("src.api.binance_client.UMFutures")
    def test_returns_position(self, mock_futures: MagicMock) -> None:
        instance = mock_futures.return_value
        instance.get_position_risk.return_value = [
            {"symbol": "BTCUSDT", "positionAmt": "0.01"},
        ]
        client = BinanceClient("key", "secret")
        pos = client.get_position("BTCUSDT")
        assert pos is not None
        assert pos["positionAmt"] == "0.01"

    @patch("src.api.binance_client.UMFutures")
    def test_returns_none_when_flat(self, mock_futures: MagicMock) -> None:
        instance = mock_futures.return_value
        instance.get_position_risk.return_value = [
            {"symbol": "BTCUSDT", "positionAmt": "0"},
        ]
        client = BinanceClient("key", "secret")
        assert client.get_position("BTCUSDT") is None
