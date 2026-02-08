"""Entry point for the RSI trading bot."""

import sys

from config import settings
from src.bot import TradingBot
from src.exchange import ExchangeClient
from src.risk_manager import RiskManager
from src.strategy import RSIStrategy
from src.utils import setup_logging


def main() -> None:
    logger = setup_logging(settings.LOG_LEVEL)

    if not settings.BINANCE_API_KEY or not settings.BINANCE_API_SECRET:
        logger.error(
            "BINANCE_API_KEY and BINANCE_API_SECRET must be set. "
            "Copy .env.example to .env and fill in your credentials."
        )
        sys.exit(1)

    logger.info("Initialising RSI Trading Bot")
    logger.info("Symbol: %s | Timeframe: %s", settings.SYMBOL, settings.TIMEFRAME)
    logger.info("Dry run: %s", settings.DRY_RUN)

    exchange = ExchangeClient()
    strategy = RSIStrategy()
    risk_manager = RiskManager()

    bot = TradingBot(
        exchange=exchange,
        strategy=strategy,
        risk_manager=risk_manager,
    )
    bot.run()


if __name__ == "__main__":
    main()
