import numpy as np
import pandas as pd


def information_coefficient(
    signal: pd.DataFrame,
    forward_returns: pd.DataFrame,
    method: str = "spearman",
) -> pd.Series:
    """Per-date cross-sectional correlation between signal and forward returns.

    Rank IC (default 'spearman') is the standard factor-research metric.
    """
    dates = signal.index.intersection(forward_returns.index)
    cols = signal.columns.intersection(forward_returns.columns)
    s = signal.loc[dates, cols]
    r = forward_returns.loc[dates, cols]
    return s.corrwith(r, axis=1, method=method)


def information_ratio(ic: pd.Series) -> float:
    """IR = mean(IC) / std(IC). Unannualized — multiply by sqrt(freq) downstream."""
    ic = ic.dropna()
    if len(ic) == 0 or ic.std() == 0:
        return float("nan")
    return float(ic.mean() / ic.std())


def quantile_returns(
    signal: pd.DataFrame,
    forward_returns: pd.DataFrame,
    n_quantiles: int = 5,
) -> pd.DataFrame:
    """Mean forward return per signal quantile per date.

    Returns wide DataFrame: index = dates, columns = 1..n_quantiles.
    """
    dates = signal.index.intersection(forward_returns.index)
    cols = signal.columns.intersection(forward_returns.columns)
    s = signal.loc[dates, cols]
    r = forward_returns.loc[dates, cols]

    labels = list(range(1, n_quantiles + 1))
    records = {}
    for date in s.index:
        row_s = s.loc[date].dropna()
        row_r = r.loc[date].reindex(row_s.index).dropna()
        valid = row_s.loc[row_r.index]
        if len(valid) < n_quantiles:
            continue
        try:
            bins = pd.qcut(valid, n_quantiles, labels=labels, duplicates="drop")
        except ValueError:
            continue
        records[date] = row_r.groupby(bins, observed=False).mean()

    if not records:
        return pd.DataFrame(columns=labels)
    return pd.DataFrame(records).T


def turnover(weights: pd.DataFrame) -> pd.Series:
    """One-way turnover per date (half of |Δweights| sum)."""
    t = weights.diff().abs().sum(axis=1) / 2
    if len(weights) > 0:
        t.iloc[0] = weights.iloc[0].abs().sum() / 2
    return t


def factor_report(
    signal: pd.DataFrame,
    forward_returns: pd.DataFrame,
    n_quantiles: int = 5,
) -> dict:
    """One-shot factor evaluation summary."""
    ic = information_coefficient(signal, forward_returns)
    qret = quantile_returns(signal, forward_returns, n_quantiles)

    long_short = (
        (qret[n_quantiles] - qret[1]).mean() if n_quantiles in qret.columns else np.nan
    )

    return {
        "ic": ic,
        "ic_mean": float(ic.mean()),
        "ic_std": float(ic.std()),
        "ic_ir": information_ratio(ic),
        "ic_hit_rate": float((ic > 0).mean()),
        "quantile_returns": qret,
        "long_short_mean_return": float(long_short) if pd.notna(long_short) else float("nan"),
    }
