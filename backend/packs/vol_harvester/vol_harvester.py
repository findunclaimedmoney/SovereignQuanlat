"""
Sovereign Quant Strategy Pack — VOLATILITY HARVESTER
Drop-in module for the Sovereign Quant workstation (v1.3+).

Usage:
    from vol_harvester import VolatilityHarvester
    strat = VolatilityHarvester(atr_window=14, target_vol=0.12)
    signals = strat.generate(prices_df)  # prices_df: DataFrame with 'close' and 'high'/'low'
"""

import numpy as np
import pandas as pd


class VolatilityHarvester:
    """Volatility-targeted momentum with regime classification.

    Sizes positions inversely to realized volatility and only trades
    when the volatility regime is 'harvestable' (rising vol from a
    compressed base, not a spike crash).
    """

    def __init__(self, atr_window: int = 14, target_vol: float = 0.12,
                 vol_lookback: int = 60, momentum_lookback: int = 20):
        self.atr_window = atr_window
        self.target_vol = target_vol
        self.vol_lookback = vol_lookback
        self.momentum_lookback = momentum_lookback

    def _atr(self, df: pd.DataFrame) -> pd.Series:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.ewm(span=self.atr_window, adjust=False).mean()

    def realized_vol(self, close: pd.Series) -> pd.Series:
        returns = close.pct_change()
        return returns.rolling(self.vol_lookback).std() * np.sqrt(252)

    def vol_regime(self, close: pd.Series) -> pd.Series:
        vol = self.realized_vol(close)
        vol_ma = vol.rolling(self.vol_lookback).mean()
        regime = pd.Series("neutral", index=close.index)
        regime[(vol > vol_ma) & (vol < vol_ma * 1.8)] = "harvestable"
        regime[vol >= vol_ma * 1.8] = "spike"
        regime[vol < vol_ma * 0.7] = "compressed"
        return regime

    def position_size(self, close: pd.Series, capital: float) -> pd.Series:
        vol = self.realized_vol(close).replace(0, np.nan)
        weight = (self.target_vol / vol).clip(0, 2.0)
        return (weight * capital).fillna(0)

    def generate(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["atr"] = self._atr(df)
        out["realized_vol"] = self.realized_vol(df["close"])
        out["regime"] = self.vol_regime(df["close"])
        out["momentum"] = df["close"].pct_change(self.momentum_lookback)
        long_sig = (out["regime"] == "harvestable") & (out["momentum"] > 0)
        short_sig = (out["regime"] == "harvestable") & (out["momentum"] < 0)
        out["signal"] = 0
        out.loc[long_sig, "signal"] = 1
        out.loc[short_sig, "signal"] = -1
        return out
