import numpy as np
import pandas as pd
import pytest

from qtools.metrics.performance import (
    annualized_return,
    annualized_vol,
    calmar,
    max_drawdown,
    sharpe,
    sortino,
)


@pytest.fixture
def daily_returns():
    np.random.seed(42)
    return pd.Series(np.random.normal(0.0005, 0.01, 252))


def test_sharpe_sign(daily_returns):
    s = sharpe(daily_returns)
    # Positive mean → positive Sharpe
    assert s > 0


def test_sharpe_zero_vol():
    flat = pd.Series([0.0] * 100)
    assert np.isnan(sharpe(flat))


def test_sortino_ge_sharpe(daily_returns):
    # Sortino >= Sharpe when mean > 0 (penalizes only downside)
    assert sortino(daily_returns) >= sharpe(daily_returns)


def test_max_drawdown_known():
    # 1.0 → 1.10 → 0.88 → 0.968
    returns = pd.Series([0.10, -0.20, 0.10])
    mdd = max_drawdown(returns)
    assert abs(mdd - (-0.20)) < 1e-10


def test_max_drawdown_no_loss():
    returns = pd.Series([0.01, 0.02, 0.03])
    assert max_drawdown(returns) == 0.0


def test_annualized_return_one_year():
    # 252 days of 0.1% daily → check it's roughly 28.6%
    returns = pd.Series([0.001] * 252)
    ann = annualized_return(returns, 252)
    assert 0.28 < ann < 0.29


def test_annualized_vol():
    returns = pd.Series([0.01, -0.01] * 126)
    vol = annualized_vol(returns, 252)
    expected = returns.std() * np.sqrt(252)
    assert abs(vol - expected) < 1e-10


def test_calmar(daily_returns):
    c = calmar(daily_returns)
    ann = annualized_return(daily_returns)
    mdd = max_drawdown(daily_returns)
    assert abs(c - ann / abs(mdd)) < 1e-10
