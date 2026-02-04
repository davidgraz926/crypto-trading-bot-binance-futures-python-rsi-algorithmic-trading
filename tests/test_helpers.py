"""Tests for utility helper functions."""

import pytest

from src.utils.helpers import round_step_size, round_price, pct_change


class TestRoundStepSize:
    def test_rounds_down(self) -> None:
        assert round_step_size(0.12345, 0.001) == 0.123

    def test_exact_value(self) -> None:
        assert round_step_size(1.0, 0.1) == 1.0

    def test_large_step(self) -> None:
        assert round_step_size(1.99, 1.0) == 1.0


class TestRoundPrice:
    def test_basic(self) -> None:
        assert round_price(50123.456, 0.01) == 50123.45

    def test_integer_tick(self) -> None:
        assert round_price(50123.9, 1.0) == 50123.0


class TestPctChange:
    def test_positive_change(self) -> None:
        assert pct_change(100.0, 110.0) == pytest.approx(10.0)

    def test_negative_change(self) -> None:
        assert pct_change(100.0, 90.0) == pytest.approx(-10.0)

    def test_zero_base_raises(self) -> None:
        with pytest.raises(ValueError, match="zero"):
            pct_change(0, 100)
