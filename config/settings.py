"""
Bot configuration and constants.
Loads from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# --- Binance API ---
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BINANCE_TESTNET = os.getenv("BINANCE_TESTNET", "true").lower() == "true"

# --- Trading ---
TRADING_SYMBOL = os.getenv("TRADING_SYMBOL", "BTCUSDT")
TRADING_TIMEFRAME = os.getenv("TRADING_TIMEFRAME", "1h")
TRADING_LEVERAGE = int(os.getenv("TRADING_LEVERAGE", "5"))

# --- Indicator Parameters ---
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

EMA_SHORT = 50
EMA_LONG = 200

BOLLINGER_PERIOD = 20
BOLLINGER_STD_DEV = 2.0

# --- Risk Management ---
MAX_POSITION_SIZE_PCT = float(os.getenv("MAX_POSITION_SIZE_PCT", "10.0"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "2.0"))
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "4.0"))
MAX_DRAWDOWN_PCT = float(os.getenv("MAX_DRAWDOWN_PCT", "15.0"))
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "3"))

# --- Grid Trading ---
GRID_LEVELS = int(os.getenv("GRID_LEVELS", "10"))
GRID_SPACING_PCT = float(os.getenv("GRID_SPACING_PCT", "0.5"))

# --- Strategy ---
STRATEGY_MODE = os.getenv("STRATEGY_MODE", "hybrid")  # trend_follow, grid, hybrid

# --- Logging ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

# --- Timeframe mapping for Binance API ---
TIMEFRAME_MAP = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "6h": "6h",
    "8h": "8h",
    "12h": "12h",
    "1d": "1d",
    "3d": "3d",
    "1w": "1w",
    "1M": "1M",
}

# Minimum candles needed for indicators to warm up
MIN_CANDLES = max(EMA_LONG, BOLLINGER_PERIOD, RSI_PERIOD, MACD_SLOW + MACD_SIGNAL) + 50
