"""Tests for DEX ABI helpers."""

from src.dex_abis import DEX_ROUTERS, UNISWAP_V2_ROUTER, token_symbol


class TestTokenSymbol:
    def test_known_token_returns_symbol(self) -> None:
        assert token_symbol("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2") == "WETH"

    def test_case_insensitive(self) -> None:
        assert token_symbol("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2") == "WETH"

    def test_unknown_token_returns_shortened_address(self) -> None:
        addr = "0x0000000000000000000000000000000000000001"
        result = token_symbol(addr)
        assert result.startswith("0x0000")
        assert result.endswith("0001")
        assert len(result) < len(addr)


class TestDexRouters:
    def test_uniswap_v2_in_routers(self) -> None:
        assert UNISWAP_V2_ROUTER.lower() in DEX_ROUTERS

    def test_all_routers_have_dex_name(self) -> None:
        for addr, name in DEX_ROUTERS.items():
            assert isinstance(name, str)
            assert len(name) > 0
