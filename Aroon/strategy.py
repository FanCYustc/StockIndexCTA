import sys
sys.path.append(r"E:\StockIndexCTA")

from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd

class AroonStrategy(BaseStrategy):
    # 策略配置
    symbol = "IM"
    
    # Aroon 参数
    NDAY = 25
    UPBAND = 70
    LOWBAND = 30
    
    name = f'{symbol}_Aroon_{NDAY}'
    min_date = 20160101

    def getOrgData(self):
        # 获取原始数据
        path = fr"E:\StockIndexCTA\Data\{self.symbol}_{self.td}.csv"
        self.raw_data = pd.read_csv(path)

    def prepare_data(self):
        # 准备数据
        arr = self.raw_data.values
        
        # 提取价格数据
        self.openPrice = arr[:, 1]
        self.closePrice = arr[:, 2]
        self.highPrice = arr[:, 3]
        self.lowPrice = arr[:, 4]
        
        # --- 指标计算 ---
        high_series = pd.Series(self.highPrice)
        low_series = pd.Series(self.lowPrice)
        n = self.NDAY
        
        # Aroon Up: (N - HHVBARS(High, N)) / N * 100
        rolling_argmax = high_series.rolling(window=n).apply(np.argmax, raw=True)
        self.aroon_up = ((rolling_argmax + 1) / n * 100).values
        
        # Aroon Down: (N - LLVBARS(Low, N)) / N * 100
        rolling_argmin = low_series.rolling(window=n).apply(np.argmin, raw=True)
        self.aroon_down = ((rolling_argmin + 1) / n * 100).values

    def GetSig(self, i):
        # 暖身期检查
        if i < self.NDAY:
            self.prePosition = self.position
            self.position = 0
            return

        # 获取当前指标值
        up = self.aroon_up[i]
        down = self.aroon_down[i]
        
        # 信号逻辑:
        # 做多: UP > upband 且 DOWN < lowband
        # 做空: DOWN > upband 且 UP < lowband
        # 状态: 持有直到反向信号 (Flip-flop)
        
        sig = self.position # 默认维持原有仓位
        
        if up > self.UPBAND and down < self.LOWBAND:
            sig = 1
        elif down > self.UPBAND and up < self.LOWBAND:
            sig = -1
            
        self.prePosition = self.position
        self.position = sig

if __name__ == "__main__":
    run_backtest(AroonStrategy)