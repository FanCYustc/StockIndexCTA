import sys
sys.path.append(r"E:\StockIndexCTA")

from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd

class ADXStrategy(BaseStrategy):
    # Strategy settings
    symbol = "IF"
    N = 14
    ADX_THRESHOLD = 30
    name = f'{symbol}_ADX_{N}'
    min_date = 20220701

    def getOrgData(self):
        path = fr"E:\StockIndexCTA\Data\{self.symbol}_{self.td}.csv"
        self.raw_data = pd.read_csv(path)

    def prepare_data(self):
        arr = self.raw_data.values
        
        # Required by BaseStrategy
        self.openPrice = arr[:, 1]
        self.closePrice = arr[:, 2]
        self.highPrice = arr[:, 3]
        self.lowPrice = arr[:, 4]
        
        # --- Indicator Calculation ---
        
        # 1. TR (True Range)
        prev_close = pd.Series(self.closePrice).shift(1)
        tr1 = pd.Series(self.highPrice) - pd.Series(self.lowPrice)
        tr2 = (pd.Series(self.highPrice) - prev_close).abs()
        tr3 = (prev_close - pd.Series(self.lowPrice)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 2. MTR = EMA(TR, n)
        mtr = tr.ewm(span=self.N, adjust=False).mean()
        
        # 3. DM
        hd = pd.Series(self.highPrice) - pd.Series(self.highPrice).shift(1)
        ld = pd.Series(self.lowPrice).shift(1) - pd.Series(self.lowPrice)
        
        plus_dm = np.where((hd > 0) & (hd > ld), hd, 0.0)
        minus_dm = np.where((ld > 0) & (ld > hd), ld, 0.0)
        
        plus_dm = pd.Series(plus_dm, index=pd.Series(self.highPrice).index)
        minus_dm = pd.Series(minus_dm, index=pd.Series(self.lowPrice).index)
        
        dmp = plus_dm.ewm(span=self.N, adjust=False).mean()
        dmm = minus_dm.ewm(span=self.N, adjust=False).mean()
        
        # 4. DI
        pdi = (dmp / mtr) * 100
        mdi = (dmm / mtr) * 100
        
        # 5. DX
        denom = pdi + mdi
        dx = (abs(pdi - mdi) / denom) * 100
        dx = dx.fillna(0)
        
        # 6. ADX = EMA(DX, n)
        adx = dx.ewm(span=self.N, adjust=False).mean()
        
        # 7. MA (Simple Moving Average)
        ma = pd.Series(self.closePrice).rolling(window=60).mean()
        
        # Store arrays for GetSig access
        self.adx_arr = adx.values
        self.ma_arr = ma.values
        self.close_arr = self.closePrice

    def GetSig(self, i):
        # Warmup check
        if i < self.N:
            self.prePosition = self.position
            return

        # Current values
        adx_val = self.adx_arr[i]
        
        curr_close = self.close_arr[i]
        curr_ma = self.ma_arr[i]

        # Logic
        sig = self.position 
        
        # 1. Band Definitions (1 +/- 0.05%)
        # 均线上下轨 (0.05% 缓冲区)
        upper_band = curr_ma * (1 + 0.0005)
        lower_band = curr_ma * (1 - 0.0005)
        
        # 2. Trend Filters
        # ADX强弱判断
        is_trend_strong = (adx_val > self.ADX_THRESHOLD)

        # 3. Trading Logic
        if sig == 0:
            # Entry Logic (State-Based)
            # 只要价格在通道外且趋势强，就入场
            # Improved: Checks "Current State" rather than just "Crossover Moment"
            if curr_close > upper_band and is_trend_strong:
                sig = 1
            elif curr_close < lower_band and is_trend_strong:
                sig = -1
                
        elif sig == 1:
            # Long Exit / Reverse
            # 跌破下轨时进行判断
            if curr_close < lower_band:
                if is_trend_strong:
                    sig = -1 # Reverse to Short
                else:
                    sig = 0  # Close Position
                    
        elif sig == -1:
            # Short Exit / Reverse
            # 突破上轨时进行判断
            if curr_close > upper_band:
                if is_trend_strong:
                    sig = 1  # Reverse to Long
                else:
                    sig = 0  # Close Position
        
        self.prePosition = self.position
        self.position = sig

if __name__ == "__main__":
    run_backtest(ADXStrategy)