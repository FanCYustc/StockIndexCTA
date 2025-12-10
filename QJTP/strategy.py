#QJTP

import sys
sys.path.append(r"E:\StockIndexCTA")
from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

class MinStrategy(BaseStrategy):

    symbol = "IM"
    name = f'{symbol}_QJTP'
    min_date = 20170101

    def getOrgData(self):
        path = fr"E:\StockIndexCTA\Data\{self.symbol}_{self.td}.csv"
        self.raw_data = pd.read_csv(path)

    def prepare_data(self):
        arr = self.raw_data.values

        self.x_series = np.nanmean(arr[:, [1, 2, 3, 4]], axis=1)
        self.openPrice = arr[:, 1]
        self.closePrice = arr[:, 2]


    def GetSig(self, i):
        if i < 6:
            self.prePosition = self.position
            self.position = 0
            return

        data = self.x_series[:i+1]
        nowPoint = data[-1]
        lastLine = data[-6:-1]
        x = np.linspace(1, len(lastLine), len(lastLine))

        clf = LinearRegression()
        clf.fit(x.reshape(-1, 1), lastLine / np.nanmean(lastLine))
        R2 = clf.score(x.reshape(-1, 1), lastLine / np.nanmean(lastLine))
        coef = clf.coef_[0]
        cond = nowPoint / lastLine[-1] - 1

        if coef >= 0.0005 and R2 > 0.5 and cond > 0.001:
            sig = -1 * R2
        elif coef <= -0.0005 and R2 > 0.5 and cond <= -0.001:
            sig = 1 * R2
        else:
            sig = 0

        self.prePosition = self.position
        self.position = sig

if __name__ == "__main__":
    df = run_backtest(MinStrategy)
