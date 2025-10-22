"""
Performance Analytics Module

Contains all functions for analyzing trading system performance,
generating reports, and creating visualizations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import csv

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

try:
    import mplfinance as mpf
    HAS_MPLFINANCE = True
except ImportError:
    HAS_MPLFINANCE = False


class PerformanceAnalytics:
    """Performance analysis and reporting for trading systems"""

    def __init__(self, config=None):
        self.config = config

    # ==================== Equity Curve Analysis ====================

    def drawdown(self, equity):
        """
        Calculate drawdown series from equity curve

        Args:
            equity: Series with equity values

        Returns:
            Series with drawdown values (negative)
        """
        maxvalue = equity.expanding(0).max()
        drawdown = equity - maxvalue
        return pd.Series(drawdown, index=equity.index)

    def max_drawdown(self, equity):
        """Calculate maximum drawdown"""
        dd = self.drawdown(equity)
        return round(dd.min(), 2)

    def avg_drawdown_nozero(self, equity):
        """Calculate average drawdown (excluding zeros)"""
        dd = self.drawdown(equity)
        return round(dd[dd < 0].mean(), 2)

    def delay_between_peaks(self, equity):
        """
        Calculate delay (in bars) between equity peaks

        Args:
            equity: Equity curve series

        Returns:
            Series with delay counts
        """
        work_df = pd.DataFrame(equity, index=equity.index)
        work_df['drawdown'] = self.drawdown(equity)
        work_df['delay_elements'] = work_df['drawdown'].apply(lambda x: 1 if x < 0 else 0)
        work_df['resets'] = np.where(work_df['drawdown'] == 0, 1, 0)
        work_df['cumsum'] = work_df['resets'].cumsum()
        a = pd.Series(work_df['delay_elements'].groupby(work_df['cumsum']).cumsum())
        return a

    def max_delay_between_peaks(self, equity):
        """Calculate maximum delay between equity peaks"""
        a = self.delay_between_peaks(equity)
        return a.max()

    def avg_delay_between_peaks(self, equity):
        """Calculate average delay between equity peaks"""
        work_df = pd.DataFrame(equity, index=equity.index)
        work_df['drawdown'] = self.drawdown(equity)
        work_df['delay_elements'] = work_df['drawdown'].apply(lambda x: 1 if x < 0 else np.nan)
        work_df['resets'] = np.where(work_df['drawdown'] == 0, 1, 0)
        work_df['cumsum'] = work_df['resets'].cumsum()
        work_df.dropna(inplace=True)
        a = work_df['delay_elements'].groupby(work_df['cumsum']).sum()
        return round(a.mean(), 2)

    # ==================== Operations Analysis ====================

    def profit(self, equity):
        """Calculate total profit"""
        return round(equity.iloc[-1], 2)

    def operation_number(self, operations):
        """Count total number of operations"""
        return operations.count()

    def avg_trade(self, operations):
        """Calculate average trade result"""
        return round(operations.mean(), 2)

    def gross_profit(self, operations):
        """Calculate total gross profit"""
        return round(operations[operations > 0].sum(), 2)

    def gross_loss(self, operations):
        """Calculate total gross loss"""
        return round(operations[operations <= 0].sum(), 2)

    def profit_factor(self, operations):
        """Calculate profit factor (gross profit / gross loss)"""
        a = self.gross_profit(operations)
        b = self.gross_loss(operations)
        if b != 0:
            return round(abs(a / b), 2)
        else:
            return round(abs(a / 0.00000001), 2)

    def percent_win(self, operations):
        """Calculate percentage of winning trades"""
        if self.operation_number(operations) == 0:
            return 0
        return round(operations[operations > 0].count() / operations.count() * 100, 2)

    def avg_gain(self, operations):
        """Calculate average gain"""
        winning_ops = operations[operations > 0]
        if len(winning_ops) == 0:
            return 0
        return round(winning_ops.mean(), 2)

    def max_gain(self, operations):
        """Calculate maximum gain"""
        winning_ops = operations[operations > 0]
        if len(winning_ops) == 0:
            return 0
        return round(winning_ops.max(), 2)

    def max_gain_date(self, operations):
        """Get date of maximum gain"""
        winning_ops = operations[operations > 0]
        if len(winning_ops) == 0:
            return None
        return winning_ops.idxmax()

    def avg_loss(self, operations):
        """Calculate average loss"""
        losing_ops = operations[operations < 0]
        if len(losing_ops) == 0:
            return 0
        return round(losing_ops.mean(), 2)

    def max_loss(self, operations):
        """Calculate maximum loss"""
        losing_ops = operations[operations < 0]
        if len(losing_ops) == 0:
            return 0
        return round(losing_ops.min(), 2)

    def max_loss_date(self, operations):
        """Get date of maximum loss"""
        losing_ops = operations[operations < 0]
        if len(losing_ops) == 0:
            return None
        return losing_ops.idxmin()

    def reward_risk_ratio(self, operations):
        """Calculate reward/risk ratio"""
        avg_loss_val = self.avg_loss(operations)
        avg_gain_val = self.avg_gain(operations)

        if avg_loss_val != 0:
            return round(avg_gain_val / -avg_loss_val, 2)
        else:
            return np.inf

    # ==================== Visualization Functions ====================

    def plot_equity(self, equity, color='green', title='Equity Line', figsize=(14, 8)):
        """Plot equity curve"""
        plt.figure(figsize=figsize, dpi=300)
        plt.plot(equity, color=color)
        plt.xlabel('Time')
        plt.ylabel('Profit/Loss')
        plt.title(title)
        plt.xticks(rotation='vertical')
        plt.grid(True)
        plt.tight_layout()
        return plt.gcf()

    def plot_drawdown(self, equity, color='red', title='Drawdown', figsize=(12, 6)):
        """Plot drawdown"""
        dd = self.drawdown(equity)
        plt.figure(figsize=figsize, dpi=300)
        plt.plot(dd, color=color)
        plt.fill_between(dd.index, 0, dd, color=color, alpha=0.3)
        plt.xlabel('Time')
        plt.ylabel('Drawdown')
        plt.title(title)
        plt.xticks(rotation='vertical')
        plt.grid(True)
        plt.tight_layout()
        return plt.gcf()

    def plot_double_equity(self, closed_equity, open_equity, figsize=(12, 6)):
        """Plot both closed and open equity curves"""
        plt.figure(figsize=figsize, dpi=300)
        plt.plot(open_equity, color='red', label='Open Equity', alpha=0.7)
        plt.plot(closed_equity, color='green', label='Closed Equity', alpha=0.7)
        plt.xlabel('Time')
        plt.ylabel('Profit/Loss')
        plt.title('Open & Closed Equity')
        plt.legend()
        plt.xticks(rotation='vertical')
        plt.grid(True)
        plt.tight_layout()
        return plt.gcf()

    def plot_annual_histogram(self, operations, figsize=(10, 7)):
        """Plot annual performance histogram"""
        yearly = operations.resample('A').sum()
        colors = yearly.apply(lambda x: 'green' if x > 0 else 'red')

        plt.figure(figsize=figsize, dpi=200)
        bars = plt.bar(range(len(yearly)), yearly.values, color=colors, alpha=0.7)

        plt.xlabel('Years')
        plt.ylabel('Profit/Loss')
        plt.title('Annual Performance')
        plt.xticks(range(len(yearly)), yearly.index.year, rotation=90)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        return plt.gcf()

    def plot_equity_heatmap(self, operations, annotations=False, figsize=(10, 8)):
        """Plot monthly equity heatmap"""
        if not HAS_SEABORN:
            print("Seaborn not available. Cannot create heatmap.")
            return None

        monthly = operations.resample('M').sum()
        toHeatMap = pd.DataFrame(monthly)
        toHeatMap['Year'] = toHeatMap.index.year
        toHeatMap['Month'] = toHeatMap.index.month

        Show = toHeatMap.groupby(by=['Year', 'Month']).sum().unstack()
        Show.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        plt.figure(figsize=figsize, dpi=120)
        max_val = max(abs(monthly.min()), abs(monthly.max()))

        sns.heatmap(Show, cmap='RdYlGn', linecolor='white', linewidth=0.1,
                   annot=annotations, vmin=-max_val, vmax=max_val,
                   center=0, fmt='.0f' if annotations else '')

        plt.title('Monthly Performance Heatmap')
        plt.tight_layout()
        return plt.gcf()

    def plot_trading_signals(self, trading_system, ticker, direction='long',
                            lookback=100, figsize=(14, 8)):
        """
        Plot trading signals on price chart

        Args:
            trading_system: DataFrame with trading system data
            ticker: Stock symbol
            direction: 'long' or 'short'
            lookback: Number of bars to display
            figsize: Figure size tuple

        Returns:
            matplotlib figure
        """
        if not HAS_MPLFINANCE:
            print("mplfinance not available. Using basic plot.")
            return self._plot_trading_signals_basic(trading_system, ticker, direction, lookback, figsize)

        # Take last N bars
        df = trading_system.tail(lookback).copy()

        if df.empty or 'close' not in df.columns or df['close'].dropna().empty:
            print(f"⚠️ Cannot generate chart for {ticker}: insufficient data")
            return None

        # Prepare entry/exit signals
        entry_arrows = np.where(df['events_in'] == 'entry', df['close'], np.nan)
        exit_arrows = np.where(df['events_out'] == 'exit', df['close'], np.nan)

        has_signals = (not np.isnan(entry_arrows).all()) or (not np.isnan(exit_arrows).all())

        addplots = []
        if has_signals:
            if direction == 'long':
                ap_entry = mpf.make_addplot(entry_arrows, scatter=True, markersize=100,
                                           marker='^', color='green')
                ap_exit = mpf.make_addplot(exit_arrows, scatter=True, markersize=100,
                                          marker='v', color='red')
            else:  # short
                ap_entry = mpf.make_addplot(entry_arrows, scatter=True, markersize=100,
                                           marker='v', color='green')
                ap_exit = mpf.make_addplot(exit_arrows, scatter=True, markersize=100,
                                          marker='^', color='red')
            addplots = [ap_entry, ap_exit]
            title_suffix = f'Trading Signals ({direction.upper()})'
        else:
            title_suffix = '(No signals)'

        try:
            fig, axes = mpf.plot(
                df,
                type='candle',
                addplot=addplots if addplots else None,
                volume=False,
                ylabel='Price',
                title=f'{ticker} {title_suffix}',
                style='charles',
                figsize=figsize,
                returnfig=True
            )
            return fig
        except Exception as e:
            print(f"❌ Error creating chart: {e}")
            return None

    def _plot_trading_signals_basic(self, trading_system, ticker, direction, lookback, figsize):
        """Fallback basic plotting without mplfinance"""
        df = trading_system.tail(lookback).copy()

        fig, ax = plt.subplots(figsize=figsize, dpi=150)
        ax.plot(df.index, df['close'], label='Close Price', color='blue', linewidth=1)

        # Plot entry signals
        entry_mask = df['events_in'] == 'entry'
        if entry_mask.any():
            ax.scatter(df.index[entry_mask], df['close'][entry_mask],
                      marker='^' if direction == 'long' else 'v',
                      color='green', s=100, label='Entry', zorder=5)

        # Plot exit signals
        exit_mask = df['events_out'] == 'exit'
        if exit_mask.any():
            ax.scatter(df.index[exit_mask], df['close'][exit_mask],
                      marker='v' if direction == 'long' else '^',
                      color='red', s=100, label='Exit', zorder=5)

        ax.set_xlabel('Time')
        ax.set_ylabel('Price')
        ax.set_title(f'{ticker} Trading Signals ({direction.upper()})')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        return fig

    # ==================== Performance Reports ====================

    def performance_report_console(self, trading_system, operations, closed_equity, open_equity):
        """
        Print comprehensive performance report to console

        Args:
            trading_system: Trading system DataFrame
            operations: Series of completed operations
            closed_equity: Closed equity curve
            open_equity: Open equity curve
        """
        print('=' * 60)
        print('PERFORMANCE REPORT')
        print('=' * 60)
        print()
        print(f'Total Profit:              {self.profit(open_equity):>15,.2f}')
        print(f'Number of Operations:      {self.operation_number(operations):>15}')
        print()
        print(f'Average Trade:             {self.avg_trade(operations):>15,.2f}')
        print()
        print(f'Profit Factor:             {self.profit_factor(operations):>15,.2f}')
        print(f'Gross Profit:              {self.gross_profit(operations):>15,.2f}')
        print(f'Gross Loss:                {self.gross_loss(operations):>15,.2f}')
        print()
        print(f'Winning Trades:            {self.percent_win(operations):>14,.1f}%')
        print(f'Losing Trades:             {100 - self.percent_win(operations):>14,.1f}%')
        print(f'Reward/Risk Ratio:         {self.reward_risk_ratio(operations):>15,.2f}')
        print()
        max_gain_date = self.max_gain_date(operations)
        max_loss_date = self.max_loss_date(operations)
        print(f'Max Gain:                  {self.max_gain(operations):>15,.2f}')
        if max_gain_date:
            print(f'  Date:                    {max_gain_date.strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'Average Gain:              {self.avg_gain(operations):>15,.2f}')
        print()
        print(f'Max Loss:                  {self.max_loss(operations):>15,.2f}')
        if max_loss_date:
            print(f'  Date:                    {max_loss_date.strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'Average Loss:              {self.avg_loss(operations):>15,.2f}')
        print()
        print(f'Avg Open Drawdown:         {self.avg_drawdown_nozero(open_equity):>15,.2f}')
        print(f'Max Open Drawdown:         {self.max_drawdown(open_equity):>15,.2f}')
        print()
        print(f'Avg Closed Drawdown:       {self.avg_drawdown_nozero(closed_equity):>15,.2f}')
        print(f'Max Closed Drawdown:       {self.max_drawdown(closed_equity):>15,.2f}')
        print()
        print(f'Avg Delay Between Peaks:   {self.avg_delay_between_peaks(open_equity):>15,.0f} bars')
        print(f'Max Delay Between Peaks:   {self.max_delay_between_peaks(open_equity):>15,.0f} bars')
        print('=' * 60)

    def performance_report_dict(self, trading_system, operations, closed_equity, open_equity):
        """
        Generate performance report as dictionary

        Returns:
            Dictionary with all performance metrics
        """
        max_gain_date = self.max_gain_date(operations)
        max_loss_date = self.max_loss_date(operations)

        return {
            'profit': self.profit(open_equity),
            'operations': self.operation_number(operations),
            'avg_trade': self.avg_trade(operations),
            'profit_factor': self.profit_factor(operations),
            'gross_profit': self.gross_profit(operations),
            'gross_loss': self.gross_loss(operations),
            'percent_win': self.percent_win(operations),
            'percent_loss': 100 - self.percent_win(operations),
            'reward_risk_ratio': self.reward_risk_ratio(operations),
            'max_gain': self.max_gain(operations),
            'max_gain_date': max_gain_date.strftime("%Y-%m-%d %H:%M:%S") if max_gain_date else None,
            'avg_gain': self.avg_gain(operations),
            'max_loss': self.max_loss(operations),
            'max_loss_date': max_loss_date.strftime("%Y-%m-%d %H:%M:%S") if max_loss_date else None,
            'avg_loss': self.avg_loss(operations),
            'avg_open_drawdown': self.avg_drawdown_nozero(open_equity),
            'max_open_drawdown': self.max_drawdown(open_equity),
            'avg_closed_drawdown': self.avg_drawdown_nozero(closed_equity),
            'max_closed_drawdown': self.max_drawdown(closed_equity),
            'avg_delay_peaks': self.avg_delay_between_peaks(open_equity),
            'max_delay_peaks': self.max_delay_between_peaks(open_equity)
        }

    def save_performance_report_csv(self, ticker, trading_system, operations,
                                   closed_equity, open_equity, output_path):
        """
        Save performance report to CSV file

        Args:
            ticker: Stock symbol
            trading_system: Trading system DataFrame
            operations: Series of operations
            closed_equity: Closed equity curve
            open_equity: Open equity curve
            output_path: Path to save CSV file
        """
        report = self.performance_report_dict(trading_system, operations, closed_equity, open_equity)
        report['ticker'] = ticker

        # Reorder columns
        columns = ['ticker', 'profit', 'operations', 'avg_trade', 'profit_factor',
                  'gross_profit', 'gross_loss', 'percent_win', 'percent_loss',
                  'reward_risk_ratio', 'max_gain', 'max_gain_date', 'avg_gain',
                  'max_loss', 'max_loss_date', 'avg_loss', 'avg_open_drawdown',
                  'max_open_drawdown', 'avg_closed_drawdown', 'max_closed_drawdown',
                  'avg_delay_peaks', 'max_delay_peaks']

        df = pd.DataFrame([report])[columns]
        df.to_csv(output_path, index=False)
        print(f"Performance report saved to: {output_path}")


# Export main class
__all__ = ['PerformanceAnalytics']
