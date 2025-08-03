import numpy as np
import pandas as pd

from qtools.metrics.factor import (
    factor_report,
    information_coefficient,
    information_ratio,
    quantile_returns,
    turnover,
)


def test_ic_perfect_positive():
    dates = pd.date_range("2024-01-01", periods=3)
    cols = list("ABCDE")
    signal = pd.DataFrame(
        [[1, 2, 3, 4, 5], [5, 4, 3, 2, 1], [2, 5, 1, 4, 3]],
        index=dates, columns=cols, dtype=float,
    )
    fret = signal.copy()  # identical ranks
    ic = information_coefficient(signal, fret, method="spearman")
    assert (ic - 1.0).abs().max() < 1e-10


def test_ic_perfect_negative():
    dates = pd.date_range("2024-01-01", periods=1)
    cols = list("ABCDE")
    signal = pd.DataFrame([[1, 2, 3, 4, 5]], index=dates, columns=cols, dtype=float)
    fret = pd.DataFrame([[5, 4, 3, 2, 1]], index=dates, columns=cols, dtype=float)
    ic = information_coefficient(signal, fret, method="spearman")
    assert (ic + 1.0).abs().max() < 1e-10


def test_information_ratio_shape():
    ic = pd.Series(np.random.RandomState(0).randn(100) * 0.05 + 0.02)
    ir = information_ratio(ic)
    assert isinstance(ir, float)
    assert ir > 0  # mean is positive


def test_quantile_returns_monotonic_on_signal():
    rng = np.random.RandomState(1)
    n_dates, n_symbols = 50, 50
    dates = pd.date_range("2024-01-01", periods=n_dates)
    cols = [f"S{i}" for i in range(n_symbols)]
    signal = pd.DataFrame(rng.randn(n_dates, n_symbols), index=dates, columns=cols)
    fret = signal * 0.01 + rng.randn(n_dates, n_symbols) * 0.005  # noisy but aligned

    qret = quantile_returns(signal, fret, n_quantiles=5)
    means = qret.mean()
    assert means[5] > means[1]  # top quintile beats bottom


def test_turnover_zero_when_weights_constant():
    dates = pd.date_range("2024-01-01", periods=5)
    w = pd.DataFrame(0.1, index=dates, columns=[f"S{i}" for i in range(10)])
    t = turnover(w)
    # First date is "initial allocation" so turnover > 0; rest should be 0
    assert (t.iloc[1:] == 0).all()


def test_factor_report_keys():
    dates = pd.date_range("2024-01-01", periods=30)
    cols = [f"S{i}" for i in range(20)]
    rng = np.random.RandomState(2)
    signal = pd.DataFrame(rng.randn(30, 20), index=dates, columns=cols)
    fret = pd.DataFrame(rng.randn(30, 20) * 0.01, index=dates, columns=cols)

    rep = factor_report(signal, fret, n_quantiles=5)
    assert set(rep.keys()) >= {
        "ic", "ic_mean", "ic_std", "ic_ir", "ic_hit_rate",
        "quantile_returns", "long_short_mean_return",
    }
