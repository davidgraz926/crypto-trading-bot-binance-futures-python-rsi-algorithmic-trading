import os
from dotenv import load_dotenv

load_dotenv()

# Binance API credentials
BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET: str = os.getenv("BINANCE_API_SECRET", "")
BINANCE_TESTNET: bool = os.getenv("BINANCE_TESTNET", "true").lower() == "true"

# Trading pair
SYMBOL: str = "BTCUSDT"
TIMEFRAME: str = "1h"

# RSI strategy parameters
RSI_PERIOD: int = 14
RSI_OVERBOUGHT: float = 70.0
RSI_OVERSOLD: float = 30.0

# Risk management
LEVERAGE: int = 1
MAX_POSITION_SIZE_PCT: float = 0.02  # 2% of account balance per trade
STOP_LOSS_PCT: float = 0.02  # 2% stop loss
TAKE_PROFIT_PCT: float = 0.04  # 4% take profit

# Bot behaviour
DRY_RUN: bool = True  # Paper trading mode (no real orders)
POLLING_INTERVAL_SECONDS: int = 60
LOG_LEVEL: str = "INFO"

# Kline history length needed to compute indicators
KLINE_LIMIT: int = 100
