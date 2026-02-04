"""Application entry point for the RSI trading bot."""

import argparse
import sys

from config.settings import Settings
from src.bot.trading_bot import TradingBot
from src.utils.logger import setup_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Binance Futures RSI Trading Bot"
    )
    parser.add_argument(
        "--testnet",
        action="store_true",
        default=False,
        help="Force testnet mode regardless of .env setting",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings()

    if args.testnet:
        settings.use_testnet = True

    logger = setup_logger(level=settings.log_level)

    if not settings.binance_api_key or not settings.binance_api_secret:
        logger.error(
            "BINANCE_API_KEY and BINANCE_API_SECRET must be set. "
            "Copy .env.example to .env and fill in your credentials."
        )
        sys.exit(1)

    logger.info("Starting RSI Trading Bot (testnet=%s)", settings.use_testnet)

    bot = TradingBot(settings)
    try:
        bot.start()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        bot.stop()


if __name__ == "__main__":
    main()
