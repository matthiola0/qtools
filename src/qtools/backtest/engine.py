from dataclasses import dataclass

import pandas as pd

from qtools.backtest.costs import CostModel


@dataclass
class BacktestResult:
    returns: pd.Series           # daily strategy returns, net of costs
    gross_returns: pd.Series     # daily returns before costs
    weights: pd.DataFrame        # daily held weights (after forward-fill)
    turnover: pd.Series          # per-day |Δweights| sum (one-way per leg)
    costs: pd.Series             # per-day cost drag


class BacktestEngine:
    """Vectorized long-only or long-short backtest.

    Assumes weights are applied at close of day t and earn t+1's return
    (standard lagged convention — no look-ahead).
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        cost_model: CostModel | None = None,
    ) -> None:
        if not {"date", "symbol", "close"}.issubset(prices.columns):
            raise ValueError("prices must have columns: date, symbol, close")

        self._close = (
            prices.pivot(index="date", columns="symbol", values="close")
            .sort_index()
        )
        self._returns = self._close.pct_change()
        self.cost_model = cost_model or CostModel()

    def run(self, weights: pd.DataFrame) -> BacktestResult:
        """Run the backtest.

        weights: date × symbol DataFrame. Can be sparse (only at rebalance
        dates) — will be forward-filled to daily. Missing symbols treated
        as zero weight.
        """
        aligned = (
            weights.reindex(columns=self._close.columns, fill_value=0.0)
            .reindex(self._close.index)
            .ffill()
            .fillna(0.0)
        )

        # Lag weights by 1 day: today's position comes from yesterday's close
        positions = aligned.shift(1).fillna(0.0)
        gross_daily = (positions * self._returns).sum(axis=1)

        costs = self.cost_model.apply(aligned)

        turnover = aligned.diff().abs().sum(axis=1)
        if len(aligned) > 0:
            turnover.iloc[0] = aligned.iloc[0].abs().sum()

        net_daily = gross_daily.sub(costs, fill_value=0.0)

        return BacktestResult(
            returns=net_daily.fillna(0.0),
            gross_returns=gross_daily.fillna(0.0),
            weights=aligned,
            turnover=turnover,
            costs=costs,
        )
