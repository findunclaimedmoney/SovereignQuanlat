"""
Sovereign Quant Strategy Pack — MEAN REVERSION PRO
Drop-in module for the Sovereign Quant workstation (v1.3+).

Usage:
    from mean_reversion_pro import MeanReversionPro
    strat = MeanReversionPro(bb_window=20, bb_std=2.0)
    signals = strat.generate(prices_df)  # DataFrame with a 'close' column
"""

import numpy as np
import pandas as pd


class MeanReversionPro:
    """Bollinger z-score reversion with RSI(2) confirmation, a
    200-SMA regime gate, and an Ornstein-Uhlenbeck half-life filter
    so you only fade moves in genuinely mean-reverting regimes.
    """

    def __init__(self, bb_window: int = 20, bb_std: float = 2.0,
                 regime_window: int = 200, halflife_max: float = 30.0):
        self.bb_window = bb_window
        self.bb_std = bb_std
        self.regime_window = regime_window
        self.halflife_max = halflife_max

    def zscore(self, close: pd.Series) -> pd.Series:
        ma = close.rolling(self.bb_window).mean()
        sd = close.rolling(self.bb_window).std()
        return (close - ma) / sd.replace(0, np.nan)

    def rsi2(self, close: pd.Series) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(2).mean()
        loss = (-delta.clip(upper=0)).rolling(2).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - 100 / (1 + rs)

    def half_life(self, close: pd.Series) -> float:
        lag = close.shift(1).dropna()
        delta = close.diff().dropna()
        if len(lag) < 30:
            return np.inf
        slope = np.polyfit(lag.values, delta.values, 1)[0]
        if slope >= 0:
            return np.inf
        return -np.log(2) / slope

    def generate(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["z"] = self.zscore(df["close"])
        out["rsi2"] = self.rsi2(df["close"])
        sma200 = df["close"].rolling(self.regime_window).mean()
        out["regime_ok"] = df["close"] > sma200  # only long-fade above the 200
        hl = self.half_life(df["close"].tail(120))
        out["half_life_ok"] = hl <= self.halflife_max
        long_sig = (out["z"] < -self.bb_std) & (out["rsi2"] < 10) & out["regime_ok"] & out["half_life_ok"]
        exit_sig = out["z"] > 0
        out["signal"] = 0
        out.loc[long_sig, "signal"] = 1
        out.loc[exit_sig, "signal"] = -1  # exit marker
        out.attrs["half_life"] = hl
        return out
