import pandas as pd
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
import os
import inspect


matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False 

class BaseStrategy:
    def __init__(self, td, symbol):
        self.td = td
        self.symbol = symbol   # "IM", "IF", "000852", "000300"
        self.raw_data = None
        self.PNL = []
        self.position = 0
        self.prePosition = 0
        self.trade_records = []

    def CmpRet(self, nowClose, nowOpen):
        ret = self.prePosition * (nowClose / nowOpen - 1)
        if self.prePosition != self.position:
            ret = ret * (1 - 0.0)
        return ret

    def run_backtest(self, start_minute=5):
        self.getOrgData()
        self.prepare_data()

        for i in range(start_minute, 229):

            self.GetSig(i)
            
            # 获取当前分钟的开盘价和收盘价
            nowOpen = self.openPrice[i]
            nowClose = self.closePrice[i]

            ret = self.CmpRet(nowClose, nowOpen)
            self.PNL.append(ret)

            if ret != 0:
                self.trade_records.append([
                    self.td,           # 交易日期
                    i,                 # 分钟索引 (i)
                    nowOpen,           # 开盘价
                    nowClose,          # 收盘价
                    self.prePosition,  # 持仓信号 (上一分钟的仓位)
                    ret                # 分钟收益率
                ])


def run_backtest(strategy_cls):
    tradedates = pd.read_csv(r'E:\StockIndexCTA\研究\UpdateTD\tradedates.csv')
    tradedates = tradedates['TradingDayInt'].to_list()

    rslt = []
    all_trade_records = [] 

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_title(f'Cumulative Return - {strategy_cls.name}') 
    plt.ion()

    for td in tradedates:
        if td < strategy_cls.min_date:
            continue
        try:
            stg = strategy_cls(td, strategy_cls.symbol)
            stg.run_backtest()
        except (FileNotFoundError, pd.errors.EmptyDataError):
            print(f"跳过 {td}, {strategy_cls.symbol} 无数据")
            continue

        RET = np.sum(stg.PNL)
        rslt.append([td, RET])
        print(f"{td} 收益: {RET:.6f}")
        
        all_trade_records.extend(stg.trade_records)

        ax.clear()
        dates = [str(x[0]) for x in rslt]
        rets = np.cumsum(np.array([x[1] for x in rslt]))

        ax.plot(dates, rets, linewidth=1, color='#8B0000', label='Cumulative Return') 
        ax.set_title(f'Cumulative Return - {strategy_cls.name} (Current Date: {td})') 
        
        step = max(1, len(dates)//10)
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels(dates[::step], rotation=45, fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.6) 
        plt.tight_layout()
        plt.pause(0.025)

    plt.ioff()

    # -------------------------------
    # 计算指标
    # -------------------------------

    df = pd.DataFrame(rslt, columns=["date", "ret"])
    df["cum_ret"] = np.cumsum(df["ret"])
    total_days = len(df)
    
    # 保存分钟交易明细
    trade_df = pd.DataFrame(
        all_trade_records,
        columns=["date", "minute_i", "open_price", "close_price", "position", "minute_ret"]
    )
    
    strategy_file = inspect.getfile(strategy_cls)
    result_dir = os.path.dirname(strategy_file)
    os.makedirs(result_dir, exist_ok=True)
    
    trade_save_path = os.path.join(result_dir, f"{strategy_cls.name}_trades.csv")
    trade_df.to_csv(trade_save_path, index=False)
    print(f"分钟交易明细已保存到：{trade_save_path}")
    
    # -------------------------------
    # 指标计算和日收益保存
    # -------------------------------
    annual_ret = df["cum_ret"].iloc[-1] * 242 / total_days
    sharpe = (df["ret"].mean() / df["ret"].std()) * np.sqrt(242) if df["ret"].std() != 0 else np.nan 

    # ===== 最大回撤 =====
    cum_max = df["cum_ret"].cummax()
    drawdown = df["cum_ret"] - cum_max
    max_drawdown = -drawdown.min()

    calmar = annual_ret / max_drawdown if max_drawdown != 0 else np.nan

    start_date = str(df["date"].iloc[0])
    end_date = str(df["date"].iloc[-1])
    days = len(df)

    save_path = os.path.join(result_dir, f"{strategy_cls.name}.csv")
    df.to_csv(save_path, index=False)
    print(f"日结果已保存到：{save_path}")

    ax.set_title(f'Cumulative Return - {strategy_cls.name}')
    ax.plot(df["date"].astype(str), df["cum_ret"], linewidth=1, color='#8B0000')

    text_str = (
        f"年化收益率: {annual_ret:.2%}\n"
        f"夏普比率: {sharpe:.2f}\n"
        f"卡玛比率: {calmar:.2f}\n"
        f"最大回撤: {max_drawdown:.2%}\n"
        f"{start_date} - {end_date}({days}天)"
    )

    ax.text(0.01, 0.97, text_str, transform=ax.transAxes,
             verticalalignment='top', fontsize=9,
             bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', boxstyle='round,pad=0.5')) 

    step = max(1, len(df)//10)
    xtick_labels = df["date"].astype(str)[::step]
    ax.set_xticks(range(0, len(df), step))
    ax.set_xticklabels(xtick_labels, rotation=45, fontsize=8)

    ax.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    fig.canvas.draw()
    plt.show()

    return df