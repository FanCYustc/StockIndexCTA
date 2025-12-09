import sys
sys.path.append(r"E:\StockIndexCTA")

from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd

class ACStrategy(BaseStrategy):

    symbol = "IM"
    n1 = 35
    n2 = 135
    name = f'{symbol}_AC_{n1}_{n2}'
    min_date = 20220101

    def getOrgData(self):
        path = fr"E:\StockIndexCTA\Data\{self.symbol}_{self.td}.csv"
        self.raw_data = pd.read_csv(path)

    def prepare_data(self):
        arr = self.raw_data.values

        # GEMINI.md: 1:open, 2:close, 3:high, 4:low
        self.openPrice = arr[:, 1]
        self.highPrice = arr[:, 3]
        self.lowPrice = arr[:, 4]
        self.closePrice = arr[:, 2] 

        # --- Vectorized Indicator Calculation ---
        
        # 1. Median Price
        median_price = (self.highPrice + self.lowPrice) / 2.0
        mp_series = pd.Series(median_price)

        # 2. AO (Awesome Oscillator)
        n1 = self.n1
        n2 = self.n2
        
        sma_fast = mp_series.rolling(window=n1).mean()
        sma_slow = mp_series.rolling(window=n2).mean()
        ao = sma_fast - sma_slow

        # 3. AC (Accelerator Oscillator)
        sma_ao = ao.rolling(window=n1).mean()
        ac_series = ao - sma_ao
        self.ac_series = ac_series.values # numpy array
        
        # 4. Trend Filter (MA60)
        ma_trend = pd.Series(self.closePrice).rolling(window=60).mean()
        self.ma_trend = ma_trend.values

        # --- Vectorized Logic Preparation ---
        
        # Pre-calculate shifted AC for comparison
        ac = self.ac_series
        p1 = np.roll(ac, 1) # p1[i] = ac[i-1]
        p2 = np.roll(ac, 2)
        p3 = np.roll(ac, 3)
        
        # Handle NaN/Boundary issues
        p1[:1] = np.nan; p2[:2] = np.nan; p3[:3] = np.nan
        
        # 1. Condition Helpers (Boolean Arrays)
        is_rising_1 = (ac > p1)
        is_rising_2 = (p1 > p2)
        is_rising_3 = (p2 > p3)
        
        is_falling_1 = (ac < p1)
        is_falling_2 = (p1 < p2)
        is_falling_3 = (p2 < p3)
        
        # 2. Entry Conditions (Vectorized)
        # Buy: (Positive Zone & 2 Rising) OR (Negative Zone & 3 Rising)
        buy_cond_pos = (ac > 0) & is_rising_1 & is_rising_2
        buy_cond_neg = (ac < 0) & is_rising_1 & is_rising_2 & is_rising_3
        raw_buy_signal = (buy_cond_pos | buy_cond_neg)
        
        # Sell: (Negative Zone & 2 Falling) OR (Positive Zone & 3 Falling)
        sell_cond_neg = (ac < 0) & is_falling_1 & is_falling_2
        sell_cond_pos = (ac > 0) & is_falling_1 & is_falling_2 & is_falling_3
        raw_sell_signal = (sell_cond_neg | sell_cond_pos)
        
        # Trend Conditions
        trend_up = (self.closePrice > self.ma_trend)
        trend_down = (self.closePrice < self.ma_trend)
        
        # --- State Machine Simulation (Fast Loop) ---
        # Initialize position array
        pos_arr = np.zeros(len(ac))
        current_pos = 0.0
        
        # We start from max(n2, 60) to avoid NaNs
        start_idx = max(n2, 60)
        
        # Pre-extract arrays for speed (avoiding self lookups in loop)
        ac_vals = ac
        p1_vals = p1
        buy_sigs = raw_buy_signal.astype(bool)
        sell_sigs = raw_sell_signal.astype(bool)
        t_up = trend_up.astype(bool)
        t_down = trend_down.astype(bool)
        
        for i in range(start_idx, len(ac)):
            
            # 1. Forced Exit Logic
            if current_pos == 1 and ac_vals[i] < p1_vals[i]:
                current_pos = 0
            elif current_pos == -1 and ac_vals[i] > p1_vals[i]:
                current_pos = 0
                
            # 2. Entry Logic
            # Buy if signal + trend up
            if buy_sigs[i] and t_up[i]:
                current_pos = 1
            # Sell if signal + trend down
            elif sell_sigs[i] and t_down[i]:
                current_pos = -1
            
            pos_arr[i] = current_pos
            
        self.target_positions = pos_arr

    def GetSig(self, i):
        # Extremely fast lookup
        if i < 60:
            self.prePosition = self.position
            self.position = 0
            return

        self.prePosition = self.position
        self.position = self.target_positions[i]

if __name__ == "__main__":
    run_backtest(ACStrategy)
