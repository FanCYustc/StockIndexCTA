import sys
sys.path.append(r"E:\StockIndexCTA")

from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd

class BollingerStrategy(BaseStrategy):
    # 策略配置
    symbol = "IM"

    # Bollinger 参数
    MDAY = 15
    NDAY = 21
    NSTD = 2.125
    
    name = f'{symbol}_Bollinger_{MDAY}_{NDAY}_{NSTD}'
    min_date = 20160101

    def getOrgData(self):
        path = fr"E:\StockIndexCTA\Data\{self.symbol}_{self.td}.csv"
        self.raw_data = pd.read_csv(path)

    def prepare_data(self):
        arr = self.raw_data.values

        # 1:开盘价, 2:收盘价, 3:最高价, 4:最低价
        self.openPrice = arr[:, 1]
        self.highPrice = arr[:, 3]
        self.lowPrice = arr[:, 4]
        self.closePrice = arr[:, 2] 

        # --- 指标计算 ---
        close_s = pd.Series(self.closePrice)

        # 1. 上轨 (UPP): MA(MDAY) + NSTD * STD(MDAY)
        ma_m = close_s.rolling(window=self.MDAY).mean()
        std_m = close_s.rolling(window=self.MDAY).std()
        self.upp = (ma_m + self.NSTD * std_m).values

        # 2. 下轨 (DOWNP): MA(NDAY) - NSTD * STD(NDAY)
        ma_n = close_s.rolling(window=self.NDAY).mean()
        std_n = close_s.rolling(window=self.NDAY).std()
        self.downp = (ma_n - self.NSTD * std_n).values

    def GetSig(self, i):
        # 暖身期检查
        warmup = max(self.MDAY, self.NDAY)
        if i < warmup:
            self.prePosition = self.position
            self.position = 0
            return

        # 获取当前收盘价和轨道值
        close = self.closePrice[i]
        upp = self.upp[i]
        downp = self.downp[i]

        # 信号逻辑:
        # 买入: Close > UPP
        # 卖出: Close < DOWNP
        # 状态: 维持原有仓位
        
        sig = self.position # 默认维持原有仓位

        if close > upp:
            sig = -1
        elif close < downp:
            sig = 1

        self.prePosition = self.position
        self.position = sig

if __name__ == "__main__":
    run_backtest(BollingerStrategy)
