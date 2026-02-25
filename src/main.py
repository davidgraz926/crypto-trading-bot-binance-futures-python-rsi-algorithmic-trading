import signal
import sys

from src.bot import TradingBot
from src.exchange import ExchangeClient
from src.utils import setup_logging


def main() -> None:
    logger = setup_logging()
    logger.info("Initialising trading bot...")

    exchange = ExchangeClient()
    bot = TradingBot(exchange)

    def _shutdown(signum: int, frame: object) -> None:
        logger.info("Received signal %s, shutting down...", signum)
        bot.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    bot.run()
    logger.info("Bot exited cleanly")
    sys.exit(0)


if __name__ == "__main__":
    main()
