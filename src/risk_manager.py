import logging

from config.settings import (
    MAX_OPEN_POSITIONS,
    RISK_PER_TRADE_PCT,
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
)

logger = logging.getLogger("trading_bot")


def calculate_position_size(
    balance: float, entry_price: float, stop_loss_pct: float = STOP_LOSS_PCT
) -> float:
    """Determine position size based on account balance and risk percentage.

    Args:
        balance: Available account balance in USDT.
        entry_price: Expected entry price.
        stop_loss_pct: Stop-loss distance as a percentage of entry price.

    Returns:
        Position size in base asset units.
    """
    if entry_price <= 0 or balance <= 0:
        return 0.0
    risk_amount = balance * (RISK_PER_TRADE_PCT / 100.0)
    stop_distance = entry_price * (stop_loss_pct / 100.0)
    if stop_distance <= 0:
        return 0.0
    size = risk_amount / stop_distance
    logger.info(
        "Position size=%.6f (balance=%.2f, risk=%.2f%%, SL=%.2f%%)",
        size, balance, RISK_PER_TRADE_PCT, stop_loss_pct,
    )
    return size


def compute_stop_loss(entry_price: float, side: str) -> float:
    """Compute the stop-loss price for a given entry and side."""
    if side == "BUY":
        return entry_price * (1 - STOP_LOSS_PCT / 100.0)
    return entry_price * (1 + STOP_LOSS_PCT / 100.0)


def compute_take_profit(entry_price: float, side: str) -> float:
    """Compute the take-profit price for a given entry and side."""
    if side == "BUY":
        return entry_price * (1 + TAKE_PROFIT_PCT / 100.0)
    return entry_price * (1 - TAKE_PROFIT_PCT / 100.0)


def can_open_position(open_position_count: int) -> bool:
    """Check whether a new position is allowed."""
    allowed = open_position_count < MAX_OPEN_POSITIONS
    if not allowed:
        logger.info(
            "Max open positions reached (%d/%d)",
            open_position_count, MAX_OPEN_POSITIONS,
        )
    return allowed
