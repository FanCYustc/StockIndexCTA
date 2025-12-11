#QJTP

import sys
sys.path.append(r"E:\StockIndexCTA")
from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

class MinStrategy(BaseStrategy):
    # 策略配置
    symbol = "IM"
    name = f'{symbol}_QJTP'
    min_date = 20170101

    def getOrgData(self):
        # 获取原始数据
        path = fr"E:\StockIndexCTA\Data\{self.symbol}_{self.td}.csv"
        self.raw_data = pd.read_csv(path)

    def prepare_data(self):
        # 准备数据
        arr = self.raw_data.values

        # 计算OHLC的平均值作为核心价格序列
        self.x_series = np.nanmean(arr[:, [1, 2, 3, 4]], axis=1)
        
        # 提取基础价格数据
        self.openPrice = arr[:, 1]
        self.closePrice = arr[:, 2]


    def GetSig(self, i):
        if i < 6:
            self.prePosition = self.position
            self.position = 0
            return

        # 获取数据窗口
        data = self.x_series[:i+1]
        nowPoint = data[-1]         # 当前点
        lastLine = data[-6:-1]      # 过去5个点
        
        x = np.linspace(1, len(lastLine), len(lastLine))

        # 线性回归拟合
        clf = LinearRegression()
        clf.fit(x.reshape(-1, 1), lastLine / np.nanmean(lastLine))
        
        # 计算统计量
        R2 = clf.score(x.reshape(-1, 1), lastLine / np.nanmean(lastLine)) # 拟合优度
        coef = clf.coef_[0] # 斜率
        
        # 当前价格相对于过去5分钟末端的偏离度
        cond = nowPoint / lastLine[-1] - 1

        # 交易逻辑: 均值回归 (Reversal Strategy)
        # 1. 如果过去5分钟呈现明显上涨趋势 (coef > 0.0005) 且拟合度高 (R2 > 0.5)
        #    并且当前价格继续向上偏离 (cond > 0.001) -> 认为超买，反向做空
        if coef >= 0.0005 and R2 > 0.5 and cond > 0.001:
            sig = -1 * R2 # 信号强度由R2决定
            
        # 2. 如果过去5分钟呈现明显下跌趋势 (coef < -0.0005) 且拟合度高 (R2 > 0.5)
        #    并且当前价格继续向下偏离 (cond < -0.001) -> 认为超卖，反向做多
        elif coef <= -0.0005 and R2 > 0.5 and cond <= -0.001:
            sig = 1 * R2
            
        # 3. 无明显机会，平仓
        else:
            sig = 0

        self.prePosition = self.position
        self.position = sig

if __name__ == "__main__":
    df = run_backtest(MinStrategy)
