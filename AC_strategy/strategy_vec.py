
import sys
import os

# Add project root to sys.path to ensure we can import CTA_BT
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd

class ACStrategyVec(BaseStrategy):
    """
    Vectorized version of ACStrategy for high performance optimization.
    """
    symbol = "IF"
    n1 = 5
    n2 = 34
    name = f'{symbol}_AC_{n1}_{n2}'
    min_date = 20170101

    def getOrgData(self):
        # Using relative path assuming execution from root or handling paths correctly
        # The base class or main script usually handles the path, but here we replicate logic
        path = os.path.join(project_root, "Data", f"{self.symbol}_{self.td}.csv")
        self.raw_data = pd.read_csv(path)

    def prepare_data(self):
        arr = self.raw_data.values

        self.openPrice = arr[:, 1]
        self.closePrice = arr[:, 2]

        close = pd.Series(self.closePrice)

        
        # Vectorized AC calculation
        # AO = SMA(Median Price, 5) - SMA(Median Price, 34)
        # But original strategy uses close price diffs?
        # Original: a[n1:] = close[n1:] - close[:-n1] -> Momentum? 
        # a is close - close_lag_n1
        # c is close - close_lag_n2
        # ac = a - c
        # This is effectively (Close - Close_n1) - (Close - Close_n2) = Close_n2 - Close_n1
        
        # Let's stick strictly to the original logic:
        # a[i] = close[i] - close[i-n1]
        # c[i] = close[i] - close[i-n2]

        n1 = self.n1
        n2 = self.n2
        
        # Using pandas shift for convenience
        a = close - close.shift(n1)
        c = close - close.shift(n2)
        ac_series = a - c
        self.ac_series = ac_series.values # Keep as numpy array for later if needed, or series
        
        # Vectorized Signal Logic
        # We need p1 (lag 1), p2 (lag 2), p3 (lag 3) of AC
        
        ac = ac_series
        p1 = ac.shift(1)
        p2 = ac.shift(2)
        p3 = ac.shift(3)
        
        # Buy Conditions
        # 1) p1 <= 0 and val > 0 and val > p1 and p1 > p2
        cond_buy_1 = (p1 <= 0) & (ac > 0) & (ac > p1) & (p1 > p2)
        
        # 2) val > 0 and val > p1 and p1 > p2
        cond_buy_2 = (ac > 0) & (ac > p1) & (p1 > p2)
        
        # 3) val < 0 and val > p1 and p1 > p2 and p2 > p3
        cond_buy_3 = (ac < 0) & (ac > p1) & (p1 > p2) & (p2 > p3)
        
        buy_signal = cond_buy_1 | cond_buy_2 | cond_buy_3
        
        # Sell Conditions
        # 1) p1 >= 0 and val < 0 and val < p1 and p1 < p2
        cond_sell_1 = (p1 >= 0) & (ac < 0) & (ac < p1) & (p1 < p2)
        
        # 2) val > 0 and val < p1 and p1 < p2 and p2 < p3 (Fixed logic based on original code comments/impl)
        # Original code: val > 0 and val < p1 and p1 < p2 and p2 < p3
        cond_sell_2 = (ac > 0) & (ac < p1) & (p1 < p2) & (p2 < p3)
        
        # 3) val < 0 and val < p1 and p1 < p2
        cond_sell_3 = (ac < 0) & (ac < p1) & (p1 < p2)
        
        sell_signal = cond_sell_1 | cond_sell_2 | cond_sell_3
        
        # Generate Target Positions
        # Initialize with NaNs to use ffill for "hold" logic
        # However, we start with 0 position.
        
        # Create a series to hold signals: 1 for Buy, -1 for Sell, NaN for Hold
        signals = pd.Series(np.nan, index=ac.index)
        signals[buy_signal] = 1
        signals[sell_signal] = -1
        
        # Forward fill to propagate position
        # Note: Original strategy starts checking at i=20 and sets position=0 for i<20
        # We should respect the start index
        
        signals = signals.ffill().fillna(0)
        
        # Enforce i < 20 is 0
        signals.iloc[:20] = 0
        
        self.target_positions = signals.values

    def GetSig(self, i):
        # In vectorized strategy, GetSig just retrieves the pre-calculated position
        # The base strategy loop calls GetSig(i) then calculates PNL based on self.position
        
        # BaseStrategy updates PNL based on:
        # ret = self.prePosition * (nowClose / nowOpen - 1)
        # So we need to set self.position for the CURRENT minute i.
        
        if i < 20:
            self.prePosition = self.position
            self.position = 0
            return

        self.prePosition = self.position
        self.position = self.target_positions[i]

if __name__ == "__main__":
    run_backtest(ACStrategyVec)
