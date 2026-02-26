import os
from dotenv import load_dotenv

load_dotenv()

# Binance API
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BINANCE_TESTNET = os.getenv("BINANCE_TESTNET", "true").lower() == "true"

# Trading pair
SYMBOL = "BTCUSDT"
TIMEFRAME = "1h"

# RSI strategy parameters
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Risk management
LEVERAGE = 1
RISK_PER_TRADE_PCT = 1.0  # percentage of balance to risk per trade
STOP_LOSS_PCT = 2.0       # stop-loss percentage from entry
TAKE_PROFIT_PCT = 4.0     # take-profit percentage from entry
MAX_OPEN_POSITIONS = 1

# Bot settings
POLL_INTERVAL_SECONDS = 60
DRY_RUN = True  # paper-trading mode; set False for live trading

# MEV Monitoring
MEV_ENABLED = os.getenv("MEV_ENABLED", "false").lower() == "true"
MEV_CHAIN = os.getenv("MEV_CHAIN", "ethereum")  # "ethereum" or "bsc"
MEV_RPC_URL = os.getenv("MEV_RPC_URL", "")
MEV_MIN_SWAP_VALUE_USD = float(os.getenv("MEV_MIN_SWAP_VALUE_USD", "50000"))
MEV_WHALE_THRESHOLD_USD = float(os.getenv("MEV_WHALE_THRESHOLD_USD", "500000"))
MEV_PRESSURE_WINDOW_SECONDS = float(os.getenv("MEV_PRESSURE_WINDOW_SECONDS", "300"))
MEV_PRESSURE_WEIGHT = float(os.getenv("MEV_PRESSURE_WEIGHT", "0.3"))
MEV_POLL_INTERVAL_SECONDS = float(os.getenv("MEV_POLL_INTERVAL_SECONDS", "5"))

# Logging
LOG_LEVEL = "INFO"
LOG_DIR = "logs"
