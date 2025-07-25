import numpy as np
import pandas as pd
import pytest

from qtools.backtest.costs import CostModel
from qtools.backtest.engine import BacktestEngine


@pytest.fixture
def prices():
    idx = pd.bdate_range("2024-01-01", "2024-06-30")
    symbols = [f"S{i}" for i in range(10)]
    rng = np.random.RandomState(42)
    rets = pd.DataFrame(rng.normal(0.0005, 0.01, (len(idx), 10)),
                        index=idx, columns=symbols)
    close = (1 + rets).cumprod() * 100
    long = close.reset_index(names="date").melt(id_vars="date", var_name="symbol",
                                                 value_name="close")
    long["open"] = long["close"]
    long["high"] = long["close"]
    long["low"] = long["close"]
    long["volume"] = 1e6
    return long


def test_equal_weight_static_no_costs(prices):
    engine = BacktestEngine(prices)
    symbols = sorted(prices["symbol"].unique())
    dates = sorted(prices["date"].unique())
    weights = pd.DataFrame(1.0 / len(symbols), index=dates, columns=symbols)

    result = engine.run(weights)
    assert len(result.returns) == len(dates)
    # Costs are zero after day 1 (weights never change)
    assert result.costs.iloc[1:].sum() == 0.0


def test_sparse_weights_forward_fill(prices):
    engine = BacktestEngine(prices)
    symbols = sorted(prices["symbol"].unique())

    # Two sparse rebalance dates
    rb_dates = [pd.Timestamp("2024-01-31"), pd.Timestamp("2024-03-29")]
    weights = pd.DataFrame(0.0, index=rb_dates, columns=symbols)
    weights.iloc[0, :5] = 0.2   # first half long
    weights.iloc[1, 5:] = 0.2   # switch to second half

    result = engine.run(weights)
    # Daily weights span all trading days, equals the input on rebalance dates
    # and ffills between
    assert len(result.weights) == len(set(prices["date"]))
    # Turnover on second rebalance day is non-trivial (switching universes)
    t = result.turnover.loc[pd.Timestamp("2024-03-29")]
    assert t > 0.5


def test_costs_reduce_return(prices):
    symbols = sorted(prices["symbol"].unique())
    rb_dates = [pd.Timestamp("2024-01-31"),
                pd.Timestamp("2024-02-29"),
                pd.Timestamp("2024-03-29")]
    w = pd.DataFrame(0.0, index=rb_dates, columns=symbols)
    w.iloc[0, :5] = 0.2
    w.iloc[1, 5:] = 0.2  # full swap
    w.iloc[2, :5] = 0.2  # swap back

    no_cost = BacktestEngine(prices, cost_model=CostModel())
    with_cost = BacktestEngine(prices, cost_model=CostModel(commission_bps=100))

    r0 = no_cost.run(w).returns.sum()
    r1 = with_cost.run(w).returns.sum()
    assert r1 < r0


def test_no_lookahead(prices):
    """Position at day t should earn day t's return from yesterday's weight."""
    engine = BacktestEngine(prices)
    symbols = sorted(prices["symbol"].unique())
    # Single rebalance on Feb 1; the return on Feb 1 should come from t-1 weight
    # (which is 0 since the first non-zero weight is on Feb 1 itself).
    rb = pd.Timestamp("2024-02-01")
    w = pd.DataFrame(0.0, index=[rb], columns=symbols)
    w.iloc[0, 0] = 1.0

    r = engine.run(w)
    # Return on Feb 1 uses position from Jan 31 which was still 0
    # (weights ffilled forward but shifted back), so it should be 0
    assert r.returns.loc[rb] == 0.0 or abs(r.returns.loc[rb]) < 1e-10
