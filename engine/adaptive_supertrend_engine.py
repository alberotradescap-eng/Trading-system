"""
Adaptive SuperTrend Trading Engine - Version 17
Enhanced and Bug-Fixed Version

This module contains the complete trading system engine with:
- Bug fixes for missing functions
- Improved error handling
- Configurable paths
- Better modularity
"""

import pandas as pd
import datetime
import time
import numpy as np
import json
import matplotlib.pyplot as plt
import math
import os
import csv
from pathlib import Path

# Optional imports
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

# Optional imports with fallback
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    print("Warning: seaborn not installed. Heatmap visualizations will be limited.")
    HAS_SEABORN = False

try:
    import mplfinance as mpf
    HAS_MPLFINANCE = True
except ImportError:
    print("Warning: mplfinance not installed. Candlestick charts will be limited.")
    HAS_MPLFINANCE = False

try:
    from ta.volume import VolumeWeightedAveragePrice
    from ta.trend import SMAIndicator
    HAS_TA = True
except ImportError:
    print("Warning: ta library not installed. Some indicators may not work.")
    HAS_TA = False


class TradingEngineConfig:
    """Configuration class for trading engine parameters"""

    def __init__(self, base_path=None):
        # Use provided base_path or default to current directory
        self.base_path = Path(base_path) if base_path else Path.cwd()

        # Configure paths relative to base_path
        self.data_path = self.base_path / 'data'
        self.data_simulation_path = self.base_path / 'data-simulation'
        self.reports_path = self.base_path / 'reports'
        self.reports_simulation_path = self.base_path / 'reports-simulation'
        self.logs_path = self.base_path / 'logs'
        self.sounds_path = self.base_path / 'sounds'

        # Create directories if they don't exist
        for path in [self.data_path, self.data_simulation_path,
                     self.reports_path, self.reports_simulation_path,
                     self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)

    def get_path(self, path_type, simulation=False):
        """Get the appropriate path based on type and simulation mode"""
        if path_type == 'data':
            return self.data_simulation_path if simulation else self.data_path
        elif path_type == 'reports':
            return self.reports_simulation_path if simulation else self.reports_path
        elif path_type == 'logs':
            return self.logs_path
        elif path_type == 'sounds':
            return self.sounds_path
        else:
            raise ValueError(f"Unknown path type: {path_type}")


