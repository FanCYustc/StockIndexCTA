# Change Log - ADX Strategy

## 2025-12-10

- **Parameters Update**
  - Adjusted `N` from 20 to 14.
  - Adjusted `ADX_THRESHOLD` from 25 to 28.

- **Refactoring**
  - Fixed ADX strategy entry logic to be State-Based.
  - Modified code in `ADX_strategy/strategy.py`.

- **Initialization**
  - Initialized ADX strategy structure.
  - Added backtest results.


## 2025-12-12

将信号触发逻辑反转，保存为IM_ADX_14