# CTA_BTv3.py Changes Log

## Overview
This document outlines the modifications made to `CTA_BT/CTA_BTv3.py` in the `framework-improvements` branch compared to the `master` branch. The changes were aimed at improving trade tracking accuracy, adding performance metrics, and enhancing visualization.

## Key Changes

### 1. Enhanced Trade Tracking Logic
- **Old Behavior**: Simply recorded the position and return for every minute where `ret != 0` into a flat list `trade_records`. This made it difficult to reconstruct exact trade entry/exit points and calculate per-trade statistics.
- **New Behavior**: 
    - Introduced `self.trade_logs` (list of dictionaries) to store structured trade data.
    - Implemented explicit logic to track:
        - `entry_price` and `entry_minute`
        - `exit_price` and `exit_minute`
        - **Reversals**: Correctly handles cases where position flips (e.g., 1 to -1) by closing the current trade and opening a new one in the same minute.
        - **Daily Close**: Automatically closes any open position at the end of the trading day (minute 229) to ensure accurate daily PnL accounting.

### 2. Advanced Performance Metrics
- Added calculation of the following metrics at the end of the backtest:
    - **Win Rate**: Percentage of profitable trades.
    - **P/L Ratio**: Average Profit / Average Loss (absolute value).
    - **Average Net Profit**: Total PnL / Total Trades.
- These metrics are now displayed in the final plot's text box.

### 3. Visualization Improvements (Drawdown Plot)
- **Structure**: Changed the plot layout from a single axis (`ax`) to two subplots (`ax1`, `ax2`) with a 3:1 height ratio.
    - `ax1`: Cumulative Return (Top)
    - `ax2`: Drawdown / Underwater Plot (Bottom)
- **Features**:
    - `ax2` now shows the drawdown curve with a blue fill (`fill_between`), making it easier to visualize risk and recovery periods.
    - Text box with metrics is updated to include the new trade statistics.

### 4. Code Refactoring
- Renamed `all_trade_records` to `all_trade_logs` to reflect the structured nature of the data.
- Updated the in-loop plotting code to target `ax1` instead of `ax`.
