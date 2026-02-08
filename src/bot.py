import logging
import time

from config import settings
from src.exchange import ExchangeClient
from src.risk_manager import RiskManager
from src.strategy import RSIStrategy, Signal

logger = logging.getLogger("trading_bot")


class TradingBot:
    """Core trading bot that ties together strategy, exchange, and risk management."""

    def __init__(
        self,
        exchange: ExchangeClient,
        strategy: RSIStrategy,
        risk_manager: RiskManager,
        symbol: str = settings.SYMBOL,
        dry_run: bool = settings.DRY_RUN,
    ) -> None:
        self.exchange = exchange
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.symbol = symbol
        self.dry_run = dry_run
        self.running = False

    def _execute_signal(self, signal: Signal) -> None:
        """Act on a trading signal."""
        if signal == Signal.HOLD:
            return

        open_positions = self.exchange.get_open_positions(self.symbol)
        side = signal.value  # "BUY" or "SELL"

        # Skip if already in a position in the same direction
        for pos in open_positions:
            amt = float(pos.get("positionAmt", 0))
            if (side == "BUY" and amt > 0) or (side == "SELL" and amt < 0):
                logger.info("Already in a %s position, skipping", side)
                return

        price = self.exchange.get_symbol_price(self.symbol)
        balance = self.exchange.get_account_balance()
        quantity = self.risk_manager.calculate_position_size(balance, price)

        if not self.risk_manager.validate_trade(balance, quantity, price):
            return

        sl = self.risk_manager.stop_loss_price(price, side)
        tp = self.risk_manager.take_profit_price(price, side)

        if self.dry_run:
            logger.info(
                "[DRY RUN] Would place %s order: %s %.4f @ %.2f | SL=%.2f TP=%.2f",
                side, self.symbol, quantity, price, sl, tp,
            )
            return

        self.exchange.place_market_order(self.symbol, side, quantity)
        logger.info(
            "Executed %s order: %s %.4f @ ~%.2f | SL=%.2f TP=%.2f",
            side, self.symbol, quantity, price, sl, tp,
        )

    def tick(self) -> None:
        """Execute a single iteration of the trading loop."""
        logger.info("--- Tick: fetching market data for %s ---", self.symbol)
        df = self.exchange.get_klines(self.symbol)
        signal = self.strategy.evaluate(df["close"])
        self._execute_signal(signal)

    def run(self) -> None:
        """Start the main trading loop."""
        self.running = True
        logger.info(
            "Bot started (symbol=%s, dry_run=%s, interval=%ds)",
            self.symbol, self.dry_run, settings.POLLING_INTERVAL_SECONDS,
        )

        self.exchange.set_leverage(self.symbol)

        while self.running:
            try:
                self.tick()
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                self.stop()
            except Exception:
                logger.exception("Error during tick")

            if self.running:
                time.sleep(settings.POLLING_INTERVAL_SECONDS)

    def stop(self) -> None:
        """Stop the trading loop."""
        self.running = False
        logger.info("Bot stopped")
