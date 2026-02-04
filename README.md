# Binance Futures RSI Trading Bot

Automated cryptocurrency trading bot for Binance Futures using RSI (Relative Strength Index) algorithmic trading.

## Features

- RSI crossover strategy with configurable overbought/oversold thresholds
- Automatic stop-loss and take-profit order placement
- Position sizing with maximum drawdown protection
- Binance Futures testnet support for safe development
- Retry logic for transient API failures

## Quick Start

```bash
# Clone and setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your Binance testnet API credentials

# Run
python -m src.main --testnet
```

## Configuration

All settings are loaded from environment variables or a `.env` file. See `.env.example` for the full list of options including RSI thresholds, risk parameters, and trading symbol.

## Testing

```bash
pytest tests/ -v
```

## Disclaimer

This software is for educational purposes. Use at your own risk. Always test on the Binance testnet before using real funds.
