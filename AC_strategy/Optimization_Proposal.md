# AC策略：滚动回测(WFA)与性能优化完整实施方案

基于你的决策，本方案旨在构建一套严谨的**滚动窗口分析 (Walk-Forward Analysis, WFA)** 系统，并对策略底层进行**向量化加速**，以实现高效且抗过拟合的参数寻优。

## 1. 总体架构

我们将开发两个核心模块：
1.  **高性能策略模块**: 重构 `ACStrategy`，利用向量化运算替代逐行循环判断，大幅提升单次回测速度。
2.  **滚动回测引擎 (WFA Engine)**: 一个全新的驱动程序（类似 `CTA_BTv3.py`），负责时间窗口的滚动、贝叶斯优化调度以及回测结果的拼接。

---


## 2. 步骤一：策略计算向量化 (Vectorization)

当前的 `GetSig(i)` 在每一分钟的循环中通过 `if` 语句访问过去的数据点，效率较低。我们将利用 `Pandas` 的矩阵运算能力，在 `prepare_data` 阶段一次性生成全天的信号。

### 改造逻辑
*   **当前**: `for i in minutes: GetSig(i) -> check data[i], data[i-1]...`
*   **目标**:
    1.  在 `prepare_data` 中计算 `AC` 值。
    2.  利用 `shift()` 构造 `p1, p2, p3` 列（即滞后1, 2, 3分钟的值）。
    3.  利用布尔索引 (Boolean Indexing) 一次性计算出所有满足买入/卖出条件的时刻，生成 `TargetPosition` 数组。
    4.  `GetSig(i)` 简化为直接读取 `self.target_positions[i]`。

**预期代码结构 (伪代码)**:
```python
def prepare_data(self):
    # ... 计算 AC ...
    ac = self.ac_series
    
    # 构造滞后序列
    p1 = pd.Series(ac).shift(1)
    p2 = pd.Series(ac).shift(2)
    p3 = pd.Series(ac).shift(3)
    
    # 向量化计算买入条件 (Mask)
    cond_buy = ( (p1<=0) & (ac>0) & (ac>p1) & (p1>p2) ) | \
               ( (ac>0) & (ac>p1) & (p1>p2) ) | ...
               
    # 向量化计算卖出条件 (Mask)
    cond_sell = ...
    
    # 生成目标仓位
    self.sig_array = np.zeros(len(ac))
    self.sig_array[cond_buy] = 1
    self.sig_array[cond_sell] = -1
    
    # 处理持仓保持 (fill logic if needed)
    # 注意：如果信号是“触发式”而非“状态式”，需在循环中简单处理状态延续
```

---


## 3. 步骤二：构建滚动回测引擎 (WFA Engine)

我们将创建一个新文件 `WFA_BT.py` (或类似命名)，专门处理滚动优化的逻辑，仿照 `CTA_BTv3.py`的结构在CTA_BT文件夹创建。

### 3.1 时间窗口设计
*   **训练窗口 (Training Window)**: 12个月 (用于参数优选)
*   **测试窗口 (Testing Window)**: 3个月 (用于样本外验证/实盘模拟)
*   **滚动步长**: 3个月

**滚动示意图**:
```text
Round 1: [训练: 2016.01 - 2016.12] -> (优化出 Par1) -> [测试: 2017.01 - 2017.03 用 Par1]
Round 2: [训练: 2016.04 - 2017.03] -> (优化出 Par2) -> [测试: 2017.04 - 2017.06 用 Par2]
Round 3: [训练: 2016.07 - 2017.06] -> (优化出 Par3) -> [测试: 2017.07 - 2017.09 用 Par3]
...
```
*注：训练窗口随时间向前滑动，始终包含最近1年的数据。*

### 3.2 贝叶斯优化集成 (Optuna)
在每个训练窗口内，运行 Optuna：
*   **目标函数**: 最大化总收益 (Total Return)。
*   **参数空间**: `n1: [5, 60]`, `n2: [10, 100]`, 约束 `n2 > n1 + 5`。
*   **迭代次数**: 约 30-50 次 (得益于向量化加速，这会很快)。

### 3.3 核心流程伪代码

```python
def run_wfa():
    # 1. 加载所有交易日
    all_dates = load_trade_dates()
    
    # 2. 设定起始点
    start_idx = 0 
    window_train_len = 242 # 约1年
    window_test_len = 60   # 约3个月
    
    wfa_results = [] # 存储最终拼接的资金曲线
    
    while start_idx + window_train_len + window_test_len < len(all_dates):
        # A. 定义切片
        train_dates = all_dates[start_idx : start_idx + window_train_len]
        test_dates = all_dates[start_idx + window_train_len : start_idx + window_train_len + window_test_len]
        
        # B. 训练阶段 (In-Sample Optimization)
        best_params = run_optuna_optimization(train_dates)
        print(f"窗口 {train_dates[-1]} 最佳参数: {best_params}")
        
        # C. 测试阶段 (Out-of-Sample Testing)
        # 使用 best_params 在 test_dates 上跑回测
        period_pnl = run_backtest_period(test_dates, best_params)
        
        wfa_results.extend(period_pnl)
        
        # D. 滚动
        start_idx += window_test_len

    # 3. 统计与绘图
    analyze_wfa_performance(wfa_results)
```

---


## 4. 实施计划 (Action Items)

为了确保不破坏现有代码，我们将按以下顺序操作：

1.  **创建新策略文件** `AC_strategy/strategy_vec.py`:
    *   继承原 `ACStrategy` 或 `BaseStrategy`。
    *   重写 `prepare_data` 实现向量化。
    *   重写 `GetSig` 以适配向量化数据。
    *   *验证*: 运行一次单日回测，确保结果与原版逻辑一致。

2.  **创建 WFA 引擎** `CTA_BT/run_wfa.py`:
    *   实现日期切片逻辑。
    *   集成 `optuna` 的 `objective` 函数。
    *   实现结果拼接和最终指标计算（WFA Sharpe, WFA Drawdown）。

3.  **执行与分析**:
    *   运行 `run_wfa.py`。
    *   生成一份 `wfa_report.csv` 记录每一期的最佳参数和对应收益，观察参数是否稳定，保存在`AC_strategy/`中。

此方案完美兼顾了**运行效率**（向量化+局部数据优化）与**科学性**（滚动窗口+样本外验证）。
