import sys
sys.path.append(r"E:\StockIndexCTA")

from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd

class AlligatorStrategy(BaseStrategy):
    # Strategy settings
    symbol = "IF"
    
    # Default parameters from PDF (IV. Default Parameter Results)
    FAST = 20
    MID = 60
    SLOW = 120
    
    name = f'{symbol}_Alligator_{FAST}_{MID}_{SLOW}'
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
        # MP := (HIGH + LOW) / 2
        mp = (pd.Series(self.highPrice) + pd.Series(self.lowPrice)) / 2
        
        # MEMA (Modified EMA / Smoothed Moving Average)
        # Standard Alligator uses SMMA which is equivalent to EMA with alpha = 1/N
        
        # LIPS: MEMA(MP, FAST)
        self.lips = mp.ewm(alpha=1/self.FAST, adjust=False).mean().values
        
        # TEETH: MEMA(MP, MID)
        self.teeth = mp.ewm(alpha=1/self.MID, adjust=False).mean().values
        
        # JAW: MEMA(MP, SLOW)
        self.jaw = mp.ewm(alpha=1/self.SLOW, adjust=False).mean().values
        
        self.close_arr = self.closePrice

    def GetSig(self, i):
        # Warmup check
        if i < self.SLOW:
            self.prePosition = self.position
            self.position = 0
            return

        # Current values
        price = self.close_arr[i]
        l = self.lips[i]
        t = self.teeth[i]
        j = self.jaw[i]
        
   
        # signal logic
        
        if price > l and l > t and t > j:
            sig = 1
        elif price < l and l < t and t < j:
            sig = -1
        else:
            sig = 0
        
        self.prePosition = self.position
        self.position = sig

if __name__ == "__main__":
    run_backtest(AlligatorStrategy)
