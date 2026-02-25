import logging
import os
from datetime import datetime

from config.settings import LOG_DIR, LOG_LEVEL


def setup_logging() -> logging.Logger:
    """Configure and return the application logger."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"bot_{timestamp}.log")

    logger = logging.getLogger("trading_bot")
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def round_price(price: float, tick_size: float) -> float:
    """Round a price to the exchange's tick size."""
    if tick_size <= 0:
        return price
    precision = len(str(tick_size).rstrip("0").split(".")[-1])
    return round(round(price / tick_size) * tick_size, precision)


def round_quantity(quantity: float, step_size: float) -> float:
    """Round a quantity to the exchange's step size."""
    if step_size <= 0:
        return quantity
    precision = len(str(step_size).rstrip("0").split(".")[-1])
    return round(quantity // step_size * step_size, precision)
