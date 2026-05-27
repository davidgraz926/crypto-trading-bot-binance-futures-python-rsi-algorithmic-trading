"""
Core trading bot engine.
Orchestrates the exchange, strategy, and risk management layers.
"""

import logging
import time
from typing import Optional

from config import settings
from src.exchange import ExchangeClient
from src.risk_manager import OrderProposal, RiskManager
from src.strategy import (
    BaseStrategy,
    GridStrategy,
    HybridStrategy,
    MarketRegime,
    Signal,
    TrendFollowStrategy,
)
from src.utils import round_step

logger = logging.getLogger("trading_bot.bot")


class TradingBot:
    """
    Main trading bot that ties everything together.

    Loop:
    1. Fetch latest market data
    2. Run strategy analysis
    3. Pass signals through risk management
    4. Execute approved orders
    5. Manage grid orders if in grid mode
    6. Sleep until next candle
    """

    def __init__(
        self,
        exchange: Optional[ExchangeClient] = None,
        strategy: Optional[BaseStrategy] = None,
        risk_manager: Optional[RiskManager] = None,
        dry_run: bool = True,
    ):
        self.exchange = exchange or ExchangeClient()
        self.risk_manager = risk_manager or RiskManager()
        self.dry_run = dry_run
        self._running = False

        # Select strategy based on config
        if strategy:
            self.strategy = strategy
        elif settings.STRATEGY_MODE == "trend_follow":
            self.strategy = TrendFollowStrategy()
        elif settings.STRATEGY_MODE == "grid":
            self.strategy = GridStrategy()
        else:
            self.strategy = HybridStrategy()

        self._tick_count = 0

    def start(self) -> None:
        """Initialize and start the trading bot."""
        logger.info("=" * 60)
        logger.info("TRADING BOT STARTING")
        logger.info("Strategy: %s", self.strategy.name())
        logger.info("Symbol: %s", settings.TRADING_SYMBOL)
        logger.info("Timeframe: %s", settings.TRADING_TIMEFRAME)
        logger.info("Leverage: %dx", settings.TRADING_LEVERAGE)
        logger.info("Dry run: %s", self.dry_run)
        logger.info("=" * 60)

        # Connect to exchange
        self.exchange.connect()

        if not self.dry_run:
            # Set leverage
            self.exchange.set_leverage()

            # Initialize risk manager with current balance
            balance = self.exchange.get_account_balance()
            self.risk_manager.set_initial_balance(balance)
            logger.info("Account balance: %.2f USDT", balance)
        else:
            self.risk_manager.set_initial_balance(10000.0)  # Paper trading balance
            logger.info("DRY RUN mode - using 10,000 USDT paper balance")

        self._running = True
        self._run_loop()

    def stop(self) -> None:
        """Gracefully stop the bot."""
        logger.info("Stopping bot...")
        self._running = False

    def _run_loop(self) -> None:
        """Main trading loop."""
        interval_seconds = self._timeframe_to_seconds(settings.TRADING_TIMEFRAME)

        while self._running:
            try:
                self._tick()
                self._tick_count += 1

                logger.info(
                    "Tick %d complete. Sleeping %ds until next candle...",
                    self._tick_count, interval_seconds,
                )
                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                self.stop()
            except Exception as e:
                logger.error("Error in main loop: %s", e, exc_info=True)
                time.sleep(30)  # Wait before retrying

    def _tick(self) -> None:
        """Single iteration of the trading loop."""
        symbol = settings.TRADING_SYMBOL

        # 1. Fetch market data
        logger.info("--- Tick %d: Fetching data for %s ---", self._tick_count + 1, symbol)
        df = self.exchange.get_klines(limit=settings.MIN_CANDLES)

        if len(df) < settings.MIN_CANDLES:
            logger.warning(
                "Not enough candles (%d/%d), skipping tick",
                len(df), settings.MIN_CANDLES,
            )
            return

        # 2. Run strategy
        signal = self.strategy.analyze(df)
        logger.info(
            "Signal: %s | Regime: %s | Confidence: %.2f | %s",
            signal.signal.value, signal.regime.value,
            signal.confidence, signal.reason,
        )

        # 3. Handle based on active strategy mode
        if isinstance(self.strategy, HybridStrategy) and self.strategy.active_strategy_name == "grid":
            self._handle_grid_mode(signal, symbol)
        else:
            self._handle_trend_mode(signal, symbol)

    def _handle_trend_mode(self, signal, symbol: str) -> None:
        """Handle trend-following signals."""
        if self.dry_run:
            balance = 10000.0
            positions = []
        else:
            balance = self.exchange.get_account_balance()
            positions = self.exchange.get_open_positions(symbol)

        # 4. Risk management gate
        proposal = self.risk_manager.evaluate_signal(
            signal=signal,
            current_balance=balance,
            open_positions=positions,
            symbol=symbol,
        )

        if proposal is None:
            logger.info("No trade this tick (signal filtered by risk manager)")
            return

        # 5. Execute
        self._execute_order(proposal)

    def _handle_grid_mode(self, signal, symbol: str) -> None:
        """Handle grid trading mode."""
        grid_strategy = (
            self.strategy.grid
            if isinstance(self.strategy, HybridStrategy)
            else self.strategy
        )

        if not isinstance(grid_strategy, GridStrategy):
            return

        if not grid_strategy.is_active:
            # Set up the grid
            current_price = signal.entry_price
            grid_levels = grid_strategy.calculate_grid(current_price)

            if self.dry_run:
                logger.info("DRY RUN: Would place %d grid orders", len(grid_levels))
                for level in grid_levels:
                    logger.info(
                        "  %s @ %.2f", level.side, level.price,
                    )
            else:
                balance = self.exchange.get_account_balance()
                qty_per_level = self.risk_manager.calculate_grid_position_size(
                    balance=balance,
                    grid_levels=len(grid_levels),
                    entry_price=current_price,
                )

                for level in grid_levels:
                    self.exchange.place_limit_order(
                        symbol=symbol,
                        side=level.side,
                        quantity=qty_per_level,
                        price=level.price,
                    )
                logger.info("Grid deployed: %d orders placed", len(grid_levels))
        else:
            # Grid is active - check for fills and replace
            if not self.dry_run:
                self._manage_active_grid(grid_strategy, symbol)
            else:
                logger.info("DRY RUN: Grid active, monitoring...")

    def _manage_active_grid(self, grid_strategy: GridStrategy, symbol: str) -> None:
        """Monitor and maintain the grid - replace filled orders."""
        open_orders = self.exchange.get_open_orders(symbol)
        open_order_ids = {str(o.get("orderId", "")) for o in open_orders}

        for level in grid_strategy.grid_levels:
            if level.order_id and level.order_id not in open_order_ids and not level.filled:
                level.filled = True
                logger.info("Grid level filled: %s @ %.2f", level.side, level.price)

                # Place opposite order at the same level
                opposite_side = "SELL" if level.side == "BUY" else "BUY"
                balance = self.exchange.get_account_balance()
                qty = self.risk_manager.calculate_grid_position_size(
                    balance=balance,
                    grid_levels=len(grid_strategy.grid_levels),
                    entry_price=level.price,
                )
                result = self.exchange.place_limit_order(
                    symbol=symbol,
                    side=opposite_side,
                    quantity=qty,
                    price=level.price,
                )
                level.side = opposite_side
                level.order_id = str(result.get("orderId", ""))
                level.filled = False

    def _execute_order(self, proposal: OrderProposal) -> None:
        """Execute an approved order proposal."""
        if self.dry_run:
            logger.info(
                "DRY RUN: %s %s %.6f %s @ %.2f | SL: %.2f | TP: %.2f",
                "CLOSE" if proposal.reduce_only else "OPEN",
                proposal.side, proposal.quantity, proposal.symbol,
                proposal.entry_price, proposal.stop_loss, proposal.take_profit,
            )
            return

        result = self.exchange.place_market_order(
            symbol=proposal.symbol,
            side=proposal.side,
            quantity=proposal.quantity,
            reduce_only=proposal.reduce_only,
        )

        logger.info("Order executed: %s", result.get("orderId", "unknown"))

    @staticmethod
    def _timeframe_to_seconds(timeframe: str) -> int:
        """Convert timeframe string to seconds."""
        multipliers = {
            "m": 60,
            "h": 3600,
            "d": 86400,
            "w": 604800,
        }
        unit = timeframe[-1]
        value = int(timeframe[:-1])
        return value * multipliers.get(unit, 60)
