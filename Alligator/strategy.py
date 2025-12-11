import sys
sys.path.append(r"E:\StockIndexCTA")

from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd

class AlligatorStrategy(BaseStrategy):
    # 策略配置
    symbol = "IM"
    
    # 鳄鱼线参数
    FAST = 20
    MID = 60
    SLOW = 120
    
    name = f'{symbol}_Alligator_{FAST}_{MID}_{SLOW}'
    min_date = 20220701

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
        # MP (中价) := (最高价 + 最低价) / 2
        mp = (pd.Series(self.highPrice) + pd.Series(self.lowPrice)) / 2
        
        # MEMA
        
        # LIPS (嘴唇/绿线): MEMA(MP, FAST)
        self.lips = mp.ewm(alpha=1/self.FAST, adjust=False).mean().values
        
        # TEETH (牙齿/红线): MEMA(MP, MID)
        self.teeth = mp.ewm(alpha=1/self.MID, adjust=False).mean().values
        
        # JAW (下巴/蓝线): MEMA(MP, SLOW)
        self.jaw = mp.ewm(alpha=1/self.SLOW, adjust=False).mean().values
        
        self.close_arr = self.closePrice

    def GetSig(self, i):
        # 暖身期检查 (确保有足够数据计算指标)
        if i < self.SLOW:
            self.prePosition = self.position
            self.position = 0
            return

        # 获取当前分钟的指标值
        price = self.close_arr[i]
        l = self.lips[i]
        t = self.teeth[i]
        j = self.jaw[i]
        
        # 信号逻辑:
        # 买入信号: Price > Lips > Teeth > Jaw
        # 卖出信号: Price < Lips < Teeth < Jaw
        # 否则: 空仓
        
        sig = 0 # 默认为空仓
        
        if price > l and l > t and t > j:
            sig = 1 # 持有多仓
        elif price < l and l < t and t < j:
            sig = -1 # 持有空仓
        else:
            sig = 0 # 空仓
        
        self.prePosition = self.position
        self.position = sig

if __name__ == "__main__":
    run_backtest(AlligatorStrategy)
