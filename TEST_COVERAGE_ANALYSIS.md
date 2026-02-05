# Test Coverage Analysis

## Current State

**Coverage: 0%** — No source code or tests exist yet. The repository contains only `README.md` and `CLAUDE.md`.

This analysis maps the planned architecture (from `CLAUDE.md`) to a comprehensive testing strategy, prioritized by risk and criticality.

---

## Module-by-Module Test Plan

### 1. `src/indicators.py` — Technical Indicator Calculations

**Priority: CRITICAL** — Incorrect indicator math leads directly to bad trades and financial loss.

This is the highest-value module to test because it is **pure computation** with no external dependencies, making it easy to test thoroughly.

| Test Case | Description |
|---|---|
| `test_rsi_basic_calculation` | Verify RSI output against a known reference (e.g., TradingView or manual calculation) for a fixed dataset |
| `test_rsi_all_gains` | When all price changes are positive, RSI should approach 100 |
| `test_rsi_all_losses` | When all price changes are negative, RSI should approach 0 |
| `test_rsi_equal_gains_losses` | Equal average gains and losses should yield RSI ≈ 50 |
| `test_rsi_period_parameter` | Different period values (7, 14, 21) produce different results |
| `test_rsi_insufficient_data` | Fewer data points than the RSI period should raise an error or return NaN |
| `test_rsi_single_data_point` | Edge case: single candle |
| `test_rsi_constant_price` | Flat price series (zero change) — should return RSI = 50 or handle gracefully |
| `test_rsi_output_range` | RSI values must always be in [0, 100] across random inputs |
| `test_rsi_large_dataset` | Performance/correctness on 10,000+ candles |
| `test_rsi_float_precision` | Ensure no floating-point drift causes values outside [0, 100] |

**Gap if missing:** Silently wrong indicator values propagate into strategy decisions. This is the #1 area to test first.

---

### 2. `src/strategy.py` — RSI Trading Strategy

**Priority: CRITICAL** — This is where buy/sell decisions are made. Wrong logic = wrong trades.

| Test Case | Description |
|---|---|
| `test_buy_signal_on_oversold` | RSI crossing below 30 should generate a BUY signal |
| `test_sell_signal_on_overbought` | RSI crossing above 70 should generate a SELL signal |
| `test_no_signal_in_neutral_zone` | RSI between 30–70 should produce no signal |
| `test_custom_thresholds` | Configurable overbought/oversold thresholds (e.g., 80/20) should work |
| `test_signal_on_threshold_boundary` | RSI exactly at 30 or 70 — verify boundary behavior is documented and consistent |
| `test_no_duplicate_signals` | Multiple consecutive oversold readings shouldn't generate repeated BUY signals |
| `test_signal_requires_crossover` | Distinguish between RSI *being* below 30 vs. *crossing* below 30 |
| `test_strategy_with_empty_data` | No candle data should not crash; should return no signal |
| `test_strategy_state_persistence` | Strategy tracks its state correctly across multiple `evaluate()` calls |
| `test_strategy_is_interchangeable` | Verify the strategy conforms to a common interface (strategy pattern) |

**Gap if missing:** The bot could enter positions at the wrong time, hold when it should exit, or double-enter positions.

---

### 3. `src/risk_manager.py` — Position Sizing and Risk Management

**Priority: CRITICAL** — This module prevents catastrophic losses. Bugs here have outsized financial impact.

| Test Case | Description |
|---|---|
| `test_position_size_calculation` | Given account balance, risk %, and stop-loss distance, verify correct position size |
| `test_position_size_respects_max` | Position size should never exceed a configured maximum |
| `test_position_size_zero_balance` | Zero balance should return zero position size, not error |
| `test_stop_loss_placement` | Stop-loss price is calculated correctly for long and short positions |
| `test_take_profit_placement` | Take-profit price is calculated correctly for both directions |
| `test_risk_reward_ratio` | Verify configurable risk/reward ratio is enforced |
| `test_leverage_limits` | Leverage should not exceed configured maximum |
| `test_max_open_positions` | Reject new positions when max concurrent positions reached |
| `test_max_drawdown_circuit_breaker` | Trading should halt when drawdown exceeds threshold |
| `test_negative_inputs` | Negative balance, negative leverage, etc. should be rejected |
| `test_risk_per_trade_percentage` | Risk per trade must stay within bounds (e.g., 1–2% of account) |

**Gap if missing:** Unlimited position sizes, missing stop-losses, or broken circuit breakers could cause total account liquidation.

---

### 4. `src/exchange.py` — Binance API Client Wrapper

**Priority: HIGH** — This is the I/O boundary. Failures here mean orders don't execute or data is wrong.

| Test Case | Description |
|---|---|
| `test_fetch_klines_returns_ohlcv` | Mock API response and verify correct OHLCV DataFrame structure |
| `test_fetch_klines_handles_empty_response` | Empty response should return empty DataFrame, not crash |
| `test_place_order_sends_correct_params` | Verify order parameters (symbol, side, quantity, price) are passed correctly |
| `test_place_order_api_error` | Simulated API error (400, 500) should raise a descriptive exception |
| `test_rate_limiting` | Requests are throttled to stay within Binance rate limits |
| `test_connection_timeout` | Network timeout should raise a retryable exception |
| `test_retry_on_transient_failure` | Transient 5xx errors trigger automatic retry with backoff |
| `test_authentication` | Signed requests include correct HMAC signature (mocked) |
| `test_testnet_vs_production_url` | `BINANCE_TESTNET=true` uses testnet endpoint |
| `test_websocket_reconnection` | Simulated disconnect triggers automatic reconnection |
| `test_time_sync` | Server time synchronization is handled before signed requests |

