import sys
sys.path.append(r"E:\StockIndexCTA")

from CTA_BT.CTA_BTv3 import BaseStrategy, run_backtest
import numpy as np
import pandas as pd

class ADXStrategy(BaseStrategy):
    # 策略配置
    symbol = "IM"
    N = 16 # ADX计算周期
    ADX_THRESHOLD = 30 # ADX阈值
    name = f'{symbol}_ADX_{N}'
    min_date = 20220701

    def getOrgData(self):
        # 获取原始数据
        path = fr"E:\StockIndexCTA\Data\{self.symbol}_{self.td}.csv"
        self.raw_data = pd.read_csv(path)

    def prepare_data(self):
        # 准备数据
        arr = self.raw_data.values
        
        # 提取价格数据 (BaseStrategy需要)
        self.openPrice = arr[:, 1]
        self.closePrice = arr[:, 2]
        self.highPrice = arr[:, 3]
        self.lowPrice = arr[:, 4]
        
        # --- 指标计算 ---
        
        # 1. TR (真实波幅)
        prev_close = pd.Series(self.closePrice).shift(1)
        tr1 = pd.Series(self.highPrice) - pd.Series(self.lowPrice)
        tr2 = (pd.Series(self.highPrice) - prev_close).abs()
        tr3 = (prev_close - pd.Series(self.lowPrice)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 2. MTR (平滑真实波幅) = EMA(TR, N)
        mtr = tr.ewm(span=self.N, adjust=False).mean()
        
        # 3. DM (方向移动)
        hd = pd.Series(self.highPrice) - pd.Series(self.highPrice).shift(1)
        ld = pd.Series(self.lowPrice).shift(1) - pd.Series(self.lowPrice)
        
        plus_dm = np.where((hd > 0) & (hd > ld), hd, 0.0)
        minus_dm = np.where((ld > 0) & (ld > hd), ld, 0.0)
        
        plus_dm = pd.Series(plus_dm, index=pd.Series(self.highPrice).index)
        minus_dm = pd.Series(minus_dm, index=pd.Series(self.lowPrice).index)
        
        dmp = plus_dm.ewm(span=self.N, adjust=False).mean()
        dmm = minus_dm.ewm(span=self.N, adjust=False).mean()
        
        # 4. DI (方向指数)
        pdi = (dmp / mtr) * 100
        mdi = (dmm / mtr) * 100
        
        # 5. DX (动向指数)
        denom = pdi + mdi
        dx = (abs(pdi - mdi) / denom) * 100
        dx = dx.fillna(0)
        
        # 6. ADX (平均动向指数) = EMA(DX, N)
        adx = dx.ewm(span=self.N, adjust=False).mean()
        
        # 7. MA (简单移动平均线)
        ma = pd.Series(self.closePrice).rolling(window=60).mean()
        # 可以改用EMA        


        # 存储计算结果
        self.adx_arr = adx.values
        self.ma_arr = ma.values
        self.close_arr = self.closePrice

    def GetSig(self, i):

        if i < self.N:
            self.prePosition = self.position
            return

        # 获取当前分钟的指标值和价格
        adx_val = self.adx_arr[i]
        
        curr_close = self.close_arr[i]
        curr_ma = self.ma_arr[i]

        prev_close = self.close_arr[i-1]                                                                                
        prev_ma = self.ma_arr[i-1]
        
        # 交易逻辑
        sig = self.position # 默认保持当前仓位 
        
        # 1. 均线交叉定义
        cross_up = (curr_close > curr_ma and prev_close <= prev_ma) # 价格向上突破均线
        cross_down = (curr_close < curr_ma and prev_close >= prev_ma) # 价格向下突破均线
        
        # 2. 趋势过滤条件
        is_trend_strong = (adx_val > self.ADX_THRESHOLD) # ADX判断趋势强度
        
        #if cross_up and is_trend_strong:
        #    sig = 1 # 开多仓
        #elif cross_down and is_trend_strong:
        #    sig = -1 # 开空仓
        
        if cross_up and is_trend_strong:
            sig = -1 # 开空仓
        elif cross_down and is_trend_strong:
            sig = 1 # 开多仓
        # else:
        #     sig = 0 # 平仓
        
        self.prePosition = self.position
        self.position = sig

if __name__ == "__main__":
    run_backtest(ADXStrategy)