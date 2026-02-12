"""Parameter sweep tool for RSI strategy optimisation.

Generates synthetic market data (or loads a CSV) and runs the backtester
across a grid of RSI parameter combinations, printing a ranked table of
results.

Usage:
    # Sweep with built-in synthetic data (no API keys needed)
    python -m scripts.parameter_sweep

    # Sweep with a CSV file containing OHLCV data
    python -m scripts.parameter_sweep --csv data/btcusdt_1h.csv

    # Customise the grid
    python -m scripts.parameter_sweep --periods 7 10 14 21 --oversold 20 25 30 --overbought 70 75 80
"""

import argparse
import itertools
import logging
import sys
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from src.backtester import Backtester, BacktestResult
from src.strategy import RSIStrategy

logging.getLogger("trading_bot").setLevel(logging.WARNING)

# ── Synthetic data generators ──────────────────────────────────────────


def generate_synthetic_ohlcv(
    bars: int = 1000,
    base_price: float = 40_000.0,
    volatility: float = 0.02,
    seed: int = 42,
) -> pd.DataFrame:
    """Create realistic-looking OHLCV data using geometric Brownian motion."""
    rng = np.random.default_rng(seed)

    log_returns = rng.normal(loc=0.0, scale=volatility, size=bars)
    closes = base_price * np.exp(np.cumsum(log_returns))

    # Build open/high/low around each close
    intra_vol = volatility * 0.5
    opens = closes * (1 + rng.normal(0, intra_vol * 0.3, size=bars))
    highs = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0, intra_vol, size=bars)))
    lows = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0, intra_vol, size=bars)))
    volume = rng.uniform(100, 5000, size=bars)

    return pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volume,
    })


# ── Sweep logic ────────────────────────────────────────────────────────


@dataclass
class SweepRow:
    """One row in the sweep results table."""

    rsi_period: int
    oversold: float
    overbought: float
    total_return_pct: float
    win_rate: float
    total_trades: int
    max_drawdown_pct: float
    sharpe_ratio: float
    final_balance: float


def run_sweep(
    df: pd.DataFrame,
    periods: List[int],
    oversold_levels: List[float],
    overbought_levels: List[float],
    initial_balance: float = 10_000.0,
    stop_loss_pct: float = 0.02,
    take_profit_pct: float = 0.04,
    leverage: int = 1,
    commission_pct: float = 0.0004,
) -> List[SweepRow]:
    """Run the backtester for every combination and return ranked results."""
    results: List[SweepRow] = []

    combos = list(itertools.product(periods, oversold_levels, overbought_levels))
    # Filter out invalid combos (oversold must be < overbought)
    combos = [(p, os, ob) for p, os, ob in combos if os < ob]

    for i, (period, oversold, overbought) in enumerate(combos, 1):
        strategy = RSIStrategy(
            period=period, overbought=overbought, oversold=oversold
        )
        bt = Backtester(
            strategy=strategy,
            initial_balance=initial_balance,
            max_position_pct=0.02,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            leverage=leverage,
            commission_pct=commission_pct,
        )
        r: BacktestResult = bt.run(df)
        results.append(SweepRow(
            rsi_period=period,
            oversold=oversold,
            overbought=overbought,
            total_return_pct=r.total_return_pct,
            win_rate=r.win_rate,
            total_trades=r.total_trades,
            max_drawdown_pct=r.max_drawdown_pct,
            sharpe_ratio=r.sharpe_ratio,
            final_balance=r.final_balance,
        ))

    # Sort by Sharpe ratio descending, then by return
    results.sort(key=lambda r: (r.sharpe_ratio, r.total_return_pct), reverse=True)
    return results


def print_table(rows: List[SweepRow]) -> None:
    """Print results as a formatted table to stdout."""
    header = (
        f"{'#':>3}  {'Period':>6}  {'OS':>5}  {'OB':>5}  "
        f"{'Return%':>8}  {'WinRate':>7}  {'Trades':>6}  "
        f"{'MaxDD%':>7}  {'Sharpe':>7}  {'Final$':>10}"
    )
    print("\n" + "=" * len(header))
    print("RSI Parameter Sweep Results")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for i, r in enumerate(rows, 1):
        print(
            f"{i:>3}  {r.rsi_period:>6}  {r.oversold:>5.0f}  {r.overbought:>5.0f}  "
            f"{r.total_return_pct:>8.2f}  {r.win_rate:>7.2%}  {r.total_trades:>6}  "
            f"{r.max_drawdown_pct:>7.2f}  {r.sharpe_ratio:>7.4f}  "
            f"{r.final_balance:>10.2f}"
        )

    print("-" * len(header))

    if rows:
        best = rows[0]
        print(
            f"\nBest combo: RSI({best.rsi_period}) with "
            f"oversold={best.oversold:.0f} / overbought={best.overbought:.0f}"
        )
        print(
            f"  Return: {best.total_return_pct:+.2f}%  |  "
            f"Sharpe: {best.sharpe_ratio:.4f}  |  "
            f"MaxDD: {best.max_drawdown_pct:.2f}%  |  "
            f"Trades: {best.total_trades}"
        )
    print()


# ── CLI ────────────────────────────────────────────────────────────────


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sweep RSI parameters and rank by Sharpe ratio"
    )
    parser.add_argument(
        "--csv", type=str, default=None,
        help="Path to OHLCV CSV file (must have open,high,low,close columns)",
    )
    parser.add_argument(
        "--periods", type=int, nargs="+", default=[7, 10, 14, 21],
        help="RSI periods to test",
    )
    parser.add_argument(
        "--oversold", type=float, nargs="+", default=[20, 25, 30],
        help="Oversold thresholds to test",
    )
    parser.add_argument(
        "--overbought", type=float, nargs="+", default=[70, 75, 80],
        help="Overbought thresholds to test",
    )
    parser.add_argument("--balance", type=float, default=10_000.0)
    parser.add_argument("--stop-loss", type=float, default=0.02)
    parser.add_argument("--take-profit", type=float, default=0.04)
    parser.add_argument("--leverage", type=int, default=1)
    parser.add_argument("--bars", type=int, default=1000,
                        help="Number of bars for synthetic data")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for synthetic data")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> List[SweepRow]:
    args = parse_args(argv)

    if args.csv:
        print(f"Loading data from {args.csv} ...")
        df = pd.read_csv(args.csv)
        for col in ("open", "high", "low", "close"):
            if col not in df.columns:
                print(f"ERROR: CSV missing required column '{col}'", file=sys.stderr)
                sys.exit(1)
            df[col] = pd.to_numeric(df[col], errors="coerce")
    else:
        print(f"Generating {args.bars} bars of synthetic BTC-like data (seed={args.seed}) ...")
        df = generate_synthetic_ohlcv(bars=args.bars, seed=args.seed)

    print(
        f"Sweeping: periods={args.periods}  "
        f"oversold={args.oversold}  overbought={args.overbought}"
    )

    rows = run_sweep(
        df,
        periods=args.periods,
        oversold_levels=args.oversold,
        overbought_levels=args.overbought,
        initial_balance=args.balance,
        stop_loss_pct=args.stop_loss,
        take_profit_pct=args.take_profit,
        leverage=args.leverage,
    )
    print_table(rows)
    return rows


if __name__ == "__main__":
    main()
