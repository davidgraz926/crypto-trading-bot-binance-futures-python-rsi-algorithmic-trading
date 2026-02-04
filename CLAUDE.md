# CLAUDE.md - AI Assistant Guide

This document provides guidance for AI assistants working on the Binance Futures RSI Trading Bot codebase.

## Project Overview

**Purpose**: Automated cryptocurrency trading bot for Binance Futures using RSI (Relative Strength Index) algorithmic trading strategies.

**Status**: Core implementation complete with RSI strategy, risk management, and full test suite.

**Key Technologies**:
- Python 3.9+
- `binance-futures-connector` (UMFutures client)
- pandas / numpy for data handling
- pydantic-settings for configuration
- pytest for testing

## Repository Structure

```
crypto-trading-bot-binance-futures-python-rsi-algorithmic-trading/
├── CLAUDE.md                # AI assistant guidance (this file)
├── README.md                # Project documentation
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore patterns
├── config/
│   ├── __init__.py
│   └── settings.py          # Pydantic Settings (loads .env)
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point (argparse + bot startup)
│   ├── api/
│   │   ├── __init__.py
│   │   └── binance_client.py    # UMFutures wrapper with retry logic
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── trading_bot.py       # Main loop: fetch → signal → execute
│   │   └── order_manager.py     # Order placement + SL/TP lifecycle
│   ├── indicators/
│   │   ├── __init__.py
│   │   └── rsi.py               # Wilder-smoothed RSI calculation
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py              # BaseStrategy ABC + Signal/SignalType
│   │   └── rsi_strategy.py      # RSI crossover strategy
│   ├── risk/
│   │   ├── __init__.py
│   │   └── manager.py           # Position sizing, SL/TP, drawdown
│   └── utils/
│       ├── __init__.py
│       ├── logger.py            # Logging setup
│       └── helpers.py           # round_step_size, round_price, pct_change
└── tests/
    ├── __init__.py
    ├── conftest.py              # Shared fixtures (settings, OHLCV data)
    ├── test_helpers.py          # Utils tests
    ├── test_risk_manager.py     # Risk manager tests
    ├── test_api/
    │   ├── __init__.py
    │   └── test_binance_client.py   # Mocked API client tests
    ├── test_indicators/
    │   ├── __init__.py
    │   └── test_rsi.py              # RSI calculation tests
    └── test_strategies/
        ├── __init__.py
        └── test_rsi_strategy.py     # RSI strategy signal tests
```

## Architecture

### Data Flow

```
BinanceClient.get_klines()  →  RSIStrategy.generate_signal()  →  TradingBot._tick()
                                                                        │
                                                          ┌─────────────┤
                                                          ▼             ▼
                                                  RiskManager    OrderManager
                                                  (sizing/SL/TP) (place orders)
```

### Key Classes

| Class | File | Responsibility |
|-------|------|----------------|
| `Settings` | `config/settings.py` | Load configuration from `.env` via pydantic-settings |
| `BinanceClient` | `src/api/binance_client.py` | All Binance Futures API calls with retry |
| `TradingBot` | `src/bot/trading_bot.py` | Main loop orchestrating fetch → signal → execute |
| `OrderManager` | `src/bot/order_manager.py` | Market order + SL/TP placement lifecycle |
| `BaseStrategy` | `src/strategies/base.py` | ABC defining `generate_signal()` contract |
| `RSIStrategy` | `src/strategies/rsi_strategy.py` | RSI crossover entry/exit signals |
| `RiskManager` | `src/risk/manager.py` | Position sizing, drawdown check, SL/TP prices |
| `Signal` / `SignalType` | `src/strategies/base.py` | Signal dataclass and enum (LONG, SHORT, CLOSE_LONG, CLOSE_SHORT, HOLD) |

## Build & Run Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in Binance testnet credentials

# Run bot (testnet)
python -m src.main --testnet

# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Lint & format
black --check .
flake8 src/ tests/
mypy src/
```

## Development Guidelines

### Code Style

- PEP 8 with 88-char line length (Black default)
- Type hints on all function signatures
- Docstrings on all public classes and methods
- Logging via `logging.getLogger("trading_bot")` — never `print()`

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase` (`TradingBot`, `RSIStrategy`)
- **Functions/Methods**: `snake_case` (`calculate_rsi`, `get_klines`)
- **Constants**: `UPPER_SNAKE_CASE` (`TESTNET_URL`, `MAX_POSITION_SIZE`)
- **Private methods**: `_leading_underscore` (`_retry`, `_place_exit_orders`)

### Error Handling

- `BinanceClient._retry()` handles transient API errors with exponential backoff
- `TradingBot._run_loop()` catches exceptions per tick to keep the bot alive
- Never expose API keys in logs — `Settings` fields are not logged directly

