# StockIndexCTA

This project focuses on developing and backtesting single-factor intraday strategies for individual futures using minute-level time series data. It is a Python-based CTA backtesting framework for Stock Index Futures (e.g., IM, IF, IC). The framework allows defining trading strategies, running minute-level backtests over historical intraday data, and visualizing cumulative returns.

## Project Structure

*   **`CTA_BT/`**: Contains the core backtesting engine.
    *   `CTA_BTv3.py`: The main script defining the `BaseStrategy` class and the `run_backtest` driver function. It handles data iteration, PnL calculation, and plotting.
*   **`Data/`**: Stores historical intraday minute-level data files in CSV format (e.g., `IC_20160104.csv`). Files appear to be named `[Symbol]_[Date].csv`. Don't change the files in this folder anytime. Columns include:
   1. MinInt: represents the minute of the day(240 minutes a day, range from 931 to 1500).
   2. open_price: The price at which the instrument opened trading during that specific minute.
   3. close_price: The price at which the instrument closed trading at the end of that specific minute.
   4. high_price: The highest price reached by the instrument during that specific minute.
   5. low_price: The lowest price reached by the instrument during that specific minute.
   6. volume: The total number of contracts or shares traded during that specific minute.
   7. open_interest: The total number of outstanding derivative contracts that have not been closed out or delivered at that specific minute.
*   **`QJTP/`**: Directory for specific strategy implementations.
    *   `strategy.py`: An example implementation of a strategy (`MinStrategy`) inheriting from `BaseStrategy`.
    *   `*_trades.csv`, `*.csv`: Output files containing trade logs and daily return summaries.
*   **`研究/`** (Research):
    *   `UpdateTD/`: Contains `tradedates.csv`, which provides the list of trading dates used by the backtester.
    *   `研报/`: Research reports (likely PDF/Docs).

## Architecture

1.  **Core Engine (`CTA_BTv3.py`)**:
    *   **`BaseStrategy`**: Abstract base class. Manages state (`position`, `PNL`, `trade_records`) and basic return calculation (`CmpRet`).
    *   **`run_backtest(strategy_cls)`**: The driver function. It reads the trading calendar, instantiates the strategy for each day, collects results, plots the cumulative return curve, and saves metrics (Sharpe, Calmar, Max Drawdown).

2.  **Strategy Implementation**:
    *   Strategies must inherit from `BaseStrategy`.
    *   **Required Methods to Override**:
        *   `getOrgData(self)`: Load data for the current day (`self.td`).
        *   `prepare_data(self)`: Pre-process data (e.g., extract prices to numpy arrays).
        *   `GetSig(self, i)`: Logic to calculate the target position for minute `i`.

## Development Workflow

1.  **Strategy Initialization & Documentation**:
    *   **Create Strategy Folder**: Create and name a new strategy folder based on the source material (e.g., specific research reports in `研究/研报/`) or as an iteration of a previous strategy. Naming should be descriptive.
    *   **Draft Strategy Explanation**: **Before writing any code**, create a `Strategy_Explanation.md` file in the new folder. Explain the planned strategy logic, indicators, and trading rules in **Chinese**, following the structure of `QJTP/Strategy_Explanation.md` (Core Idea, Indicator Calculation, Trading Logic, Summary).
    
2.  **Implementation & Backtesting**:
    *   **Write Strategy**: Develop the strategy logic (`strategy.py`) within the framework, ensuring it implements the logic defined in the explanation document.
    *   **Backtest**: Conduct backtesting using `CTA_BTv3.py` to validate performance and logic.

3.  **Maintenance & Synchronization**:
    *   **Sync Documentation**: If the strategy code is modified (optimization, bug fixes), immediately update `Strategy_Explanation.md` to reflect the changes. The code and documentation must always remain consistent.

4.  **Logging & Version Control**:
    *   **Git Management**: Use Git to strictly manage strategy versions.
    *   **Changelog**: Organize a `CHANGELOG.md` in the strategy folder by summarizing the git commit logs related to that strategy.
    *   **Push**: After completing a full backtest, synchronize the related code, strategy implementation, logs, and backtest results to GitHub to preserve version history and backtest traceability.

## Coding Standards

*   **Industrial-Grade Quality**: All generated code must comply with industrial-grade specifications (e.g., PEP 8). Code should be robust, modular, and readable.
*   **Chinese Comments**: Necessary comments, especially those explaining core logic or complex algorithms, must be clearly written in **Chinese**.

## Usage

### 1. Prerequisites
*   Python 3.x
*   Required libraries: `pandas`, `numpy`, `matplotlib`, `scikit-learn` (used in `QJTP/strategy.py`).

### 2. Running the Backtester

using the annaconda environment "base"

### 3. Creating a New Strategy
1.  Create a new Python file (or folder) in the root folder.
2.  Import `BaseStrategy` and `run_backtest` from `CTA_BT.CTA_BTv3`.
    *   *Note: You may need to adjust `sys.path` if your script is not in the root.*
3.  Define a class inheriting from `BaseStrategy`.
4.  Implement `getOrgData`, `prepare_data`, and `GetSig`.
5.  Call `run_backtest(YourStrategyClass)` in the `__main__` block.

## Key Configuration & Notes

*   **Hardcoded Paths**: The codebase currently uses absolute paths (e.g., `E:\StockIndexCTA\...`). These should be updated to relative paths for portability if moved to a different machine.
*   **Data Format**: The backtester expects CSV files in `Data/` to be named in a specific format compatible with the strategy's loading logic.
*   **Visualizations**: `matplotlib` is used for generating cumulative return plots. The code includes support for Chinese characters (`SimHei` font).