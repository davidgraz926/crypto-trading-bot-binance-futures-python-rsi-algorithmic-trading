# CLAUDE.md

This file provides guidance for AI assistants working on this repository.

## Project Overview

This is a **cryptocurrency algorithmic trading bot** for **Binance Futures** written in Python. It implements an **RSI (Relative Strength Index)**-based trading strategy. The project is currently in its initial scaffolding phase with no implementation code yet.

### Project Intent

- Connect to the Binance Futures API to execute trades
- Use RSI technical indicators to generate buy/sell signals
- Automate trading on futures markets with configurable parameters
- Support risk management (stop-loss, take-profit, position sizing)

## Current State

The repository is at its initial stage. Only `README.md` exists with a project title. All code, configuration, dependencies, and tests need to be implemented.

## Repository Structure (Planned)

When building out this project, follow this recommended structure:

```
.
├── CLAUDE.md              # This file - AI assistant guidance
├── README.md              # Project documentation
├── requirements.txt       # Python dependencies
├── .env.example           # Template for environment variables (never commit .env)
├── .gitignore             # Git ignore rules
├── config/
│   └── settings.py        # Bot configuration and constants
├── src/
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── bot.py             # Core trading bot logic
│   ├── exchange.py        # Binance API client wrapper
│   ├── strategy.py        # RSI trading strategy implementation
│   ├── indicators.py      # Technical indicator calculations (RSI, etc.)
│   ├── risk_manager.py    # Position sizing and risk management
│   └── utils.py           # Utility functions and helpers
├── tests/
│   ├── __init__.py
│   ├── test_strategy.py
│   ├── test_indicators.py
│   └── test_risk_manager.py
└── logs/                  # Runtime log output (gitignored)
```

## Development Guidelines

### Language and Runtime

- **Language:** Python 3.9+
- **Package management:** pip with `requirements.txt`
- **Virtual environment:** Use `venv` or `virtualenv`

### Expected Core Dependencies

- `python-binance` - Binance API client
- `pandas` - Data manipulation for OHLCV data
- `numpy` - Numerical computations
- `ta` or `TA-Lib` - Technical analysis indicators (RSI)
- `python-dotenv` - Environment variable management
- `websocket-client` - Real-time market data via WebSockets
- `pytest` - Testing framework

### Setup and Running

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your Binance API credentials

# Run the bot
python -m src.main
```

### Environment Variables

The following environment variables are expected (store in `.env`, never commit):

| Variable | Description |
|---|---|
| `BINANCE_API_KEY` | Binance API key |
| `BINANCE_API_SECRET` | Binance API secret |
| `BINANCE_TESTNET` | Set to `true` for testnet (recommended for development) |

### Security Rules

- **NEVER** commit `.env` files, API keys, or secrets
- **NEVER** hardcode credentials in source files
- Always use environment variables for sensitive configuration
- Always include `.env` and credential files in `.gitignore`
- Use Binance testnet for development and testing
- Validate and sanitize all external inputs

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_strategy.py
```

### Code Conventions

- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Use `logging` module instead of `print()` for all output
- Prefer descriptive variable names (e.g., `rsi_period` not `rp`)
- Keep functions focused and single-purpose
- Handle API errors and network failures gracefully with retries
- Use async patterns where appropriate for WebSocket connections

### Trading Strategy Notes

**RSI (Relative Strength Index):**
- RSI measures momentum on a 0-100 scale
- Typical overbought threshold: 70 (sell signal)
- Typical oversold threshold: 30 (buy signal)
- Default period: 14 candles
- Strategy parameters should be configurable, not hardcoded

### Key Architectural Decisions

- Separate exchange connectivity from trading logic for testability
- Strategy pattern: trading strategies should be interchangeable modules
- All trading parameters belong in configuration, not in code
- Implement dry-run/paper-trading mode before live trading
- Log all trade decisions with timestamps and reasoning for auditing

### Git Workflow

- `main` branch contains stable code
- Feature branches use descriptive names
- Commit messages should be clear and concise
- Do not commit generated files, logs, or cache directories

### Common Pitfalls

- Binance API has rate limits; implement request throttling
- Futures trading involves leverage; always implement risk controls
- RSI can give false signals in strongly trending markets; consider additional confirmations
- Always handle WebSocket disconnections and implement reconnection logic
- Time synchronization with Binance servers is required for signed requests
