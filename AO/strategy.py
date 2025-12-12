import sys
sys.path.append(r"E:\StockIndexCTA")

from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd

class AOStrategy(BaseStrategy):
    # 策略配置
    symbol = "IM"
    
    # AO 参数
    NDAY = 25
    MDAY = 60
    
    name = f'{symbol}_AO_{NDAY}_{MDAY}'
    min_date = 20160101

    def getOrgData(self):
        # 获取原始数据
        path = fr"E:\StockIndexCTA\Data\{self.symbol}_{self.td}.csv"
        self.raw_data = pd.read_csv(path)

    def prepare_data(self):
        # 准备数据
        if self.raw_data is None or self.raw_data.empty:
            return

        arr = self.raw_data.values
        
        # 提取价格数据
        self.openPrice = arr[:, 1]
        self.closePrice = arr[:, 2]
        self.highPrice = arr[:, 3]
        self.lowPrice = arr[:, 4]
        
        # --- 指标计算 ---
        # 1. 计算中间价 MP = (High + Low) / 2
        mp = (self.highPrice + self.lowPrice) / 2.0
        
        # 2. 计算 AO = SMA(MP, nDay) - SMA(MP, mDay)
        mp_series = pd.Series(mp)
        sma_n = mp_series.rolling(window=self.NDAY).mean()
        sma_m = mp_series.rolling(window=self.MDAY).mean()
        self.ao = (sma_n - sma_m).values

    def GetSig(self, i):
        # 暖身期检查
        if i < self.MDAY + 2:
            self.prePosition = self.position
            self.position = 0
            return

        # 获取当前及之前的 AO 值
        ao_curr = self.ao[i]        # t
        ao_prev = self.ao[i-1]      # t-1
        ao_prev2 = self.ao[i-2]     # t-2
        
        # 信号逻辑:
        sig = self.position # 默认维持原有仓位
        
        buy_signal = False
        sell_signal = False

        # 1. 零轴穿越 (Zero Cross)
        if ao_prev < 0 and ao_curr > 0:
            buy_signal = True
        elif ao_prev > 0 and ao_curr < 0:
            sell_signal = True

        # 2. 碟形 (Saucer)
        if not buy_signal and not sell_signal:
            # 买入: AO > 0, 探底回升
            if ao_curr > 0 and ao_prev > 0 and ao_prev2 > 0:
                if ao_curr > ao_prev and ao_prev < ao_prev2:
                    buy_signal = True
            # 卖出: AO < 0, 探顶回落
            if ao_curr < 0 and ao_prev < 0 and ao_prev2 < 0:
                if ao_curr < ao_prev and ao_prev > ao_prev2:
                    sell_signal = True

        # 3. 双峰 (Twin Peaks)
        if not buy_signal and not sell_signal:
            lookback = self.MDAY
            start_idx = max(0, i - lookback)
            
            # 双峰买入
            if ao_curr < 0 and ao_curr > ao_prev and ao_prev < ao_prev2:
                second_bottom_val = ao_prev
                second_bottom_idx = i - 1
                found_first_bottom = False
                
                for k in range(second_bottom_idx - 1, start_idx, -1):
                    val = self.ao[k]
                    if val >= 0: break
                    
                    val_next = self.ao[k+1]
                    val_prev = self.ao[k-1]
                    
                    if val < val_next and val < val_prev:
                        if second_bottom_val > val:
                            found_first_bottom = True
                        break 
                
                if found_first_bottom:
                    buy_signal = True

            # 双峰卖出
            if ao_curr > 0 and ao_curr < ao_prev and ao_prev > ao_prev2:
                second_top_val = ao_prev
                second_top_idx = i - 1
                found_first_top = False
                
                for k in range(second_top_idx - 1, start_idx, -1):
                    val = self.ao[k]
                    if val <= 0: break
                    
                    val_next = self.ao[k+1]
                    val_prev = self.ao[k-1]
                    
                    if val > val_next and val > val_prev:
                        if second_top_val < val:
                            found_first_top = True
                        break
                
                if found_first_top:
                    sell_signal = True

        if buy_signal:
            sig = 1
        elif sell_signal:
            sig = -1
            
        self.prePosition = self.position
        self.position = sig

if __name__ == "__main__":
    run_backtest(AOStrategy)