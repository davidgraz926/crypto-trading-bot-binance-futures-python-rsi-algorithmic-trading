import logging
import time
from typing import Optional

import pandas as pd

from config.settings import (
    DRY_RUN,
    MEV_MIN_SWAP_VALUE_USD,
    MEV_PRESSURE_WEIGHT,
    MEV_PRESSURE_WINDOW_SECONDS,
    MEV_WHALE_THRESHOLD_USD,
    POLL_INTERVAL_SECONDS,
    SYMBOL,
    TIMEFRAME,
)
from src.exchange import ExchangeClient
from src.mev_analyzer import compute_mev_pressure, detect_whale_activity
from src.risk_manager import (
    calculate_position_size,
    can_open_position,
    compute_stop_loss,
    compute_take_profit,
)
from src.strategy import Signal, evaluate, evaluate_with_mev
from src.utils import round_price, round_quantity

logger = logging.getLogger("trading_bot")


class TradingBot:
    """Core trading bot that ties together the exchange, strategy, and risk management."""

    def __init__(
        self,
        exchange: ExchangeClient,
        mempool_monitor: Optional[object] = None,
    ) -> None:
        self.exchange = exchange
        self.mempool_monitor = mempool_monitor
        self.running = False
        self._load_symbol_filters()

    def _load_symbol_filters(self) -> None:
        """Load tick size and step size from exchange info."""
        self.tick_size = 0.01
        self.step_size = 0.001
        info = self.exchange.get_symbol_info(SYMBOL)
        if info:
            for f in info.get("filters", []):
                if f["filterType"] == "PRICE_FILTER":
                    self.tick_size = float(f["tickSize"])
                elif f["filterType"] == "LOT_SIZE":
                    self.step_size = float(f["stepSize"])

    def run(self) -> None:
        """Main loop: poll candles, evaluate strategy, execute trades."""
        self.running = True
        logger.info(
            "Bot started (symbol=%s, timeframe=%s, dry_run=%s)",
            SYMBOL, TIMEFRAME, DRY_RUN,
        )
        while self.running:
            try:
                self._tick()
            except Exception:
                logger.exception("Unhandled error during tick")
            time.sleep(POLL_INTERVAL_SECONDS)

    def stop(self) -> None:
        self.running = False
        logger.info("Bot stop requested")

    def _tick(self) -> None:
        """Single iteration of the trading loop."""
        candles = self.exchange.fetch_candles(SYMBOL, TIMEFRAME)
        if candles.empty:
            logger.warning("No candle data received, skipping tick")
            return

        # Compute MEV pressure if monitor is available
        mev_pressure = None
        if self.mempool_monitor is not None:
            pending_swaps = self.mempool_monitor.get_pending_large_swaps(
                min_value_usd=MEV_MIN_SWAP_VALUE_USD
            )
            mev_pressure = compute_mev_pressure(
                pending_swaps,
                window_seconds=MEV_PRESSURE_WINDOW_SECONDS,
            )
            whale_swaps = detect_whale_activity(
                pending_swaps, MEV_WHALE_THRESHOLD_USD
            )
            if whale_swaps:
                logger.info("Whale activity detected: %d swaps", len(whale_swaps))

        # Use combined evaluation if MEV data is available
        if mev_pressure is not None:
            signal, rsi, combined = evaluate_with_mev(
                candles,
                mev_pressure=mev_pressure,
                mev_weight=MEV_PRESSURE_WEIGHT,
            )
            logger.info(
                "Combined score=%.2f (RSI=%s, MEV=%.2f)",
                combined or 0,
                f"{rsi:.2f}" if rsi is not None else "N/A",
                mev_pressure,
            )
        else:
            signal, rsi = evaluate(candles)

        if signal == Signal.HOLD:
            return

        open_positions = self.exchange.get_open_positions(SYMBOL)
        if not can_open_position(len(open_positions)):
            return

        balance = self.exchange.get_balance()
        entry_price = float(candles["close"].iloc[-1])
        raw_qty = calculate_position_size(balance, entry_price)
        quantity = round_quantity(raw_qty, self.step_size)
        if quantity <= 0:
            logger.warning("Calculated quantity is zero, skipping")
            return

        side = "BUY" if signal == Signal.BUY else "SELL"
        opposite = "SELL" if side == "BUY" else "BUY"

        if DRY_RUN:
            logger.info(
                "[DRY RUN] Would %s %.6f %s at ~%.2f (RSI=%.2f)",
                side, quantity, SYMBOL, entry_price, rsi,
            )
            return

        order = self.exchange.place_market_order(SYMBOL, side, quantity)
        if order is None:
            return

        sl_price = round_price(compute_stop_loss(entry_price, side), self.tick_size)
        tp_price = round_price(compute_take_profit(entry_price, side), self.tick_size)
        self.exchange.place_stop_loss(SYMBOL, opposite, sl_price, quantity)
        self.exchange.place_take_profit(SYMBOL, opposite, tp_price, quantity)