### Security

- **Never** commit `.env` or credentials — `.gitignore` blocks `.env`
- All secrets come from environment variables via `pydantic-settings`
- Always develop against the **testnet** (`USE_TESTNET=true`)

## Trading Logic

### RSI Strategy

1. **RSI Calculation** (`src/indicators/rsi.py`): Wilder-smoothed 14-period RSI via `ewm(alpha=1/period)`
2. **Entry Signals** (`src/strategies/rsi_strategy.py`):
   - **LONG**: previous RSI <= 30, current RSI > 30 (crosses above oversold)
   - **SHORT**: previous RSI >= 70, current RSI < 70 (crosses below overbought)
3. **Exit Signals**:
   - **CLOSE_LONG**: RSI >= 70 (overbought)
   - **CLOSE_SHORT**: RSI <= 30 (oversold)
4. **Risk Management** (`src/risk/manager.py`):
   - Position size = min(balance * leverage / price, max_position_size)
   - Stop-loss: entry_price +/- stop_loss_pct%
   - Take-profit: entry_price +/- take_profit_pct%
   - Drawdown check halts bot if balance drops below threshold

### Order Flow

1. `TradingBot._tick()` fetches klines and generates a signal
2. If LONG/SHORT and no open position → `OrderManager.open_long/short()`
3. `OrderManager` places market order + STOP_MARKET + TAKE_PROFIT_MARKET
4. If CLOSE_LONG/SHORT and position exists → `OrderManager.close_position()` cancels pending orders then market-closes

## Testing

### Test Structure

- **`tests/conftest.py`**: Shared fixtures — `settings`, `sample_ohlcv` (random walk), `oversold_data`, `overbought_data`
- **`tests/test_indicators/test_rsi.py`**: RSI range, monotonic, edge cases
- **`tests/test_strategies/test_rsi_strategy.py`**: Signal generation under various data conditions
- **`tests/test_api/test_binance_client.py`**: Mocked `UMFutures` — init URLs, balance, position
- **`tests/test_risk_manager.py`**: Drawdown, position sizing, SL/TP price calculation
- **`tests/test_helpers.py`**: `round_step_size`, `round_price`, `pct_change`

### Testing Conventions

- Mock all Binance API calls with `unittest.mock.patch`
- Use `pytest.approx` for float comparisons
- Test both normal and edge cases (zero price, missing data, constant prices)

## Common Tasks for AI Assistants

### Adding a New Strategy

1. Create `src/strategies/my_strategy.py`
2. Inherit from `BaseStrategy`, implement `generate_signal(data) -> Signal`
3. Add tests in `tests/test_strategies/test_my_strategy.py`
4. Wire it into `TradingBot.__init__()` (or make strategy selection configurable)

### Adding a New Indicator

1. Create `src/indicators/my_indicator.py` with a pure function
2. Add tests in `tests/test_indicators/test_my_indicator.py` with known values
3. Import and use in the relevant strategy

### Modifying the API Client

1. Edit `src/api/binance_client.py`
2. Wrap new API calls with `self._retry()` for resilience
3. Add mocked tests in `tests/test_api/test_binance_client.py`

## Configuration Reference

All settings are in `config/settings.py` and loaded from `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `BINANCE_API_KEY` | `""` | Binance API key |
| `BINANCE_API_SECRET` | `""` | Binance API secret |
| `TRADING_SYMBOL` | `BTCUSDT` | Futures pair to trade |
| `LEVERAGE` | `1` | Leverage multiplier |
| `RSI_PERIOD` | `14` | RSI lookback period |
| `RSI_OVERBOUGHT` | `70.0` | Overbought threshold |
| `RSI_OVERSOLD` | `30.0` | Oversold threshold |
| `MAX_POSITION_SIZE` | `0.01` | Max position in base asset |
| `STOP_LOSS_PCT` | `2.0` | Stop-loss % from entry |
| `TAKE_PROFIT_PCT` | `4.0` | Take-profit % from entry |
| `MAX_DRAWDOWN_PCT` | `10.0` | Halt trading drawdown % |
| `USE_TESTNET` | `true` | Use Binance testnet |
| `LOG_LEVEL` | `INFO` | Logging level |
| `KLINE_INTERVAL` | `1h` | Candlestick interval |
| `KLINE_LIMIT` | `100` | Number of candles to fetch |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| API connection errors | Check network, keys, and rate limits |
| Invalid symbol | Verify format (e.g. `BTCUSDT` not `BTC/USDT`) |
| Insufficient balance | Fund your testnet account at testnet.binancefuture.com |
| Order rejection | Check minimum notional / quantity for the symbol |
| RSI all NaN | Ensure `kline_limit` > `rsi_period` |

Enable debug logging: set `LOG_LEVEL=DEBUG` in `.env`.
