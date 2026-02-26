import signal
import sys

from config.settings import MEV_CHAIN, MEV_ENABLED, MEV_POLL_INTERVAL_SECONDS, MEV_RPC_URL
from src.bot import TradingBot
from src.exchange import ExchangeClient
from src.utils import setup_logging


def main() -> None:
    logger = setup_logging()
    logger.info("Initialising trading bot...")

    exchange = ExchangeClient()

    mempool_monitor = None
    if MEV_ENABLED:
        from src.mempool_monitor import MempoolMonitor
        from src.token_price_cache import TokenPriceCache

        logger.info("MEV monitoring enabled (chain=%s)", MEV_CHAIN)
        price_cache = TokenPriceCache(exchange.client)
        mempool_monitor = MempoolMonitor(
            rpc_url=MEV_RPC_URL,
            chain=MEV_CHAIN,
            poll_interval=MEV_POLL_INTERVAL_SECONDS,
            price_cache=price_cache,
        )
        mempool_monitor.start()

    bot = TradingBot(exchange, mempool_monitor=mempool_monitor)

    def _shutdown(signum: int, frame: object) -> None:
        logger.info("Received signal %s, shutting down...", signum)
        bot.stop()
        if mempool_monitor is not None:
            mempool_monitor.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    bot.run()
    logger.info("Bot exited cleanly")
    sys.exit(0)


if __name__ == "__main__":
    main()
