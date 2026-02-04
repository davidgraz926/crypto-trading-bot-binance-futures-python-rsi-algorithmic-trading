"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Trading bot configuration.

    All values can be overridden via environment variables or a .env file.
    """

    # Binance API
    binance_api_key: str = ""
    binance_api_secret: str = ""

    # Trading
    trading_symbol: str = "BTCUSDT"
    leverage: int = 1

    # RSI
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0

    # Risk management
    max_position_size: float = 0.01
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 4.0
    max_drawdown_pct: float = 10.0

    # Application
    use_testnet: bool = True
    log_level: str = "INFO"
    kline_interval: str = "1h"
    kline_limit: int = 100

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
