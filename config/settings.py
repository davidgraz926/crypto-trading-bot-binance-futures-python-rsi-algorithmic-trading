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

# Logging
LOG_LEVEL = "INFO"
LOG_DIR = "logs"
