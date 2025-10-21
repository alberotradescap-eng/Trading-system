"""
Performance Analyzer - Analizza performance di backtest

Calcola metriche avanzate e genera report dettagliati.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger


class PerformanceAnalyzer:
    """
    Analizza performance di backtest e genera report
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

        logger.info("PerformanceAnalyzer inizializzato")

    # ========================================================================
    # ADVANCED METRICS
    # ========================================================================

    def calculate_calmar_ratio(self):
        """
        Calmar Ratio = Annual Return / Max Drawdown

        Returns:
            float: Calmar ratio
        """
        annual_return = self.metrics.get('total_return_pct', 0)
        max_drawdown = self.metrics.get('max_drawdown', 1)

        if max_drawdown == 0:
            return 0

        calmar = annual_return / max_drawdown
        return round(calmar, 2)

    def calculate_sortino_ratio(self, risk_free_rate=0.02):
        """
        Sortino Ratio (simile a Sharpe ma usa solo downside deviation)

        Args:
            risk_free_rate: Tasso risk-free annuale

        Returns:
            float: Sortino ratio
        """
        if self.equity_df.empty or len(self.equity_df) < 2:
            return 0

        returns = self.equity_df['equity'].pct_change().dropna()

        # Downside deviation (solo returns negativi)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std()

        if downside_std == 0:
            return 0

        daily_risk_free = risk_free_rate / 252
        sortino = (returns.mean() - daily_risk_free) / downside_std * np.sqrt(252)

        return round(sortino, 2)

    def calculate_recovery_factor(self):
        """
        Recovery Factor = Net Profit / Max Drawdown (in $)

        Returns:
            float: Recovery factor
        """
        net_profit = self.metrics.get('total_return', 0)

        # Max drawdown in dollars
        if not self.equity_df.empty:
            running_max = self.equity_df['equity'].cummax()
            drawdown_dollars = (self.equity_df['equity'] - running_max).min()
            max_dd_dollars = abs(drawdown_dollars)
        else:
            max_dd_dollars = 1

        if max_dd_dollars == 0:
            return 0

        recovery = net_profit / max_dd_dollars
        return round(recovery, 2)

    def calculate_expectancy(self):
        """
        Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)

        Returns:
            float: Expectancy per trade
        """
        if self.trades_df.empty:
            return 0

        win_rate = self.metrics['win_rate'] / 100
        loss_rate = 1 - win_rate
        avg_win = self.metrics['avg_win']
        avg_loss = abs(self.metrics['avg_loss'])

        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        return round(expectancy, 2)

    # ========================================================================
    # TRADE ANALYSIS
    # ========================================================================

    def analyze_trades_by_hour(self):
        """
        Analizza performance per ora del giorno

        Returns:
            DataFrame: Performance per ora
        """
        if self.trades_df.empty:
            return pd.DataFrame()

        trades = self.trades_df.copy()
        trades['hour'] = pd.to_datetime(trades['timestamp']).dt.hour

        hourly_stats = trades.groupby('hour').agg({
            'pnl': ['count', 'sum', 'mean'],
        }).round(2)

        return hourly_stats

    def analyze_trades_by_day_of_week(self):
        """
        Analizza performance per giorno della settimana

        Returns:
            DataFrame: Performance per day of week
        """
        if self.trades_df.empty:
            return pd.DataFrame()

        trades = self.trades_df.copy()
        trades['day_of_week'] = pd.to_datetime(trades['timestamp']).dt.day_name()

        daily_stats = trades.groupby('day_of_week').agg({
            'pnl': ['count', 'sum', 'mean'],
        }).round(2)

        return daily_stats

    def analyze_consecutive_wins_losses(self):
        """
        Analizza sequenze di win/loss consecutive

        Returns:
            dict: {
                'max_consecutive_wins': int,
                'max_consecutive_losses': int,
                'avg_win_streak': float,
                'avg_loss_streak': float
            }
        """
        if self.trades_df.empty:
            return {}

        trades = self.trades_df.copy()
        trades['is_win'] = trades['pnl'] > 0

        # Trova sequenze
        trades['streak'] = (trades['is_win'] != trades['is_win'].shift()).cumsum()

        win_streaks = trades[trades['is_win']].groupby('streak').size()
        loss_streaks = trades[~trades['is_win']].groupby('streak').size()

        return {
            'max_consecutive_wins': int(win_streaks.max()) if len(win_streaks) > 0 else 0,
            'max_consecutive_losses': int(loss_streaks.max()) if len(loss_streaks) > 0 else 0,
            'avg_win_streak': round(win_streaks.mean(), 2) if len(win_streaks) > 0 else 0,
            'avg_loss_streak': round(loss_streaks.mean(), 2) if len(loss_streaks) > 0 else 0,
        }

    # ========================================================================
    # RISK METRICS
    # ========================================================================

    def calculate_value_at_risk(self, confidence=0.95):
        """
        Value at Risk (VaR) - Perdita massima attesa con certa confidenza

        Args:
            confidence: Livello di confidenza (default: 95%)

        Returns:
            float: VaR in $
        """
        if self.trades_df.empty:
            return 0

        returns = self.trades_df['pnl'].values
        var = np.percentile(returns, (1 - confidence) * 100)

        return round(var, 2)

    def calculate_conditional_var(self, confidence=0.95):
        """
        Conditional VaR (CVaR) - Media delle perdite oltre VaR

        Args:
            confidence: Livello di confidenza

        Returns:
            float: CVaR in $
        """
        if self.trades_df.empty:
            return 0

        returns = self.trades_df['pnl'].values
        var_threshold = np.percentile(returns, (1 - confidence) * 100)

        # Prendi solo returns peggiori del VaR
        tail_returns = returns[returns <= var_threshold]

        if len(tail_returns) == 0:
            return var_threshold

        cvar = np.mean(tail_returns)
        return round(cvar, 2)

    # ========================================================================
    # FULL REPORT
    # ========================================================================

    def generate_full_report(self):
        """
        Genera report completo con tutte le metriche

        Returns:
            dict: Report completo
        """
        report = {
            'basic_metrics': self.metrics,
            'advanced_metrics': {
                'calmar_ratio': self.calculate_calmar_ratio(),
                'sortino_ratio': self.calculate_sortino_ratio(),
                'recovery_factor': self.calculate_recovery_factor(),
                'expectancy': self.calculate_expectancy(),
            },
            'risk_metrics': {
                'var_95': self.calculate_value_at_risk(0.95),
                'cvar_95': self.calculate_conditional_var(0.95),
            },
            'streak_analysis': self.analyze_consecutive_wins_losses(),
        }

        return report

    def print_full_report(self):
        """Stampa report completo"""
        report = self.generate_full_report()

        output = f"""
╔═══════════════════════════════════════════════════════════╗
║              DETAILED PERFORMANCE REPORT                  ║
╠═══════════════════════════════════════════════════════════╣
║ BASIC METRICS                                             ║
║ Total Trades:           {report['basic_metrics']['total_trades']:>5}                         ║
║ Win Rate:               {report['basic_metrics']['win_rate']:>6.2f}%                      ║
║ Total Return:           {report['basic_metrics']['total_return_pct']:>+6.2f}%                      ║
║ Profit Factor:          {report['basic_metrics']['profit_factor']:>6.2f}                        ║
║                                                           ║
║ ADVANCED METRICS                                          ║
║ Calmar Ratio:           {report['advanced_metrics']['calmar_ratio']:>6.2f}                        ║
║ Sortino Ratio:          {report['advanced_metrics']['sortino_ratio']:>6.2f}                        ║
║ Recovery Factor:        {report['advanced_metrics']['recovery_factor']:>6.2f}                        ║
║ Expectancy:             ${report['advanced_metrics']['expectancy']:>10.2f}                  ║
║                                                           ║
║ RISK METRICS                                              ║
║ VaR (95%):              ${report['risk_metrics']['var_95']:>10.2f}                  ║
║ CVaR (95%):             ${report['risk_metrics']['cvar_95']:>10.2f}                  ║
║                                                           ║
║ STREAK ANALYSIS                                           ║
║ Max Consecutive Wins:   {report['streak_analysis']['max_consecutive_wins']:>5}                         ║
║ Max Consecutive Losses: {report['streak_analysis']['max_consecutive_losses']:>5}                         ║
╚═══════════════════════════════════════════════════════════╝
        """

        print(output)
        return output

    def export_to_csv(self, filename='backtest_results.csv'):
        """
        Esporta risultati in CSV

        Args:
            filename: Nome file output
        """
        if not self.trades_df.empty:
            self.trades_df.to_csv(filename, index=False)
            logger.info(f"Trades esportati in {filename}")
        else:
            logger.warning("Nessun trade da esportare")
