# CTA_BT 框架现状与改进计划

## 1. 现有框架原理与结构介绍 (Current Architecture)

`CTA_BT` 是一个针对股指期货（IF/IC/IM）的单因子日内回测框架。其核心思想是基于分钟级别的 K 线数据，进行事件驱动（按时间步进）的模拟交易。

### 1.1 核心组件

*   **`BaseStrategy` (在 `CTA_BTv3.py` 中定义)**
    *   **职责**：作为所有策略的基类，定义了生命周期管理和标准接口。
    *   **生命周期**：
        1.  `__init__`：初始化每日状态（PnL, Position）。
        2.  `getOrgData` & `prepare_data`：每日开始前加载并预处理数据。
        3.  `run_backtest` (Instance method)：每日内部的分钟级循环 (Minute Loop)。
        4.  `GetSig(i)`：**核心逻辑**。策略在第 `i` 分钟根据历史信息决定目标仓位 `position`。
        5.  `CmpRet`：计算单分钟收益。
    *   **交易机制**：
        *   假设在第 `i` 分钟，根据 `GetSig(i)` 更新了 `position`。
        *   收益计算：`ret = prePosition * (nowClose / nowOpen - 1)`。
        *   **注意**：目前的逻辑似乎假设是在第 `i` 分钟的 Open 建仓/持仓，Close 结算盈亏（或者说计算的是 `i` 分钟这一根 K 线的涨跌幅收益）。如果 `GetSig(i)` 使用了第 `i` 分钟的 Close 价格，则可能存在**未来函数**（除非这里的 `GetSig(i)` 实际上是在 `i` 分钟收盘后运行，指导 `i+1` 分钟的操作，但目前代码结构是在同一个循环内）。需要检查策略实现是否严谨。

*   **`run_backtest` (Driver Function)**
    *   **职责**：负责整个回测的时间轴推进、结果汇总和可视化。
    *   **流程**：
        1.  读取交易日历 (`tradedates.csv`)。
        2.  遍历每一个交易日：
            *   实例化策略类。
            *   调用 `stg.run_backtest()` 运行当日回测。
            *   收集当日 `PNL` 和 `trade_records`。
        3.  **统计与可视化**：
            *   计算累计收益、年化收益、Sharpe、MaxDD、Calmar。
            *   绘制并展示累计收益曲线。
            *   保存 `_trades.csv` (分钟级明细) 和 `.csv` (日报表)。

### 1.2 数据流
*   数据源：`Data/[Symbol]_[Date].csv` (包含 MinInt, Open, Close, High, Low, Volume, OpenInterest)。
*   策略内：通过 `prepare_data` 将 DataFrame 转换为 Numpy Array (`self.closePrice` 等) 以提高访问速度。

---

## 2. 改进计划 (Improvement Plan)

为了提升框架的研发效率、仿真真实度和评估全面性，制定以下改进计划。

### 2.1 完善策略评估指标 (Metrics & Analytics)
目前的框架主要关注资金曲线形态。建议补充以下量化指标以评估策略的“性格”和稳健性：

*   **胜率 (Win Rate)**：`盈利交易次数 / 总交易次数`。
*   **盈亏比 (Profit-Loss Ratio)**：`平均盈利 / 平均亏损`。
*   **单笔平均收益 (Avg Net Profit per Trade)**：扣除成本后的数学期望。
*   **持仓周期分析 (Holding Period)**：平均持仓分钟数。
*   **连亏分析 (Max Consecutive Losses)**：评估极端情况下的心理压力。
*   **多空分组统计**：分别统计做多和做空的表现，检测策略的方向性偏差。

### 2.2 增强回测引擎的仿真度 (Simulation Accuracy)
目前的撮合逻辑较为简化，计划增加：

*   **日内止盈止损 (Intra-bar StopLoss/TakeProfit)**：
    *   利用 `High/Low` 价格，在 K 线内部触发止损，而不是必须等到 K 线结束。
*   **滑点模型 (Slippage)**：
    *   除了固定手续费，增加滑点成本（如 1 跳或波动率动态滑点）。
*   **撮合模式配置**：
    *   明确支持“收盘价信号 -> 下一根开盘价成交”的标准模式，避免未来函数争议。

### 2.3 开发效率工具 (Development Tools)
*   **参数网格搜索 (Grid Search)**：
    *   自动遍历参数组合（如 `N`, `Threshold`）并生成热力图报告。
*   **敏感性分析**：
    *   测试参数微调对结果的影响，识别“参数孤岛”型过拟合策略。
*   **批量回测**：
    *   一键运行多品种、多策略。

### 2.4 性能与可视化 (Performance & Visualization)
*   **向量化信号计算**：
    *   将 `GetSig` 中的纯逻辑判断（如 `Close > MA`）向量化，仅保留复杂状态管理在循环中，提升回测速度。
*   **回撤曲线 (Underwater Plot)**：
    *   独立绘制回撤幅度随时间变化的图表。
*   **交易点标记**：
    *   在 K 线图上可视化买卖点，便于人工查错。

### 实施优先级建议
优先实施 **2.1 完善策略评估指标**。
*   **原因**：成本低（不改动核心撮合逻辑，只改统计代码），收益高（能立即提供更多维度的策略筛选依据）。
