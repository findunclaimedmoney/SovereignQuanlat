"""
Sovereign Quant Strategy Pack — EXECUTION SUITE
Drop-in module for the Sovereign Quant workstation (v1.3+).

Usage:
    from execution_suite import TWAPSlicer, SlippageEstimator
    slices = TWAPSlicer(total_qty=10000, intervals=20).schedule()
"""

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd


@dataclass
class TWAPSlicer:
    """Splits a parent order into equal child orders over N intervals,
    front-loading slightly when urgency is set above 1.0."""

    total_qty: float
    intervals: int
    urgency: float = 1.0

    def schedule(self) -> List[float]:
        if self.intervals <= 0:
            return [self.total_qty]
        weights = np.linspace(self.urgency, 1.0, self.intervals)
        weights = weights / weights.sum()
        return [round(self.total_qty * w, 4) for w in weights]


class ParticipationLimiter:
    """Caps child order size at a fraction of observed interval volume."""

    def __init__(self, max_participation: float = 0.10):
        self.max_participation = max_participation

    def cap(self, desired_qty: float, interval_volume: float) -> float:
        return min(desired_qty, interval_volume * self.max_participation)


class SlippageEstimator:
    """Square-root market-impact slippage model:
    slippage_bps = spread/2 + eta * sigma * sqrt(qty / adv)."""

    def __init__(self, eta: float = 0.7):
        self.eta = eta

    def estimate_bps(self, qty: float, adv: float, sigma: float,
                     spread_bps: float = 2.0) -> float:
        if adv <= 0:
            return np.inf
        impact = self.eta * sigma * np.sqrt(qty / adv) * 10000
        return spread_bps / 2 + impact

    def cost_curve(self, qty_grid: List[float], adv: float, sigma: float) -> pd.Series:
        return pd.Series(
            [self.estimate_bps(q, adv, sigma) for q in qty_grid],
            index=qty_grid, name="slippage_bps",
        )
