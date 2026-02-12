import pandas as pd
import pytest

from scripts.parameter_sweep import (
    SweepRow,
    generate_synthetic_ohlcv,
    main,
    run_sweep,
)


class TestGenerateSyntheticOHLCV:
    def test_returns_correct_shape(self) -> None:
        df = generate_synthetic_ohlcv(bars=200)
        assert len(df) == 200
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]

    def test_high_above_low(self) -> None:
        df = generate_synthetic_ohlcv(bars=500)
        assert (df["high"] >= df["low"]).all()

    def test_deterministic_with_seed(self) -> None:
        df1 = generate_synthetic_ohlcv(bars=100, seed=7)
        df2 = generate_synthetic_ohlcv(bars=100, seed=7)
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_give_different_data(self) -> None:
        df1 = generate_synthetic_ohlcv(bars=100, seed=1)
        df2 = generate_synthetic_ohlcv(bars=100, seed=2)
        assert not df1["close"].equals(df2["close"])


class TestRunSweep:
    @pytest.fixture
    def ohlcv(self) -> pd.DataFrame:
        return generate_synthetic_ohlcv(bars=300, seed=42)

    def test_returns_list_of_sweep_rows(self, ohlcv: pd.DataFrame) -> None:
        rows = run_sweep(ohlcv, periods=[14], oversold_levels=[30], overbought_levels=[70])
        assert len(rows) == 1
        assert isinstance(rows[0], SweepRow)

    def test_multiple_combos(self, ohlcv: pd.DataFrame) -> None:
        rows = run_sweep(
            ohlcv,
            periods=[7, 14],
            oversold_levels=[25, 30],
            overbought_levels=[70, 75],
        )
        # 2 periods x 2 oversold x 2 overbought = 8 valid combos
        assert len(rows) == 8

    def test_filters_invalid_combos(self, ohlcv: pd.DataFrame) -> None:
        # oversold=80 > overbought=70 should be filtered out
        rows = run_sweep(
            ohlcv,
            periods=[14],
            oversold_levels=[30, 80],
            overbought_levels=[70],
        )
        assert len(rows) == 1  # only 30/70 is valid

    def test_results_sorted_by_sharpe(self, ohlcv: pd.DataFrame) -> None:
        rows = run_sweep(
            ohlcv,
            periods=[7, 14, 21],
            oversold_levels=[25, 30],
            overbought_levels=[70, 75],
        )
        sharpes = [r.sharpe_ratio for r in rows]
        assert sharpes == sorted(sharpes, reverse=True)

    def test_sweep_row_fields(self, ohlcv: pd.DataFrame) -> None:
        rows = run_sweep(ohlcv, periods=[14], oversold_levels=[30], overbought_levels=[70])
        row = rows[0]
        assert row.rsi_period == 14
        assert row.oversold == 30
        assert row.overbought == 70
        assert isinstance(row.total_return_pct, float)
        assert isinstance(row.win_rate, float)
        assert isinstance(row.total_trades, int)
        assert isinstance(row.max_drawdown_pct, float)
        assert isinstance(row.sharpe_ratio, float)
        assert isinstance(row.final_balance, float)


class TestMainCLI:
    def test_runs_with_defaults(self) -> None:
        rows = main(["--bars", "200", "--periods", "14", "--oversold", "30", "--overbought", "70"])
        assert len(rows) == 1

    def test_custom_grid(self) -> None:
        rows = main([
            "--bars", "200",
            "--periods", "7", "14",
            "--oversold", "25", "30",
            "--overbought", "70", "75",
        ])
        assert len(rows) == 8
