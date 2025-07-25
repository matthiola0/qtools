from dataclasses import dataclass

import pandas as pd


@dataclass
class CostModel:
    """Transaction cost model (bps = basis points; 1 bp = 0.01%).

    commission + slippage apply to all trades (|Δw|).
    tax applies only to sell legs (TW securities transaction tax convention).
    """

    commission_bps: float = 0.0
    slippage_bps: float = 0.0
    tax_bps: float = 0.0

    @property
    def total_bps(self) -> float:
        return self.commission_bps + self.slippage_bps + self.tax_bps

    def apply(self, weights: pd.DataFrame) -> pd.Series:
        """Cost drag per date from weight changes.

        Returns a Series aligned to `weights.index`, values in return units
        (e.g. 0.001 = 10 bps drag).
        """
        diff = weights.diff()
        if len(diff) > 0:
            diff.iloc[0] = weights.iloc[0]

        buys = diff.clip(lower=0).sum(axis=1)
        sells = (-diff).clip(lower=0).sum(axis=1)

        bidir = (self.commission_bps + self.slippage_bps) / 1e4
        sell_tax = self.tax_bps / 1e4

        return (buys + sells) * bidir + sells * sell_tax


# Approximate round-trip costs (one-way bps; round-trip ≈ 2x on commission+slippage + tax).
TW_EQUITY = CostModel(commission_bps=14.25, slippage_bps=5, tax_bps=30)
US_EQUITY = CostModel(commission_bps=1, slippage_bps=4)
CRYPTO = CostModel(commission_bps=10, slippage_bps=10)
