# CLAUDE.md - AI Assistant Guide

This document provides guidance for AI assistants working on the Binance Futures RSI Trading Bot codebase.

## Project Overview

**Purpose**: Automated cryptocurrency trading bot for Binance Futures using RSI (Relative Strength Index) algorithmic trading strategies.

**Key Technologies**:
- Python 3.9+
- Binance Futures API
- Technical Analysis (TA) libraries
- Async/await for real-time data handling

## Repository Structure

```
crypto-trading-bot-binance-futures-python-rsi-algorithmic-trading/
├── CLAUDE.md              # AI assistant guidance (this file)
├── README.md              # Project documentation
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore             # Git ignore patterns
├── config/
│   └── settings.py        # Configuration management
├── src/
│   ├── __init__.py
│   ├── main.py            # Application entry point
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── trading_bot.py # Main bot logic
│   │   └── order_manager.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── binance_client.py  # Binance API wrapper
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py        # Base strategy class
│   │   └── rsi_strategy.py # RSI-based trading strategy
│   ├── indicators/
│   │   ├── __init__.py
│   │   └── rsi.py         # RSI calculation
│   ├── risk/
│   │   ├── __init__.py
│   │   └── manager.py     # Risk management
│   └── utils/
│       ├── __init__.py
│       ├── logger.py      # Logging configuration
│       └── helpers.py     # Utility functions
└── tests/
    ├── __init__.py
    ├── conftest.py        # Pytest fixtures
    ├── test_strategies/
    ├── test_indicators/
    └── test_api/
```

## Development Guidelines

### Code Style

- Follow PEP 8 conventions
- Use type hints for function signatures
- Maximum line length: 88 characters (Black formatter default)
- Use docstrings for public functions and classes

### Naming Conventions

- **Files**: lowercase with underscores (`trading_bot.py`)
- **Classes**: PascalCase (`TradingBot`, `RSIStrategy`)
- **Functions/Methods**: lowercase with underscores (`calculate_rsi`)
- **Constants**: UPPERCASE with underscores (`MAX_POSITION_SIZE`)
- **Private methods**: prefix with underscore (`_internal_method`)

### Error Handling

- Use custom exception classes for domain-specific errors
- Always log exceptions with appropriate context
- Never expose API keys or sensitive data in error messages
- Implement graceful degradation for API failures

### Security Considerations

- **Never** commit API keys, secrets, or credentials
- Use environment variables for all sensitive configuration
- Validate all user inputs and API responses
- Implement rate limiting to respect Binance API limits
- Use testnet for development and testing

## Key Technical Patterns

### API Client Pattern

```python
class BinanceClient:
    """Wrapper for Binance Futures API with error handling."""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.client = UMFutures(key=api_key, secret=api_secret, base_url=self._get_base_url(testnet))

    async def get_klines(self, symbol: str, interval: str, limit: int) -> list:
        """Fetch candlestick data with retry logic."""
        pass
```

### Strategy Pattern

```python
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """Generate trading signal from market data."""
        pass
```

### Configuration Pattern

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment."""

    binance_api_key: str
    binance_api_secret: str
    trading_symbol: str = "BTCUSDT"
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0

    class Config:
        env_file = ".env"
```

## Trading Logic

### RSI Strategy Overview

1. **RSI Calculation**: Use standard 14-period RSI
2. **Entry Signals**:
   - Long when RSI crosses above oversold level (default: 30)
   - Short when RSI crosses below overbought level (default: 70)
3. **Exit Signals**:
   - Close long when RSI reaches overbought
   - Close short when RSI reaches oversold
4. **Risk Management**:
   - Stop-loss and take-profit levels
   - Position sizing based on account balance
   - Maximum drawdown limits

### Order Types

- **Market Orders**: For immediate execution
- **Limit Orders**: For better entry prices
- **Stop-Loss Orders**: For risk management
- **Take-Profit Orders**: For locking in gains

## Development Workflow

### Setting Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your Binance testnet API credentials
```

### Running the Bot

```bash
# Run in testnet mode (recommended for development)
python -m src.main --testnet

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Testing Guidelines

- Write unit tests for all strategy logic
- Mock API calls in tests
- Use pytest fixtures for common test data
- Test edge cases: API failures, invalid data, extreme market conditions

## Common Tasks for AI Assistants

### When Adding a New Strategy

1. Create new file in `src/strategies/`
2. Inherit from `BaseStrategy`
3. Implement `generate_signal()` method
4. Add corresponding tests in `tests/test_strategies/`
5. Update configuration to support new strategy parameters

### When Modifying API Integration

1. Update `src/api/binance_client.py`
2. Ensure proper error handling and retry logic
3. Test with Binance testnet first
4. Update any affected strategy code

### When Adding New Indicators

1. Create new file in `src/indicators/`
2. Implement calculation function with numpy/pandas
3. Add unit tests with known test cases
4. Document the indicator's parameters and usage

## Dependencies

Core dependencies to include in `requirements.txt`:

```
binance-futures-connector>=4.0.0
pandas>=2.0.0
numpy>=1.24.0
ta>=0.10.0
python-dotenv>=1.0.0
pydantic>=2.0.0
aiohttp>=3.8.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
```

## Important Reminders

1. **Always use testnet** for development and testing
2. **Never commit credentials** - use `.env` files
3. **Test thoroughly** before any live trading
4. **Implement proper logging** for debugging and monitoring
5. **Handle API rate limits** gracefully
6. **Validate all inputs** from external sources
7. **Use decimal types** for financial calculations when precision matters

## Git Workflow

- Branch naming: `feature/description`, `fix/description`, `docs/description`
- Write clear commit messages describing the change
- Keep commits atomic and focused
- Run tests before committing

## Troubleshooting

### Common Issues

1. **API Connection Errors**: Check network, API keys, and rate limits
2. **Invalid Symbol Errors**: Verify symbol format (e.g., "BTCUSDT")
3. **Insufficient Balance**: Check testnet account balance
4. **Order Rejection**: Verify position size meets minimum requirements

### Debug Mode

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file.
