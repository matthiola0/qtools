import numpy as np
import pandas as pd

from qtools.backtest.portfolio import equal_weight, signal_to_weights


def test_long_short_quintile_dollar_neutral():
    signal = pd.DataFrame(
        [list(range(10))],
        index=[pd.Timestamp("2024-01-31")],
        columns=[f"S{i}" for i in range(10)],
    )
    w = signal_to_weights(signal, n_quantiles=5, long_short=True, rebalance=None)
    row = w.iloc[0]
    assert abs(row.sum()) < 1e-10          # dollar-neutral
    assert abs(row.abs().sum() - 2.0) < 1e-10  # gross = 200%
    # Top quintile (S8, S9) are positive, bottom (S0, S1) are negative
    assert row["S9"] > 0 and row["S8"] > 0
    assert row["S0"] < 0 and row["S1"] < 0
    # Middle (S2..S7) are zero
    assert (row[[f"S{i}" for i in range(2, 8)]] == 0).all()


def test_long_only_fully_invested():
    signal = pd.DataFrame(
        [list(range(10))],
        index=[pd.Timestamp("2024-01-31")],
        columns=[f"S{i}" for i in range(10)],
    )
    w = signal_to_weights(signal, n_quantiles=5, long_short=False, rebalance=None)
    row = w.iloc[0]
    assert abs(row.sum() - 1.0) < 1e-10
    assert (row >= 0).all()


def test_monthly_rebalance_subsamples():
    idx = pd.bdate_range("2024-01-01", "2024-03-31")
    signal = pd.DataFrame(
        np.random.RandomState(0).randn(len(idx), 10),
        index=idx,
        columns=[f"S{i}" for i in range(10)],
    )
    w = signal_to_weights(signal, rebalance="M")
    assert len(w) == 3  # Jan, Feb, Mar ends


def test_equal_weight_on_boolean_mask():
    mask = pd.DataFrame(
        [[True, True, False], [False, True, True]],
        index=pd.date_range("2024-01-01", periods=2),
        columns=list("ABC"),
    )
    w = equal_weight(mask)
    assert (w.sum(axis=1) == 1.0).all()
    assert w.iloc[0, 0] == 0.5
    assert w.iloc[1, 2] == 0.5
