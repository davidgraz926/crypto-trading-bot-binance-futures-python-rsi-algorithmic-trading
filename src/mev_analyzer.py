"""MEV signal analysis — pure functions that aggregate pending swap data."""

import logging
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("trading_bot")


@dataclass
class PendingSwap:
    """A pending DEX swap detected in the mempool."""

    tx_hash: str
    chain: str  # "ethereum" or "bsc"
    dex: str  # "uniswap_v2", "uniswap_v3", "pancakeswap"
    token_in: str  # token symbol
    token_out: str  # token symbol
    amount_in_raw: int  # raw on-chain amount
    estimated_value_usd: float
    direction: str  # "buy" or "sell" relative to the tracked asset
    gas_price_gwei: float
    timestamp: float  # time.time() when detected


def compute_mev_pressure(
    swaps: list[PendingSwap],
    window_seconds: float = 300.0,
) -> Optional[float]:
    """Compute net MEV pressure score from -100 to +100.

    Positive values indicate buy pressure (large pending buys on DEXes),
    negative values indicate sell pressure.
    Returns None if no swaps fall within the time window.
    """
    now = time.time()
    cutoff = now - window_seconds

    recent = [s for s in swaps if s.timestamp >= cutoff]
    if not recent:
        return None

    buy_volume = sum(s.estimated_value_usd for s in recent if s.direction == "buy")
    sell_volume = sum(s.estimated_value_usd for s in recent if s.direction == "sell")
    total = buy_volume + sell_volume

    if total == 0:
        return 0.0

    # Net pressure: range [-1, +1] then scale to [-100, +100]
    raw_score = (buy_volume - sell_volume) / total * 100.0
    return max(-100.0, min(100.0, raw_score))


def detect_whale_activity(
    swaps: list[PendingSwap],
    whale_threshold_usd: float = 500_000.0,
) -> list[PendingSwap]:
    """Filter swaps to only those above the whale threshold."""
    return [s for s in swaps if s.estimated_value_usd >= whale_threshold_usd]


def compute_swap_velocity(
    swaps: list[PendingSwap],
    window_seconds: float = 60.0,
) -> float:
    """Compute the rate of large swaps per minute within the window.

    Returns the count of swaps that fall within the window,
    normalised to a per-minute rate.
    """
    now = time.time()
    cutoff = now - window_seconds

    recent = [s for s in swaps if s.timestamp >= cutoff]
    if not recent or window_seconds <= 0:
        return 0.0

    return len(recent) * (60.0 / window_seconds)
