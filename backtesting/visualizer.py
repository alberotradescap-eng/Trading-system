"""
Visualizer - Visualizza risultati backtest

Genera grafici e visualizzazioni dei risultati.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from loguru import logger


class BacktestVisualizer:
    """
    Visualizza risultati di backtest
    """

    def __init__(self, backtest_results):
        """
        Args:
            backtest_results: Risultati da BacktestEngine.run()
        """
        self.results = backtest_results
        self.equity_df = backtest_results['equity_curve']
        self.trades_df = backtest_results['trades']
        self.metrics = backtest_results['metrics']

        # Setup matplotlib style
        plt.style.use('seaborn-v0_8-darkgrid')

        logger.info("BacktestVisualizer inizializzato")

    # ========================================================================
    # EQUITY CURVE
    # ========================================================================

    def plot_equity_curve(self, filename='equity_curve.png', show=False):
        """
        Plotta equity curve

        Args:
            filename: Nome file output
            show: True per mostrare plot interattivo
        """
        if self.equity_df.empty:
            logger.warning("Equity curve vuota, impossibile plottare")
            return

        fig, ax = plt.subplots(figsize=(14, 7))

        # Plot equity
        ax.plot(
            self.equity_df['timestamp'],
            self.equity_df['equity'],
            label='Total Equity',
            linewidth=2,
            color='#2E86AB'
        )

        # Plot cash
        ax.plot(
            self.equity_df['timestamp'],
            self.equity_df['cash'],
            label='Cash',
            linewidth=1.5,
            color='#A23B72',
            alpha=0.7
        )

        # Linea iniziale
        ax.axhline(
            y=self.results['initial_capital'],
            color='gray',
            linestyle='--',
            label='Initial Capital',
            alpha=0.5
        )

        # Formatting
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Equity ($)', fontsize=12)
        ax.set_title('Equity Curve', fontsize=16, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        logger.info(f"Equity curve salvata: {filename}")

        if show:
            plt.show()
        else:
            plt.close()

    # ========================================================================
    # DRAWDOWN CHART
    # ========================================================================

    def plot_drawdown(self, filename='drawdown.png', show=False):
        """
        Plotta drawdown chart

        Args:
            filename: Nome file output
            show: True per mostrare plot
        """
        if self.equity_df.empty:
            logger.warning("Equity curve vuota, impossibile plottare drawdown")
            return

        fig, ax = plt.subplots(figsize=(14, 5))

        # Calcola drawdown
        equity = self.equity_df['equity']
        running_max = equity.cummax()
        drawdown = (equity - running_max) / running_max * 100

        # Plot
        ax.fill_between(
            self.equity_df['timestamp'],
            drawdown,
            0,
            color='#E63946',
            alpha=0.5,
            label='Drawdown'
        )
        ax.plot(
            self.equity_df['timestamp'],
            drawdown,
            color='#C1121F',
            linewidth=1.5
        )

        # Formatting
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Drawdown (%)', fontsize=12)
        ax.set_title('Drawdown Chart', fontsize=16, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        logger.info(f"Drawdown chart salvato: {filename}")

        if show:
            plt.show()
        else:
            plt.close()

    # ========================================================================
    # RETURNS DISTRIBUTION
    # ========================================================================

    def plot_returns_distribution(self, filename='returns_distribution.png', show=False):
        """
        Plotta distribuzione dei returns

        Args:
            filename: Nome file output
            show: True per mostrare plot
        """
        if self.trades_df.empty:
            logger.warning("Nessun trade, impossibile plottare distribuzione")
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        # Histogram
        ax.hist(
            self.trades_df['pnl'],
            bins=30,
            color='#06A77D',
            alpha=0.7,
            edgecolor='black'
        )

        # Linea verticale a 0
        ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Break-even')

        # Media
        mean_pnl = self.trades_df['pnl'].mean()
        ax.axvline(x=mean_pnl, color='blue', linestyle='--', linewidth=2, label=f'Mean: ${mean_pnl:.2f}')

        # Formatting
        ax.set_xlabel('PnL ($)', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Trade PnL Distribution', fontsize=16, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        logger.info(f"Returns distribution salvata: {filename}")

        if show:
            plt.show()
        else:
            plt.close()

    # ========================================================================
    # MONTHLY RETURNS HEATMAP
    # ========================================================================

    def plot_monthly_returns(self, filename='monthly_returns.png', show=False):
        """
        Plotta monthly returns heatmap

        Args:
            filename: Nome file output
            show: True per mostrare plot
        """
        if self.trades_df.empty:
            logger.warning("Nessun trade, impossibile plottare monthly returns")
            return

        trades = self.trades_df.copy()
        trades['timestamp'] = pd.to_datetime(trades['timestamp'])
        trades['year'] = trades['timestamp'].dt.year
        trades['month'] = trades['timestamp'].dt.month

        # Aggregazione mensile
        monthly = trades.groupby(['year', 'month'])['pnl'].sum().reset_index()

        # Pivot per heatmap
        pivot = monthly.pivot(index='year', columns='month', values='pnl')

        # Plot
        fig, ax = plt.subplots(figsize=(14, 6))

        cax = ax.matshow(pivot, cmap='RdYlGn', aspect='auto')
        fig.colorbar(cax, label='PnL ($)')

        # Formatting
        ax.set_xticks(range(12))
        ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)

        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Year', fontsize=12)
        ax.set_title('Monthly Returns Heatmap', fontsize=16, fontweight='bold', pad=20)

        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        logger.info(f"Monthly returns heatmap salvata: {filename}")

        if show:
            plt.show()
        else:
            plt.close()

    # ========================================================================
    # COMPREHENSIVE DASHBOARD
    # ========================================================================

    def plot_dashboard(self, filename='backtest_dashboard.png', show=False):
        """
        Crea dashboard completa con multiple visualizzazioni

        Args:
            filename: Nome file output
            show: True per mostrare plot
        """
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        # 1. Equity Curve
        ax1 = fig.add_subplot(gs[0, :])
        if not self.equity_df.empty:
            ax1.plot(self.equity_df['timestamp'], self.equity_df['equity'],
                     linewidth=2, color='#2E86AB', label='Equity')
            ax1.axhline(y=self.results['initial_capital'], color='gray',
                       linestyle='--', alpha=0.5, label='Initial Capital')
            ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Equity ($)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

        # 2. Drawdown
        ax2 = fig.add_subplot(gs[1, :])
        if not self.equity_df.empty:
            equity = self.equity_df['equity']
            running_max = equity.cummax()
            drawdown = (equity - running_max) / running_max * 100
            ax2.fill_between(self.equity_df['timestamp'], drawdown, 0,
                            color='#E63946', alpha=0.5)
            ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Drawdown (%)')
            ax2.grid(True, alpha=0.3)
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        # 3. PnL Distribution
        ax3 = fig.add_subplot(gs[2, 0])
        if not self.trades_df.empty:
            ax3.hist(self.trades_df['pnl'], bins=30, color='#06A77D',
                    alpha=0.7, edgecolor='black')
            ax3.axvline(x=0, color='red', linestyle='--', linewidth=2)
            ax3.set_title('PnL Distribution', fontsize=14, fontweight='bold')
            ax3.set_xlabel('PnL ($)')
            ax3.set_ylabel('Frequency')
            ax3.grid(True, alpha=0.3, axis='y')

        # 4. Win/Loss Pie Chart
        ax4 = fig.add_subplot(gs[2, 1])
        wins = self.metrics.get('wins', 0)
        losses = self.metrics.get('losses', 0)
        if wins + losses > 0:
            ax4.pie([wins, losses], labels=['Wins', 'Losses'],
                   autopct='%1.1f%%', colors=['#06A77D', '#E63946'],
                   startangle=90)
            ax4.set_title(f"Win Rate: {self.metrics.get('win_rate', 0):.1f}%",
                         fontsize=14, fontweight='bold')

        plt.suptitle('Backtest Dashboard', fontsize=18, fontweight='bold', y=0.995)

        plt.savefig(filename, dpi=150, bbox_inches='tight')
        logger.info(f"Dashboard salvata: {filename}")

        if show:
            plt.show()
        else:
            plt.close()

    # ========================================================================
    # GENERATE ALL CHARTS
    # ========================================================================

    def generate_all_charts(self, output_dir='data/backtest/charts/'):
        """
        Genera tutti i grafici disponibili

        Args:
            output_dir: Directory output
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"Generando tutti i grafici in {output_dir}")

        self.plot_equity_curve(f'{output_dir}equity_curve.png')
        self.plot_drawdown(f'{output_dir}drawdown.png')
        self.plot_returns_distribution(f'{output_dir}returns_distribution.png')

        if not self.trades_df.empty:
            self.plot_monthly_returns(f'{output_dir}monthly_returns.png')

        self.plot_dashboard(f'{output_dir}dashboard.png')

        logger.info("Tutti i grafici generati con successo")
