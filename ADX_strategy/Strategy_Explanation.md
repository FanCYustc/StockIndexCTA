# ADX 策略说明

## 1. 核心思想
平均趋向指标（Average Directional Index，简称 ADX）主要用于衡量趋势的强弱，而非趋势的方向。该策略结合了 ADX 指标对趋势强度的判断以及价格与均线的交叉关系来捕捉趋势性机会。当 ADX 显示趋势较强（大于特定阈值）且价格突破均线时，视为趋势确立的信号。

## 2. 指标计算
设 $H_t$ 为 $t$ 时刻的最高价，$L_t$ 为最低价，$C_t$ 为收盘价，$n$ 为计算周期（默认 14）。$EMA_n(X)$ 表示对序列 $X$ 进行周期为 $n$ 的指数移动平均。

### 计算步骤：

1.  **计算真实波幅 (True Range, TR)**:
    $$TR_t = \max(H_t - L_t, |H_t - C_{t-1}|, |C_{t-1} - L_t|)$$
    $$MTR_t = EMA_n(TR_t)$$
    
2.  **计算方向变动 (Directional Movement, DM)**:
    首先计算当日波幅变动：
    $$HD_t = H_t - H_{t-1}$$
    $$LD_t = L_{t-1} - L_t$$
    
    确定正向动向值 $(+DM_t)$ 和负向动向值 $(-DM_t)$：
    $$+DM_t = \begin{cases} HD_t, & \text{if } HD_t > 0 \text{ and } HD_t > LD_t \\ 0, & \text{otherwise} \end{cases}$$ 
    $$-DM_t = \begin{cases} LD_t, & \text{if } LD_t > 0 \text{ and } LD_t > HD_t \\ 0, & \text{otherwise} \end{cases}$$ 
    
    计算平滑后的动向值：
    $$DMP_t = EMA_n(+DM_t)$$
    $$DMM_t = EMA_n(-DM_t)$$

3.  **计算方向性指标 (Directional Indicators, DI)**:
    $$PDI_t = \frac{DMP_t}{MTR_t} \times 100$$
    $$MDI_t = \frac{DMM_t}{MTR_t} \times 100$$

4.  **计算平均趋向指标 (Average Directional Index, ADX)**:
    首先计算趋向指数 (DX)：
    $$DX_t = \frac{|PDI_t - MDI_t|}{PDI_t + MDI_t} \times 100$$ 
    
    最后计算 ADX：
    $$ADX_t = EMA_n(DX_t)$$

*(注：研报中提及均线，但未明确指定均线计算方式，本策略假设使用与 ADX 相同周期的简单移动平均线 SMA 或 EMA)*

## 3. 交易逻辑

### 入场信号
*   **买入（做多）**: 当 $ADX_t > 40$，且收盘价 $C_t$ 上穿均线时。
*   **卖出（做空）**: 当 $ADX_t > 40$，且收盘价 $C_t$ 下穿均线时。

### 信号状态
*   策略持有状态分为：看多（1）、看平（0）、看空（-1）。
*   当满足买入条件时，信号转为 1。
*   当满足卖出条件时，信号转为 -1。

## 4. 总结
该策略属于典型的趋势跟踪策略，利用 ADX 过滤掉震荡行情（低 ADX 值），只在趋势强度足够（ADX > 40）且价格确认突破（穿过均线）时入场。研报测试显示 Length=14 为默认参数，但在不同指数上最优参数可能有所不同（如 12-25 之间）。