**Testing approach:** All tests should use **mocks/fakes** for the Binance API — never hit the real API in unit tests. Consider a `FakeExchangeClient` for integration tests.

**Gap if missing:** Silent order failures, wrong order parameters, or unhandled disconnections during live trading.

---

### 5. `src/bot.py` — Core Trading Bot Logic (Orchestrator)

**Priority: HIGH** — This ties everything together. Integration-level defects live here.

| Test Case | Description |
|---|---|
| `test_bot_initialization` | Bot initializes with valid config and creates all components |
| `test_bot_trading_loop_cycle` | One iteration: fetch data → compute indicator → evaluate strategy → manage risk → place order |
| `test_bot_no_action_on_no_signal` | When strategy returns no signal, no order is placed |
| `test_bot_respects_dry_run_mode` | In paper-trading mode, orders are logged but not sent to exchange |
| `test_bot_logs_trade_decisions` | Every decision (enter, exit, hold) is logged with timestamp and reasoning |
| `test_bot_handles_exchange_errors` | Exchange errors don't crash the bot; it logs and continues |
| `test_bot_graceful_shutdown` | SIGINT/SIGTERM triggers clean shutdown (close positions optional, close connections) |
| `test_bot_startup_validation` | Missing API keys or invalid config prevent startup with clear error |

**Gap if missing:** The bot crashes mid-trade, silently skips cycles, or fails to log critical decisions.

---

### 6. `config/settings.py` — Configuration

**Priority: MEDIUM**

| Test Case | Description |
|---|---|
| `test_default_values` | All settings have sensible defaults |
| `test_env_override` | Environment variables override defaults |
| `test_invalid_config_rejected` | Invalid values (negative RSI period, leverage > max) raise errors at startup |
| `test_required_vars_missing` | Missing `BINANCE_API_KEY` raises a clear error, not a cryptic crash |

---

### 7. `src/utils.py` — Utility Functions

**Priority: MEDIUM**

| Test Case | Description |
|---|---|
| `test_logging_setup` | Logger is configured with correct format, level, and file output |
| `test_timestamp_formatting` | Timestamps are consistent and timezone-aware |
| `test_retry_decorator` | Retry logic respects max attempts and backoff |

---

## Cross-Cutting Test Categories

### Integration Tests (not in planned `tests/` yet)

The planned test structure only covers unit tests. The following integration tests are **missing from the plan**:

| Test | Description |
|---|---|
| `test_end_to_end_paper_trade` | Full cycle with mocked exchange: data → signal → order in dry-run mode |
| `test_config_to_execution` | Load real config → initialize bot → verify components wired correctly |
| `test_multiple_trading_cycles` | Run 100 cycles with synthetic data to catch state leaks |

### Tests Not Mentioned in Planned Structure

The `CLAUDE.md` plan includes `test_strategy.py`, `test_indicators.py`, and `test_risk_manager.py` but is **missing**:

- `tests/test_exchange.py` — Exchange client wrapper tests
- `tests/test_bot.py` — Bot orchestrator tests
- `tests/test_settings.py` — Configuration validation tests
- `tests/test_utils.py` — Utility function tests
- `tests/conftest.py` — Shared fixtures (mock exchange, sample OHLCV data, etc.)
- `tests/integration/` — Integration test directory

---

## Recommended Test Infrastructure

| Item | Why |
|---|---|
| `conftest.py` with shared fixtures | Avoid duplicating mock data across test files |
| Sample OHLCV datasets as JSON fixtures | Reproducible, known-good test data for indicators |
| `FakeExchangeClient` | Deterministic exchange behavior for bot/strategy tests |
| `pytest-cov` in requirements | Measure coverage from day one |
| `pytest-asyncio` | If WebSocket code uses async patterns |
| CI pipeline (GitHub Actions) | Run tests on every push/PR |

---

## Priority Summary

| Priority | Module | Reason |
|---|---|---|
| **1 (CRITICAL)** | `indicators.py` | Math errors → bad trades. Pure functions, easy to test. Start here. |
| **2 (CRITICAL)** | `strategy.py` | Decision logic errors → wrong entries/exits |
| **3 (CRITICAL)** | `risk_manager.py` | Risk failures → catastrophic financial loss |
| **4 (HIGH)** | `exchange.py` | I/O boundary failures → orders not executed or wrong |
| **5 (HIGH)** | `bot.py` | Orchestration bugs → missed trades, crashes |
| **6 (MEDIUM)** | `config/settings.py` | Bad config → unpredictable behavior |
| **7 (MEDIUM)** | `utils.py` | Support code — lower direct risk |

---

## Key Recommendations

1. **Start with `indicators.py` tests** — highest value, lowest complexity, no mocking needed
2. **Add `test_exchange.py` and `test_bot.py`** to the planned test structure — these are currently missing
3. **Create `tests/conftest.py`** with shared fixtures (sample OHLCV data, mock exchange client)
4. **Add integration tests** in `tests/integration/` for end-to-end paper trading flows
5. **Add `pytest-cov`** to `requirements.txt` and enforce a minimum coverage threshold (e.g., 80%)
6. **Set up GitHub Actions CI** to run tests on every push and PR
7. **Use property-based testing** (`hypothesis` library) for indicator calculations to catch edge cases that manual test cases miss (e.g., RSI always in [0, 100] for any valid input)
8. **Test the risk manager with adversarial inputs** — this is the last line of defense against financial loss
