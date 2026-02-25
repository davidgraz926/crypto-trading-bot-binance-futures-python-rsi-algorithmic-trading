# Crypto Trading Bot — Binance Futures RSI Strategy

An algorithmic trading bot for Binance Futures that uses the **RSI (Relative Strength Index)** to generate buy and sell signals.

## Features

- Connects to Binance Futures (testnet or live)
- RSI-based entry signals (oversold → buy, overbought → sell)
- Automated stop-loss and take-profit orders
- Configurable risk management (position sizing, leverage)
- Dry-run / paper-trading mode
- Structured logging to file and console

## Quick Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your Binance API key and secret

# Run the bot
python -m src.main
```

## Configuration

All parameters live in `config/settings.py`:

| Parameter | Default | Description |
|---|---|---|
| `SYMBOL` | BTCUSDT | Trading pair |
| `TIMEFRAME` | 1h | Candle interval |
| `RSI_PERIOD` | 14 | RSI look-back window |
| `RSI_OVERSOLD` | 30 | Buy threshold |
| `RSI_OVERBOUGHT` | 70 | Sell threshold |
| `LEVERAGE` | 1 | Futures leverage |
| `RISK_PER_TRADE_PCT` | 1.0 | % of balance risked per trade |
| `STOP_LOSS_PCT` | 2.0 | Stop-loss distance (%) |
| `TAKE_PROFIT_PCT` | 4.0 | Take-profit distance (%) |
| `DRY_RUN` | True | Paper-trade mode |

## Testing

```bash
pytest -v
```

## Project Structure

```
config/settings.py    — Bot configuration and constants
src/main.py           — Entry point
src/bot.py            — Core trading loop
src/exchange.py       — Binance API client wrapper
src/strategy.py       — RSI signal evaluation
src/indicators.py     — Technical indicator calculations
src/risk_manager.py   — Position sizing and risk controls
src/utils.py          — Logging setup and helpers
tests/                — Unit tests
```

## Disclaimer

This software is for **educational purposes only**. Trading cryptocurrency futures involves substantial risk of loss. Use the testnet for development and never trade with funds you cannot afford to lose.
