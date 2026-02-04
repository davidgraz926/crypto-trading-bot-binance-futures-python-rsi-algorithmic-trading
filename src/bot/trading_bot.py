"""Main trading bot logic."""

import logging
import time

from config.settings import Settings
from src.api.binance_client import BinanceClient
from src.bot.order_manager import OrderManager
from src.risk.manager import RiskManager
from src.strategies.base import SignalType
from src.strategies.rsi_strategy import RSIStrategy

logger = logging.getLogger("trading_bot")


class TradingBot:
    """Orchestrates the trading loop.

    Connects strategy signals to order management while respecting risk
    limits.

    Args:
        settings: Application settings instance.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = BinanceClient(
            api_key=settings.binance_api_key,
            api_secret=settings.binance_api_secret,
            testnet=settings.use_testnet,
        )
        self.risk_manager = RiskManager(
            max_position_size=settings.max_position_size,
            stop_loss_pct=settings.stop_loss_pct,
            take_profit_pct=settings.take_profit_pct,
            max_drawdown_pct=settings.max_drawdown_pct,
        )
        self.order_manager = OrderManager(
            client=self.client,
            risk_manager=self.risk_manager,
            symbol=settings.trading_symbol,
        )
        self.strategy = RSIStrategy(
            period=settings.rsi_period,
            overbought=settings.rsi_overbought,
            oversold=settings.rsi_oversold,
        )
        self._running = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Initialize and start the trading loop."""
        symbol = self.settings.trading_symbol

        self.client.set_leverage(symbol, self.settings.leverage)

        balance = self.client.get_account_balance()
        self.risk_manager.set_initial_balance(balance)
        logger.info(
            "Bot started – symbol=%s  balance=%.4f USDT", symbol, balance
        )

        self._running = True
        self._run_loop()

    def stop(self) -> None:
        """Signal the trading loop to stop after the current iteration."""
        self._running = False
        logger.info("Bot stop requested")

    # ------------------------------------------------------------------
    # Core loop
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        """Main loop: fetch data -> generate signal -> execute."""
        symbol = self.settings.trading_symbol

        while self._running:
            try:
                self._tick(symbol)
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break
            except Exception:
                logger.exception("Error in trading loop")

            # Sleep until next candle (simplified – waits 60 s)
            time.sleep(60)

    def _tick(self, symbol: str) -> None:
        """Execute a single iteration of the trading loop."""
        # 1. Check drawdown
        balance = self.client.get_account_balance()
        if self.risk_manager.check_drawdown(balance):
            logger.warning("Drawdown limit hit – pausing")
            self.stop()
            return

        # 2. Fetch market data
        df = self.client.get_klines(
            symbol=symbol,
            interval=self.settings.kline_interval,
            limit=self.settings.kline_limit,
        )

        # 3. Generate signal
        signal = self.strategy.generate_signal(df)
        logger.info("Signal: %s – %s", signal.signal_type.value, signal.reason)

        if signal.signal_type == SignalType.HOLD:
            return

        # 4. Get current position
        position = self.client.get_position(symbol)
        pos_amt = float(position["positionAmt"]) if position else 0.0

        # 5. Act on signal
        price = self.client.get_mark_price(symbol)

        if signal.signal_type == SignalType.LONG and pos_amt == 0:
            qty = self.risk_manager.compute_position_size(
                balance, price, self.settings.leverage
            )
            if qty > 0:
                self.order_manager.open_long(qty, price)

        elif signal.signal_type == SignalType.SHORT and pos_amt == 0:
            qty = self.risk_manager.compute_position_size(
                balance, price, self.settings.leverage
            )
            if qty > 0:
                self.order_manager.open_short(qty, price)

        elif signal.signal_type == SignalType.CLOSE_LONG and pos_amt > 0:
            self.order_manager.close_position("SELL", abs(pos_amt))

        elif signal.signal_type == SignalType.CLOSE_SHORT and pos_amt < 0:
            self.order_manager.close_position("BUY", abs(pos_amt))
