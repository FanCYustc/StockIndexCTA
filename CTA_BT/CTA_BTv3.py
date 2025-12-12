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
        self.active_trade_pnl = 0.0 # PnL accumulated for the current open trade
        self.trade_logs = [] # Stores details of completed trades

    def CmpRet(self, nowClose, nowOpen):
        ret = self.prePosition * (nowClose / nowOpen - 1)
        if self.prePosition != self.position:
            ret = ret * (1 - 0.0)
        return ret

    def run_backtest(self, start_minute=5):
        self.getOrgData()
        self.prepare_data()

        self.current_day_pnl = 0.0 # Initialize daily PnL
        self.entry_price = None # Initialize entry price for trade tracking
        self.entry_minute = None # Initialize entry minute for trade tracking

        for i in range(start_minute, 229):
            self.prePosition = self.position # Store the position *before* GetSig updates it for the current minute
            self.GetSig(i)
            
            nowOpen = self.openPrice[i]
            nowClose = self.closePrice[i]

            # Calculate minute PnL
            ret = self.CmpRet(nowClose, nowOpen)
            self.PNL.append(ret)
            
            # Update current day's PnL
            self.current_day_pnl += ret

            # --- Trade Tracking Logic ---
            if self.position != self.prePosition: # Position changed (trade entry/exit/reversal)
                # If prePosition was not 0, it means an existing trade was closed or reversed
                if self.prePosition != 0:
                    exit_price = nowOpen if self.position == 0 else nowClose # If full exit, use open. If reversal, use close for segment
                    entry_price = self.entry_price if hasattr(self, 'entry_price') else None

                    # Only log if an entry price was recorded, otherwise it's just a position change from flat
                    if entry_price is not None:
                        # Log completed trade
                        self.trade_logs.append({
                            'entry_date': self.td,
                            'entry_minute': self.entry_minute,
                            'exit_date': self.td,
                            'exit_minute': i,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'position_size': self.prePosition, # The position size of the trade just closed
                            'pnl': self.active_trade_pnl
                        })
                        
                    self.active_trade_pnl = 0.0 # Reset for new/next trade
                    self.entry_price = None # Clear entry details
                    self.entry_minute = None # Clear entry details


                # If new position is not 0, a new trade is opened
                if self.position != 0:
                    self.entry_price = nowOpen
                    self.entry_minute = i
            
            # Accumulate PnL for the current active trade
            if self.position != 0:
                self.active_trade_pnl += ret

        # Handle any open trade at the end of the day
        if self.position != 0:
            if hasattr(self, 'entry_price') and self.entry_price is not None:
                self.trade_logs.append({
                    'entry_date': self.td,
                    'entry_minute': self.entry_minute,
                    'exit_date': self.td, # End of day is exit
                    'exit_minute': 229, # Last minute of the day
                    'entry_price': self.entry_price,
                    'exit_price': self.closePrice[228], # Use last close price of the day
                    'position_size': self.position,
                    'pnl': self.active_trade_pnl
                })
            self.active_trade_pnl = 0.0
            self.entry_price = None
            self.entry_minute = None
        # --- End Trade Tracking Logic ---


def run_backtest(strategy_cls):
    tradedates = pd.read_csv(r'E:\StockIndexCTA\研究\UpdateTD\tradedates.csv')
    tradedates = tradedates['TradingDayInt'].to_list()

    rslt = []
    all_trade_logs = []

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

        RET = np.sum(stg.PNL) # PNL is still used for daily return calculation
        rslt.append([td, RET])
        print(f"{td} 收益: {RET:.6f}")
        
        all_trade_logs.extend(stg.trade_logs)

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
        plt.pause(0.015)

    plt.ioff()

    # -------------------------------
    # 计算指标
    # -------------------------------

    df = pd.DataFrame(rslt, columns=["date", "ret"])
    df["cum_ret"] = np.cumsum(df["ret"])
    total_days = len(df)
    
    # 保存所有交易记录
    trade_df = pd.DataFrame(all_trade_logs)
    
    strategy_file = inspect.getfile(strategy_cls)
    result_dir = os.path.dirname(strategy_file)
    os.makedirs(result_dir, exist_ok=True)
    
    trade_save_path = os.path.join(result_dir, f"{strategy_cls.name}_trades.csv")
    trade_df.to_csv(trade_save_path, index=False)
    print(f"所有交易记录已保存到：{trade_save_path}")

    # --- Calculate enhanced trade metrics ---
    total_trades = len(trade_df)
    if total_trades > 0:
        winning_trades = trade_df[trade_df['pnl'] > 0]
        losing_trades = trade_df[trade_df['pnl'] < 0]

        num_winning_trades = len(winning_trades)
        num_losing_trades = len(losing_trades)

        win_rate = (num_winning_trades / total_trades) * 100 if total_trades > 0 else 0

        avg_win_pnl = winning_trades['pnl'].mean() if num_winning_trades > 0 else 0
        avg_loss_pnl = losing_trades['pnl'].mean() if num_losing_trades > 0 else 0

        # P/L Ratio: Average Profit / Average Loss (absolute value)
        pl_ratio = abs(avg_win_pnl / avg_loss_pnl) if avg_loss_pnl != 0 else np.nan

        # Avg Net Profit per trade
        total_net_pnl = trade_df['pnl'].sum()
        avg_net_profit = total_net_pnl / total_trades
    else:
        win_rate = 0
        pl_ratio = np.nan
        avg_net_profit = 0
    # --- End enhanced trade metrics calculation ---
    
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
        f"胜率: {win_rate:.2f}%\n"
        f"盈亏比: {pl_ratio:.2f}\n"
        f"平均每笔净收益: {avg_net_profit:.4f}\n"
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

    # 保存图片
    image_save_path = os.path.join(result_dir, f"{strategy_cls.name}.png")
    fig.savefig(image_save_path)
    print(f"累计收益图已保存到：{image_save_path}")

    return df