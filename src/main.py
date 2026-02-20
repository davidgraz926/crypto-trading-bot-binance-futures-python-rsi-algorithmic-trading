"""
Entry point for the trading bot.
Usage: python -m src.main [--dry-run] [--strategy trend_follow|grid|hybrid]
"""

import argparse
import signal
import sys

from config import settings
from src.bot import TradingBot
from src.exchange import ExchangeClient
from src.risk_manager import RiskManager
from src.strategy import GridStrategy, HybridStrategy, TrendFollowStrategy
from src.utils import setup_logging

logger = setup_logging()


def parse_args():
    parser = argparse.ArgumentParser(description="Crypto Trading Bot - Binance Futures")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Run in paper trading mode (default: True)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Run in live trading mode (overrides --dry-run)",
    )
    parser.add_argument(
        "--strategy",
        choices=["trend_follow", "grid", "hybrid"],
        default=settings.STRATEGY_MODE,
        help="Trading strategy to use",
    )
    return parser.parse_args()


def create_strategy(name: str):
    strategies = {
        "trend_follow": TrendFollowStrategy,
        "grid": GridStrategy,
        "hybrid": HybridStrategy,
    }
    return strategies[name]()


def main():
    args = parse_args()
    dry_run = not args.live

    logger.info("Initializing trading bot...")
    logger.info("Strategy: %s", args.strategy)
    logger.info("Mode: %s", "DRY RUN" if dry_run else "LIVE")

    if not dry_run and (not settings.BINANCE_API_KEY or not settings.BINANCE_API_SECRET):
        logger.error("BINANCE_API_KEY and BINANCE_API_SECRET must be set for live trading")
        sys.exit(1)

    exchange = ExchangeClient()
    risk_manager = RiskManager()
    strategy = create_strategy(args.strategy)

    bot = TradingBot(
        exchange=exchange,
        strategy=strategy,
        risk_manager=risk_manager,
        dry_run=dry_run,
    )

    # Graceful shutdown on SIGINT/SIGTERM
    def shutdown_handler(signum, frame):
        logger.info("Received shutdown signal")
        bot.stop()

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    bot.start()


if __name__ == "__main__":
    main()
