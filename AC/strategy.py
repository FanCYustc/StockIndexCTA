import sys
sys.path.append(r"E:\StockIndexCTA")

from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd

class ACStrategy(BaseStrategy):

    symbol = "IF"
    n1 = 35
    n2 = 135
    name = f'{symbol}_AC_{n1}_{n2}'
    min_date = 20220101

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

        # --- 向量化指标计算 ---
        
        # 1. 中间价
        median_price = (self.highPrice + self.lowPrice) / 2.0
        mp_series = pd.Series(median_price)

        # 2. AO
        n1 = self.n1
        n2 = self.n2
        
        sma_fast = mp_series.rolling(window=n1).mean()
        sma_slow = mp_series.rolling(window=n2).mean()
        ao = sma_fast - sma_slow

        # 3. AC
        sma_ao = ao.rolling(window=n1).mean()
        ac_series = ao - sma_ao
        self.ac_series = ac_series.values 
        
        # --- 向量化逻辑准备 ---
        
        # 预计算平移后的AC值
        ac = self.ac_series
        p1 = np.roll(ac, 1) # p1[i] = ac[i-1]
        p2 = np.roll(ac, 2)
        p3 = np.roll(ac, 3)
        
        # 处理NaN/边界问题
        p1[:1] = np.nan; p2[:2] = np.nan; p3[:3] = np.nan
        
        is_rising_1 = (ac > p1)
        is_rising_2 = (p1 > p2)
        is_rising_3 = (p2 > p3)
        
        is_falling_1 = (ac < p1)
        is_falling_2 = (p1 < p2)
        is_falling_3 = (p2 < p3)
        
        # 2. 入场条件
        # 买入: (正区域 & 2连涨) 或 (负区域 & 3连涨)
        buy_cond_pos = (ac > 0) & is_rising_1 & is_rising_2
        buy_cond_neg = (ac < 0) & is_rising_1 & is_rising_2 & is_rising_3
        raw_buy_signal = (buy_cond_pos | buy_cond_neg)
        
        # 卖出: (负区域 & 2连跌) 或 (正区域 & 3连跌)
        sell_cond_neg = (ac < 0) & is_falling_1 & is_falling_2
        sell_cond_pos = (ac > 0) & is_falling_1 & is_falling_2 & is_falling_3
        raw_sell_signal = (sell_cond_neg | sell_cond_pos)
        
        # --- 状态机模拟 ---
        # 初始化
        pos_arr = np.zeros(len(ac))
        current_pos = 0.0
        
        start_idx = n2
        ac_vals = ac
        p1_vals = p1
        buy_sigs = raw_buy_signal.astype(bool)
        sell_sigs = raw_sell_signal.astype(bool)
        
        for i in range(start_idx, len(ac)):
            
            # 1. 强制出场逻辑
            if current_pos == 1 and ac_vals[i] < p1_vals[i]:
                current_pos = 0
            elif current_pos == -1 and ac_vals[i] > p1_vals[i]:
                current_pos = 0
                
            # 2. 入场逻辑
            # 有信号则买入
            if buy_sigs[i]:
                current_pos = 1
            # 有信号则卖出
            elif sell_sigs[i]:
                current_pos = -1
            
            pos_arr[i] = current_pos
            
        self.target_positions = pos_arr

    def GetSig(self, i):
        self.prePosition = self.position
        self.position = self.target_positions[i]

if __name__ == "__main__":
    run_backtest(ACStrategy)