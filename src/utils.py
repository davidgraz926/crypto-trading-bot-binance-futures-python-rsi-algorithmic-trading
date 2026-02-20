"""
Utility functions and logging setup.
"""

import logging
import os
from datetime import datetime, timezone

from config import settings


def setup_logging(name: str = "trading_bot") -> logging.Logger:
    """Configure and return a logger instance."""
    os.makedirs(settings.LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))

    if not logger.handlers:
        # Console handler
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter(settings.LOG_FORMAT))
        logger.addHandler(console)

        # File handler
        log_file = os.path.join(
            settings.LOG_DIR,
            f"bot_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log",
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
        logger.addHandler(file_handler)

    return logger


def timestamp_now() -> int:
    """Return current UTC timestamp in milliseconds."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def pct_change(old: float, new: float) -> float:
    """Calculate percentage change between two values."""
    if old == 0:
        return 0.0
    return ((new - old) / abs(old)) * 100.0


def round_step(value: float, step: float) -> float:
    """Round a value to the nearest step size (for exchange precision)."""
    if step == 0:
        return value
    precision = len(str(step).rstrip("0").split(".")[-1]) if "." in str(step) else 0
    return round(round(value / step) * step, precision)
