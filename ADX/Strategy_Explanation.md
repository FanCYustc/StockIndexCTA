# ADX 策略说明

## 1. 核心思想
平均趋向指标（Average Directional Index，简称 ADX）主要用于衡量趋势的强弱，而非趋势的方向。该策略结合了 ADX 指标对趋势强度的判断以及价格与均线的交叉关系来捕捉趋势性机会。当 ADX 显示趋势较强（大于特定阈值）且价格突破均线时，视为趋势确立的信号。

## 2. 指标计算
**参数设置**：
*   $N = 14$ (ADX 计算周期)
*   $ADX_THRESHOLD = 40$ (ADX 阈值)
*   $MA_WINDOW = 60$ (移动平均线周期)

**计算步骤**：

1.  **计算真实波幅 (True Range, TR)**:
    $$TR_t = \max(H_t - L_t, |H_t - C_{t-1}|, |C_{t-1} - L_t|)$$
    $$MTR_t = EMA_n(TR_t)$$ (使用 span=14 的指数移动平均)
    
2.  **计算方向变动 (Directional Movement, DM)**:
    $$HD_t = H_t - H_{t-1}$$
    $$LD_t = L_{t-1} - L_t$$
    
    $$+DM_t = \begin{cases} HD_t, & \text{if } HD_t > 0 \text{ and } HD_t > LD_t \\ 0, & \text{otherwise} \end{cases}$$
    $$-DM_t = \begin{cases} LD_t, & \text{if } LD_t > 0 \text{ and } LD_t > HD_t \\ 0, & \text{otherwise} \end{cases}$$
    
    $$DMP_t = EMA_n(+DM_t)$$
    $$DMM_t = EMA_n(-DM_t)$$

3.  **计算方向性指标 (Directional Indicators, DI)**:
    $$PDI_t = \frac{DMP_t}{MTR_t} \times 100$$
    $$MDI_t = \frac{DMM_t}{MTR_t} \times 100$$

4.  **计算平均趋向指标 (Average Directional Index, ADX)**:
    $$DX_t = \frac{|PDI_t - MDI_t|}{PDI_t + MDI_t} \times 100$$ 
    $$ADX_t = EMA_n(DX_t)$$

5.  **计算均线 (MA)**:
    $$MA_t = SMA_{60}(C_t)$$ (60周期简单移动平均)

## 3. 交易逻辑

### 入场信号
*   **买入（做多）**：
    1.  当前 $ADX_t > 40$ (趋势显著)。
    2.  收盘价 **上穿** 均线：$C_t > MA_t$ 且 $C_{t-1} \le MA_{t-1}$。
    
*   **卖出（做空）**： 
    1.  当前 $ADX_t > 40$ (趋势显著)。
    2.  收盘价 **下穿** 均线：$C_t < MA_t$ 且 $C_{t-1} \ge MA_{t-1}$。

### 出场逻辑
*   **平仓**： 
    *   若当前分钟未满足上述买入或卖出条件，策略将持仓置为 0（平仓）。
    *   *说明：由于“上穿/下穿”条件仅在突破发生的瞬间成立，且策略逻辑规定非信号时刻平仓，因此该策略实际表现为在突破瞬间持仓 1 分钟的短线行为，除非出现连续反向突破。*

## 4. 总结
该策略基于 ADX 强度（阈值 28）过滤均线（60周期 SMA）突破信号。代码实现上采用了“无信号即平仓”的逻辑，导致策略表现为捕捉瞬间突破的超短线（1分钟）交易，而非持有波段。这与常规的趋势跟踪策略（持有直到趋势反转）有所不同，需注意这一点。
