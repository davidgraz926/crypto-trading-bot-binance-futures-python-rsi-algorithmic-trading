"""Utility functions for the trading bot."""

from decimal import Decimal, ROUND_DOWN


def round_step_size(quantity: float, step_size: float) -> float:
    """Round a quantity down to the nearest valid step size.

    Args:
        quantity: The raw quantity to round.
        step_size: The minimum step size for the symbol.

    Returns:
        Quantity rounded to valid step size.
    """
    step = Decimal(str(step_size))
    return float(
        (Decimal(str(quantity)) / step).to_integral_value(rounding=ROUND_DOWN)
        * step
    )


def round_price(price: float, tick_size: float) -> float:
    """Round a price to the nearest valid tick size.

    Args:
        price: The raw price to round.
        tick_size: The minimum tick size for the symbol.

    Returns:
        Price rounded to valid tick size.
    """
    tick = Decimal(str(tick_size))
    return float(
        (Decimal(str(price)) / tick).to_integral_value(rounding=ROUND_DOWN)
        * tick
    )


def pct_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values.

    Args:
        old_value: The original value.
        new_value: The new value.

    Returns:
        Percentage change as a float (e.g. 5.0 for 5%).

    Raises:
        ValueError: If old_value is zero.
    """
    if old_value == 0:
        raise ValueError("Cannot calculate percentage change from zero")
    return ((new_value - old_value) / abs(old_value)) * 100.0
