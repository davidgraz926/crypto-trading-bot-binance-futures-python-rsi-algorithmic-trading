"""ABI definitions and contract addresses for DEX swap decoding."""

# Uniswap V2 Router
UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

# Uniswap V3 SwapRouter
UNISWAP_V3_ROUTER = "0xE592427A0AEce92De3Edee1F18E0157C05861564"

# PancakeSwap Router (BSC)
PANCAKESWAP_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

# Set of known DEX router addresses (lowercase for comparison)
DEX_ROUTERS: dict[str, str] = {
    UNISWAP_V2_ROUTER.lower(): "uniswap_v2",
    UNISWAP_V3_ROUTER.lower(): "uniswap_v3",
    PANCAKESWAP_ROUTER.lower(): "pancakeswap",
}

# Minimal ABIs: only swap-related function signatures for input decoding
UNISWAP_V2_SWAP_ABI = [
    {
        "name": "swapExactTokensForTokens",
        "type": "function",
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"},
        ],
    },
    {
        "name": "swapTokensForExactTokens",
        "type": "function",
        "inputs": [
            {"name": "amountOut", "type": "uint256"},
            {"name": "amountInMax", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"},
        ],
    },
    {
        "name": "swapExactETHForTokens",
        "type": "function",
        "inputs": [
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"},
        ],
    },
    {
        "name": "swapExactTokensForETH",
        "type": "function",
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"},
        ],
    },
]

UNISWAP_V3_SWAP_ABI = [
    {
        "name": "exactInputSingle",
        "type": "function",
        "inputs": [
            {
                "name": "params",
                "type": "tuple",
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "recipient", "type": "address"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMinimum", "type": "uint256"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
            }
        ],
    },
    {
        "name": "exactOutputSingle",
        "type": "function",
        "inputs": [
            {
                "name": "params",
                "type": "tuple",
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "recipient", "type": "address"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "amountOut", "type": "uint256"},
                    {"name": "amountInMaximum", "type": "uint256"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
            }
        ],
    },
]

PANCAKESWAP_SWAP_ABI = UNISWAP_V2_SWAP_ABI  # PancakeSwap uses the same interface

# Well-known token addresses (Ethereum mainnet, checksummed)
TOKEN_MAP: dict[str, str] = {
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "WETH",
    "0x2260fac5e5542a773aa44fbcfed7c193bc2c599": "WBTC",
    "0xdac17f958d2ee523a2206206994597c13d831ec7": "USDT",
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "USDC",
    "0x6b175474e89094c44da98b954eedeac495271d0f": "DAI",
    "0x4fabb145d64652a948d72533023f6e7a623c7c53": "BUSD",
    # BSC tokens
    "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c": "WBNB",
    "0x55d398326f99059ff775485246999027b3197955": "USDT",
    "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d": "USDC",
    "0xe9e7cea3dedca5984780bafc599bd69add087d56": "BUSD",
    "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c": "BTCB",
}

# Stablecoins used as quote tokens to determine swap direction
STABLECOINS = {"USDT", "USDC", "DAI", "BUSD"}

# Base assets whose price movement we care about
TRACKED_ASSETS = {"WETH", "WBTC", "WBNB", "BTCB"}


def token_symbol(address: str) -> str:
    """Resolve a token address to its symbol, or return a shortened address."""
    return TOKEN_MAP.get(address.lower(), address[:6] + "..." + address[-4:])
