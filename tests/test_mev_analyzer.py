"""Tests for MEV analyzer functions."""

import time

from src.mev_analyzer import (
    PendingSwap,
    compute_mev_pressure,
    compute_swap_velocity,
    detect_whale_activity,
)


def _make_swap(
    direction: str = "buy",
    estimated_value_usd: float = 100_000.0,
    timestamp: float | None = None,
) -> PendingSwap:
    return PendingSwap(
        tx_hash="0xabc",
        chain="ethereum",
        dex="uniswap_v2",
        token_in="USDT",
        token_out="WETH",
        amount_in_raw=100_000_000_000,
        estimated_value_usd=estimated_value_usd,
        direction=direction,
        gas_price_gwei=30.0,
        timestamp=timestamp if timestamp is not None else time.time(),
    )


class TestComputeMevPressure:
    def test_returns_none_when_no_swaps(self) -> None:
        assert compute_mev_pressure([]) is None

    def test_positive_pressure_on_buy_swaps(self) -> None:
        swaps = [_make_swap(direction="buy", estimated_value_usd=100_000)]
        pressure = compute_mev_pressure(swaps)
        assert pressure is not None and pressure > 0

    def test_negative_pressure_on_sell_swaps(self) -> None:
        swaps = [_make_swap(direction="sell", estimated_value_usd=100_000)]
        pressure = compute_mev_pressure(swaps)
        assert pressure is not None and pressure < 0

    def test_balanced_swaps_give_zero_pressure(self) -> None:
        swaps = [
            _make_swap(direction="buy", estimated_value_usd=100_000),
            _make_swap(direction="sell", estimated_value_usd=100_000),
        ]
        pressure = compute_mev_pressure(swaps)
        assert pressure is not None and pressure == 0.0

    def test_pressure_clamped_to_range(self) -> None:
        swaps = [_make_swap(direction="buy", estimated_value_usd=10_000_000)]
        pressure = compute_mev_pressure(swaps)
        assert pressure is not None
        assert -100 <= pressure <= 100

    def test_all_buy_gives_100(self) -> None:
        swaps = [_make_swap(direction="buy", estimated_value_usd=500_000)]
        pressure = compute_mev_pressure(swaps)
        assert pressure == 100.0

    def test_all_sell_gives_negative_100(self) -> None:
        swaps = [_make_swap(direction="sell", estimated_value_usd=500_000)]
        pressure = compute_mev_pressure(swaps)
        assert pressure == -100.0

    def test_old_swaps_excluded_by_window(self) -> None:
        old_swap = _make_swap(direction="buy", timestamp=time.time() - 600)
        pressure = compute_mev_pressure([old_swap], window_seconds=300)
        assert pressure is None


class TestDetectWhaleActivity:
    def test_filters_below_threshold(self) -> None:
        swaps = [_make_swap(estimated_value_usd=100_000)]
        result = detect_whale_activity(swaps, whale_threshold_usd=500_000)
        assert len(result) == 0

    def test_includes_above_threshold(self) -> None:
        swaps = [_make_swap(estimated_value_usd=1_000_000)]
        result = detect_whale_activity(swaps, whale_threshold_usd=500_000)
        assert len(result) == 1


class TestComputeSwapVelocity:
    def test_zero_when_no_swaps(self) -> None:
        assert compute_swap_velocity([], window_seconds=60) == 0.0

    def test_correct_rate_60s_window(self) -> None:
        now = time.time()
        swaps = [_make_swap(timestamp=now - i) for i in range(10)]
        velocity = compute_swap_velocity(swaps, window_seconds=60)
        assert velocity == 10.0

    def test_excludes_old_swaps(self) -> None:
        now = time.time()
        swaps = [
            _make_swap(timestamp=now - 5),
            _make_swap(timestamp=now - 120),  # outside 60s window
        ]
        velocity = compute_swap_velocity(swaps, window_seconds=60)
        assert velocity == 1.0
