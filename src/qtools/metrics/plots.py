import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes


def plot_cumulative_returns(returns: pd.Series, ax: Axes | None = None) -> Axes:
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 5))
    (1 + returns).cumprod().plot(ax=ax)
    ax.set_title("Cumulative Returns")
    ax.set_ylabel("Growth of $1")
    ax.grid(alpha=0.3)
    return ax


def plot_drawdown(returns: pd.Series, ax: Axes | None = None) -> Axes:
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 3))
    cum = (1 + returns).cumprod()
    dd = (cum - cum.cummax()) / cum.cummax()
    ax.fill_between(dd.index, dd.values, 0, color="crimson", alpha=0.5)
    ax.plot(dd.index, dd.values, color="crimson", linewidth=0.8)
    ax.set_title("Drawdown")
    ax.set_ylabel("Drawdown")
    ax.grid(alpha=0.3)
    return ax


def plot_quantile_returns(quantile_rets: pd.DataFrame, ax: Axes | None = None) -> Axes:
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 5))
    means = quantile_rets.mean()
    colors = ["crimson" if q == means.idxmin() else
              "seagreen" if q == means.idxmax() else
              "steelblue" for q in means.index]
    means.plot(kind="bar", ax=ax, color=colors)
    ax.set_title("Mean Forward Return by Quantile")
    ax.set_xlabel("Quantile")
    ax.set_ylabel("Mean Return")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.grid(alpha=0.3, axis="y")
    return ax


def plot_ic_timeseries(ic: pd.Series, ax: Axes | None = None) -> Axes:
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))
    ic.plot(ax=ax, alpha=0.3, label="IC", color="steelblue")
    window = max(12, len(ic) // 20)
    ic.rolling(window).mean().plot(ax=ax, label=f"{window}-period MA", color="darkblue")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.axhline(ic.mean(), color="red", linestyle="--", alpha=0.5,
               label=f"mean = {ic.mean():.3f}")
    ax.set_title("Information Coefficient Over Time")
    ax.set_ylabel("IC")
    ax.grid(alpha=0.3)
    ax.legend()
    return ax