class TradingEngine:
    """Main trading engine class with all trading logic"""

    def __init__(self, config=None, telegram_bot=None):
        self.config = config or TradingEngineConfig()
        self.telegram_bot = telegram_bot
        self.telegram_message = ""

    # ==================== Utility Functions ====================

    def crossover(self, array1, array2):
        """Detect crossover: array1 crosses above array2"""
        return (array1 > array2) & (array1.shift(1) <= array2.shift(1))

    def crossunder(self, array1, array2):
        """Detect crossunder: array1 crosses below array2"""
        return (array1 < array2) & (array1.shift(1) >= array2.shift(1))

    def tick_correction_up(self, level, tick):
        """Round price up to nearest tick"""
        if pd.isna(level):
            level = 0
        multiplier = math.ceil(level / tick)
        return multiplier * tick

    def tick_correction_down(self, level, tick):
        """Round price down to nearest tick"""
        if pd.isna(level):
            level = 0
        multiplier = math.floor(level / tick)
        return multiplier * tick

    # ==================== Market Position Generator ====================

    def marketposition_generator(self, enter_rules, exit_rules):
        """
        Generate market position (0 or 1) based on entry and exit rules

        Args:
            enter_rules: Boolean series for entry signals
            exit_rules: Boolean series for exit signals

        Returns:
            Series with market position (0=out, 1=in position)
        """
        service_dataframe = pd.DataFrame(index=enter_rules.index)
        service_dataframe['enter_rules'] = enter_rules
        service_dataframe['exit_rules'] = exit_rules

        status = 0
        mp = []

        for i, j in zip(enter_rules, exit_rules):
            if status == 0:
                if i == 1 and j != -1:
                    status = 1
            else:
                if j == -1:
                    status = 0
            mp.append(status)

        service_dataframe['mp_new'] = mp
        # Shift position to start from next bar
        service_dataframe['mp_new'] = service_dataframe['mp_new'].shift(1)
        service_dataframe.iloc[0, 2] = 0

        return service_dataframe['mp_new']

    # ==================== Order Validation ====================

    def stop_check(self, dataframe, rules, level, direction):
        """
        Validate entry/exit rules for STOP orders

        Args:
            dataframe: OHLC dataframe
            rules: Boolean series with entry/exit signals
            level: Price level for stop order
            direction: 'long' or 'short'

        Returns:
            Boolean series with validated rules
        """
        service_df = pd.DataFrame(index=dataframe.index)
        service_df['rules'] = rules
        service_df['level'] = level
        service_df['low'] = dataframe['low']
        service_df['high'] = dataframe['high']

        if direction == 'long':
            service_df['new_rules'] = np.where(
                (service_df['rules'] == True) &
                (service_df['high'].shift(-1) >= service_df['level'].shift(-1)),
                True, False
            )
        elif direction == 'short':
            service_df['new_rules'] = np.where(
                (service_df['rules'] == True) &
                (service_df['low'].shift(-1) <= service_df['level'].shift(-1)),
                True, False
            )
        else:
            raise ValueError(f"Invalid direction: {direction}")

        return service_df['new_rules']

    def limit_check(self, dataframe, rules, level, direction):
        """
        Validate entry/exit rules for LIMIT orders

        Args:
            dataframe: OHLC dataframe
            rules: Boolean series with entry/exit signals
            level: Price level for limit order
            direction: 'long' or 'short'

        Returns:
            Boolean series with validated rules
        """
        service_df = pd.DataFrame(index=dataframe.index)
        service_df['rules'] = rules
        service_df['level'] = level
        service_df['low'] = dataframe['low']
        service_df['high'] = dataframe['high']

        if direction == 'long':
            service_df['new_rules'] = np.where(
                (service_df['rules'] == True) &
                (service_df['low'].shift(-1) <= service_df['level'].shift(-1)),
                True, False
            )
        elif direction == 'short':
            service_df['new_rules'] = np.where(
                (service_df['rules'] == True) &
                (service_df['high'].shift(-1) >= service_df['level'].shift(-1)),
                True, False
            )
        else:
            raise ValueError(f"Invalid direction: {direction}")

        return service_df['new_rules']

    # ==================== Trailing Stop ====================

    def compute_trailing_stop(self, trading_system, trail_percent=0.003, direction='long'):
        """
        Compute trailing stop loss exit signals

        Args:
            trading_system: DataFrame with trading system data including 'mp' and 'entry_price'
            trail_percent: Percentage for trailing stop (e.g., 0.003 = 0.3%)
            direction: 'long' or 'short'

        Returns:
            Boolean series with trailing stop exit signals
        """
        df = trading_system.copy()

        # Initialize trailing stop column
        trailing_stop_exit = pd.Series(False, index=df.index)

        # Only compute when in position
        in_position = df['mp'] == 1

        if direction == 'long':
            # For long positions, track highest price and exit if price drops trail_percent below it
            highest_price = pd.Series(index=df.index, dtype=float)
            current_high = 0

            for i in range(len(df)):
                if in_position.iloc[i]:
                    if i == 0 or not in_position.iloc[i-1]:
                        # Just entered position
                        current_high = df['close'].iloc[i]
                    else:
                        # Update highest price
                        current_high = max(current_high, df['high'].iloc[i])

                    highest_price.iloc[i] = current_high

                    # Check if current price drops below trailing stop
                    stop_price = current_high * (1 - trail_percent)
                    if df['close'].iloc[i] < stop_price:
                        trailing_stop_exit.iloc[i] = True
                else:
                    highest_price.iloc[i] = 0

        elif direction == 'short':
            # For short positions, track lowest price and exit if price rises trail_percent above it
            lowest_price = pd.Series(index=df.index, dtype=float)
            current_low = float('inf')

            for i in range(len(df)):
                if in_position.iloc[i]:
                    if i == 0 or not in_position.iloc[i-1]:
                        # Just entered position
                        current_low = df['close'].iloc[i]
                    else:
                        # Update lowest price
                        current_low = min(current_low, df['low'].iloc[i])

                    lowest_price.iloc[i] = current_low

                    # Check if current price rises above trailing stop
                    stop_price = current_low * (1 + trail_percent)
                    if df['close'].iloc[i] > stop_price:
                        trailing_stop_exit.iloc[i] = True
                else:
                    lowest_price.iloc[i] = float('inf')
        else:
            raise ValueError(f"Invalid direction: {direction}")

        return trailing_stop_exit

    # ==================== Stop Loss and Take Profit ====================

    def compute_stop_loss(self, trading_system, stop_loss_rules, enter_rules, exit_rules):
        """
        Apply stop loss rules to entry and exit signals

        Args:
            trading_system: DataFrame with trading system data
            stop_loss_rules: Boolean series indicating stop loss conditions
            enter_rules: Current entry rules
            exit_rules: Current exit rules

        Returns:
            Tuple of (modified_enter_rules, modified_exit_rules)
        """
        trading_system['stop_loss'] = stop_loss_rules
        found_stop_loss = False

        for i in range(1, trading_system.shape[0]):
            current = trading_system.iloc[i]
            idx = trading_system.index[i]

            if current['stop_loss']:
                found_stop_loss = True
                text = f'⚠️ Stop loss triggered at {idx.strftime("%Y-%m-%d %H:%M:%S")}'
                print(text)
                self.telegram_message += text + '\n\n'

            trading_system.loc[idx, 'stop_loss_action'] = found_stop_loss

        stop_loss_action = trading_system['stop_loss_action']

        # Modify rules: no new entries after stop loss, exit when stop loss triggered
        enter_rules = enter_rules & (stop_loss_action == False)
        exit_rules = exit_rules | (stop_loss_action == True)

        return enter_rules, exit_rules

    def compute_take_profit(self, trading_system, take_profit_rules, enter_rules, exit_rules):
        """
        Apply take profit rules to entry and exit signals

        Args:
            trading_system: DataFrame with trading system data
            take_profit_rules: Boolean series indicating take profit conditions
            enter_rules: Current entry rules
            exit_rules: Current exit rules

        Returns:
            Tuple of (modified_enter_rules, modified_exit_rules)
        """
        trading_system['take_profit'] = take_profit_rules
        found_take_profit = False

        for i in range(1, trading_system.shape[0]):
            current = trading_system.iloc[i]
            idx = trading_system.index[i]

            if current['take_profit']:
                found_take_profit = True
                text = f'✅ Take profit triggered at {idx.strftime("%Y-%m-%d %H:%M:%S")}'
                print(text)
                self.telegram_message += text + '\n\n'

            trading_system.loc[idx, 'take_profit_action'] = found_take_profit

        take_profit_action = trading_system['take_profit_action']

        # Modify rules: no new entries after take profit, exit when take profit triggered
        enter_rules = enter_rules & (take_profit_action == False)
        exit_rules = exit_rules | (take_profit_action == True)

        return enter_rules, exit_rules

    # ==================== Core Trading System Application ====================

    def apply_trading_system(self, imported_dataframe, bigpointvalue, tick, direction,
                            order_type, enter_level, enter_rules, exit_rules,
                            operation_money, costs=0, instrument=1,
                            ticker='', export_filename='trading_system.csv',
                            simulation=False, eliminate_same_bar_entry_exit=True):
        """
        Apply trading system rules to dataframe and calculate equity curves

        Args:
            imported_dataframe: OHLC dataframe
            bigpointvalue: Point value for futures (only if instrument=2)
            tick: Minimum price increment
            direction: 'long' or 'short'
            order_type: 'market', 'stop', 'limit', or 'special'
            enter_level: Price level for entry
            enter_rules: Boolean series for entry signals
            exit_rules: Boolean series for exit signals
            operation_money: Capital allocated per operation
            costs: Transaction costs per trade
            instrument: 1=Equity/Forex, 2=Futures
            ticker: Stock/asset symbol
            export_filename: Filename to save results
            simulation: Whether in simulation mode
            eliminate_same_bar_entry_exit: Remove bars with simultaneous entry/exit

        Returns:
            DataFrame with complete trading system results
        """
        dataframe = imported_dataframe.copy()

        # Validate order type for entry
        if order_type == 'stop':
            enter_rules = self.stop_check(dataframe, enter_rules, enter_level, direction)
        elif order_type == 'limit':
            enter_rules = self.limit_check(dataframe, enter_rules, enter_level, direction)

        # Add rules to dataframe
        dataframe['enter_level'] = enter_level
        dataframe['enter_rules'] = enter_rules.apply(lambda x: 1 if x == True else 0)
        dataframe['exit_rules'] = exit_rules.apply(lambda x: -1 if x == True else 0)

        # Generate market position
        dataframe['mp'] = self.marketposition_generator(dataframe['enter_rules'], dataframe['exit_rules'])

        # Calculate entry prices based on order type
        if order_type in ['market', 'special']:
            dataframe['entry_price'] = np.where(
                (dataframe['mp'].shift(1) == 0) & (dataframe['mp'] == 1),
                dataframe['open'],
                np.nan
            )
            if instrument == 1:
                dataframe['number_of_stocks'] = np.where(
                    (dataframe['mp'].shift(1) == 0) & (dataframe['mp'] == 1),
                    operation_money / dataframe['open'],
                    np.nan
                )

        elif order_type == 'stop':
            if direction == 'long':
                dataframe['enter_level'] = dataframe['enter_level'].apply(
                    lambda x: self.tick_correction_up(x, tick)
                )
                real_entry = np.where(
                    dataframe['open'] > dataframe['enter_level'],
                    dataframe['open'],
                    dataframe['enter_level']
                )
            else:  # short
                dataframe['enter_level'] = dataframe['enter_level'].apply(
                    lambda x: self.tick_correction_down(x, tick)
                )
                real_entry = np.where(
                    dataframe['open'] < dataframe['enter_level'],
                    dataframe['open'],
                    dataframe['enter_level']
                )

            dataframe['entry_price'] = np.where(
                (dataframe['mp'].shift(1) == 0) & (dataframe['mp'] == 1),
                real_entry,
                np.nan
            )

            if instrument == 1:
                dataframe['number_of_stocks'] = np.where(
                    (dataframe['mp'].shift(1) == 0) & (dataframe['mp'] == 1),
                    operation_money / real_entry,
                    np.nan
                )

        elif order_type == 'limit':
            if direction == 'long':
                dataframe['enter_level'] = dataframe['enter_level'].apply(
                    lambda x: self.tick_correction_down(x, tick)
                )
                real_entry = np.where(
                    dataframe['open'] < dataframe['enter_level'],
                    dataframe['open'],
                    dataframe['enter_level']
                )
            else:  # short
                dataframe['enter_level'] = dataframe['enter_level'].apply(
                    lambda x: self.tick_correction_up(x, tick)
                )
                real_entry = np.where(
                    dataframe['open'] > dataframe['enter_level'],
                    dataframe['open'],
                    dataframe['enter_level']
                )

            dataframe['entry_price'] = np.where(
                (dataframe['mp'].shift(1) == 0) & (dataframe['mp'] == 1),
                real_entry,
                np.nan
            )

            if instrument == 1:
                dataframe['number_of_stocks'] = np.where(
                    (dataframe['mp'].shift(1) == 0) & (dataframe['mp'] == 1),
                    operation_money / real_entry,
                    np.nan
                )

        # Forward fill entry price and number of stocks
        dataframe['entry_price'] = dataframe['entry_price'].ffill()

        if instrument == 1:
            dataframe['number_of_stocks'] = dataframe['number_of_stocks'].apply(
                lambda x: round(x, 0)
            ).ffill()

        # Mark entry and exit events
        dataframe['events_in'] = np.where(
            (dataframe['mp'] == 1) & (dataframe['mp'].shift(1) == 0),
            'entry',
            ''
        )

        # Calculate open operations (P&L)
        if direction == 'long':
            if instrument == 1:  # Stocks
                dataframe['open_operations'] = (
                    (dataframe['close'] - dataframe['entry_price']) *
                    dataframe['number_of_stocks']
                )
                dataframe['open_operations'] = np.where(
                    (dataframe['mp'] == 1) & (dataframe['mp'].shift(-1) == 0),
                    (dataframe['open'].shift(-1) - dataframe['entry_price']) *
                    dataframe['number_of_stocks'] - 2 * costs,
                    dataframe['open_operations']
                )
            else:  # Futures
                dataframe['open_operations'] = (
                    (dataframe['close'] - dataframe['entry_price']) * bigpointvalue
                )
                dataframe['open_operations'] = np.where(
                    (dataframe['mp'] == 1) & (dataframe['mp'].shift(-1) == 0),
                    (dataframe['open'].shift(-1) - dataframe['entry_price']) *
                    bigpointvalue - 2 * costs,
                    dataframe['open_operations']
                )
        else:  # short
            if instrument == 1:  # Stocks
                dataframe['open_operations'] = (
                    (dataframe['entry_price'] - dataframe['close']) *
                    dataframe['number_of_stocks']
                )
                dataframe['open_operations'] = np.where(
                    (dataframe['mp'] == 1) & (dataframe['mp'].shift(-1) == 0),
                    (dataframe['entry_price'] - dataframe['open'].shift(-1)) *
                    dataframe['number_of_stocks'] - 2 * costs,
                    dataframe['open_operations']
                )
            else:  # Futures
                dataframe['open_operations'] = (
                    (dataframe['entry_price'] - dataframe['close']) * bigpointvalue
                )
                dataframe['open_operations'] = np.where(
                    (dataframe['mp'] == 1) & (dataframe['mp'].shift(-1) == 0),
                    (dataframe['entry_price'] - dataframe['open'].shift(-1)) *
                    bigpointvalue - 2 * costs,
                    dataframe['open_operations']
                )

        dataframe['open_operations'] = np.where(
            dataframe['mp'] == 1,
            dataframe['open_operations'],
            0
        )

        dataframe['events_out'] = np.where(
            (dataframe['mp'] == 1) & (dataframe['exit_rules'] == -1),
            'exit',
            ''
        )

        dataframe['operations'] = np.where(
            (dataframe['exit_rules'] == -1) & (dataframe['mp'] == 1),
            dataframe['open_operations'],
            np.nan
        )

        # Calculate equity curves
        dataframe['closed_equity'] = dataframe['operations'].fillna(0).cumsum()
        dataframe['open_equity'] = (
            dataframe['closed_equity'] +
            dataframe['open_operations'] -
            dataframe['operations'].fillna(0)
        )

        # Add exit price when exiting
        if instrument == 1:
            dataframe['exit_price_quando_esco'] = dataframe['close']

        # Eliminate same-bar entry/exit if requested
        if eliminate_same_bar_entry_exit:
            for i in range(2, dataframe.shape[0]):
                current = dataframe.iloc[i]
                if current['events_in'] == 'entry' and current['events_out'] == 'exit':
                    dataframe.iloc[i] = dataframe.iloc[i-1]

        # Export to CSV
        path = self.config.get_path('reports', simulation)
        if simulation:
            dataframe['stock'] = ticker

        export_path = path / export_filename
        dataframe.to_csv(export_path)
        print(f"Trading system exported to: {export_path}")

        return dataframe


# Export main classes
__all__ = ['TradingEngine', 'TradingEngineConfig']
