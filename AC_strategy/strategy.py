import sys
sys.path.append(r"E:\StockIndexCTA")

from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd

class ACStrategy(BaseStrategy):

    symbol = "IM"
    name = f'{symbol}_AC'
    min_date = 20220101

    def getOrgData(self):
        path = fr"E:\StockIndexCTA\Data\{self.symbol}_{self.td}.csv"
        self.raw_data = pd.read_csv(path)

    def prepare_data(self):
        arr = self.raw_data.values

        self.openPrice = arr[:, 1]
        self.closePrice = arr[:, 2]

        close = self.closePrice
        n1 = getattr(self, 'n1', 5)  # 超参数
        n2 = getattr(self, 'n2', 10)
        
        a = np.full_like(close, np.nan)
        c = np.full_like(close, np.nan)
        
        a[n1:] = close[n1:] - close[:-n1]
        c[n2:] = close[n2:] - close[:-n2]
        
        self.ac_series = a - c

    def GetSig(self, i):
        if i < 20:
            self.prePosition = self.position
            self.position = 0
            return

        data = self.ac_series[:i+1]
        val = data[-1]

        p1 = data[-2]
        p2 = data[-3]
        p3 = data[-4]

        sig = self.position

        # 买入条件（任一成立即开多）：
        # 1) 自下而上穿越零轴，且连续两个交易日上升 (p1 <=0 且 val>0 且 val>p1>p2)
        # 2) AC 在零轴之上，且连续两个交易日上升 (val>0 且 val>p1>p2)
        # 3) AC 在零轴之下，且连续三个交易日上升 (val<0 且 val>p1>p2>p3)
        if (p1 <= 0 and val > 0 and val > p1 and p1 > p2) or \
           (val > 0 and val > p1 and p1 > p2) or \
           (val < 0 and val > p1 and p1 > p2 and p2 > p3):
            sig = 1

        # 卖出条件（任一成立即开空）：
        # 1) 自上而下穿越零轴，且连续两个交易日下跌 (p1 >=0 且 val<0 且 val<p1<p2)
        # 2) AC 在零轴之上，且连续三个交易日下跌 (val>0 且 val<p1<p1<p2<p3 -> 实现为 val>0 且 val<p1<p1<p2<p3?)
        #    正确逻辑是 val>0 且 val<p1 且 p1<p2 且 p2<p3
        # 3) AC 在零轴之下，且连续两个交易日下跌 (val<0 且 val<p1<p2)
        if (p1 >= 0 and val < 0 and val < p1 and p1 < p2) or \
           (val > 0 and val < p1 and p1 < p2 and p2 < p3) or \
           (val < 0 and val < p1 and p1 < p2):
            sig = -1

        self.prePosition = self.position
        self.position = sig

if __name__ == "__main__":
    run_backtest(ACStrategy)
