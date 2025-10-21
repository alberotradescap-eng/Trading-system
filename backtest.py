"""
Backtesting Engine

Testa strategie su dati storici.

Usage:
    python backtest.py --symbol BTCUSDT --start 2024-01-01 --end 2024-12-31
    python backtest.py --symbol ETHUSDT --start 2024-01-01  # end = oggi
"""

import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
import matplotlib.pyplot as plt
import seaborn as sns

from config.trading_rules import ACTIVE_STRATEGY
from config.settings import BACKTEST_CONFIG, CONFIG
from etl.indicator_calculator import IndicatorCalculator
from backtesting.backtest_engine import BacktestEngine as NewBacktestEngine
from backtesting.performance_analyzer import PerformanceAnalyzer
from backtesting.visualizer import BacktestVisualizer


class BacktestEngine:
    """
    Engine per backtesting di strategie
    """

    def __init__(self, strategy, config=None):
        """
        Args:
            strategy: Oggetto strategia con metodi entry_long, exit_long, etc.
            config: Configurazione backtest (default: BACKTEST_CONFIG)
        """
        self.strategy = strategy
        self.config = config or BACKTEST_CONFIG

        self.initial_capital = self.config['initial_capital']
        self.commission = self.config['commission']
        self.slippage = self.config['slippage']

        # Risultati
        self.trades = []
        self.equity_curve = []
        self.positions = []

        logger.info(f"BacktestEngine inizializzato - Strategia: {strategy.name}")

    def load_data(self, filepath):
        """
        Carica dati storici

        Args:
            filepath: Path a file parquet/csv con dati storici
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"File non trovato: {filepath}")

        # Carica dati
        if filepath.suffix == '.parquet':
            df = pd.read_parquet(filepath)
        else:
            df = pd.read_csv(filepath)

        logger.info(f"Caricati {len(df)} records da {filepath}")

        # Assicurati che timestamp sia datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')

        return df

    def prepare_data(self, df):
        """
        Prepara dati calcolando indicatori

        Args:
            df: DataFrame con OHLCV

        Returns:
            DataFrame con indicatori
        """
        logger.info("Calcolo indicatori tecnici...")

        calculator = IndicatorCalculator()

        # Calcola indicatori
        df = calculator.process_file(df) if isinstance(df, str) else df

        # Se indicatori non già presenti, calcolali
        if 'rsi' not in df.columns:
            df['rsi'] = calculator.calculate_rsi(df)
            df['macd'], df['signal'], df['macd_hist'] = calculator.calculate_macd(df)
            df['sma_20'] = calculator.calculate_sma(df, period=20)
            df['sma_50'] = calculator.calculate_sma(df, period=50)
            df['sma_200'] = calculator.calculate_sma(df, period=200)
            df['ema_12'] = calculator.calculate_ema(df, period=12)
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = calculator.calculate_bollinger_bands(df)
            df['atr'] = calculator.calculate_atr(df)
            df['volume_sma_20'] = calculator.calculate_volume_sma(df)

        # Rimuovi NaN
        df = df.dropna()

        logger.info(f"Dati preparati: {len(df)} records con {len(df.columns)} colonne")

        return df

    def run(self, data):
        """
        Esegue backtest

        Args:
            data: DataFrame con OHLCV e indicatori

        Returns:
            Dictionary con risultati
        """
        logger.info("=" * 70)
        logger.info("INIZIO BACKTEST")
        logger.info("=" * 70)

        portfolio_value = self.initial_capital
        self.equity_curve = [portfolio_value]
        self.trades = []
        open_position = None

        position_size_pct = self.config.get('position_size_pct', 2.0)

        # Itera su tutti i dati
        for idx, row in data.iterrows():
            current_data = row.to_dict()

            # Se non c'è posizione aperta, cerca entry
            if open_position is None:
                # Check entry LONG
                if self.strategy.entry_long(current_data):
                    # Calcola size posizione
                    position_size = portfolio_value * (position_size_pct / 100)
                    entry_price = current_data['close'] * (1 + self.slippage)  # Slippage
                    quantity = position_size / entry_price

                    # Commissione
                    commission_cost = position_size * self.commission

                    open_position = {
                        'type': 'LONG',
                        'entry_price': entry_price,
                        'entry_time': current_data['timestamp'],
                        'quantity': quantity,
                        'commission': commission_cost
                    }

                    portfolio_value -= commission_cost

                    logger.debug(f"ENTRY LONG @ {entry_price:.2f} | Size: ${position_size:.2f}")

                # Check entry SHORT (opzionale)
                elif hasattr(self.strategy, 'entry_short') and self.strategy.entry_short(current_data):
                    position_size = portfolio_value * (position_size_pct / 100)
                    entry_price = current_data['close'] * (1 - self.slippage)
                    quantity = position_size / entry_price

                    commission_cost = position_size * self.commission

                    open_position = {
                        'type': 'SHORT',
                        'entry_price': entry_price,
                        'entry_time': current_data['timestamp'],
                        'quantity': quantity,
                        'commission': commission_cost
                    }

                    portfolio_value -= commission_cost

                    logger.debug(f"ENTRY SHORT @ {entry_price:.2f} | Size: ${position_size:.2f}")

            # Se c'è posizione aperta, controlla exit
            else:
                should_exit = False
                exit_reason = None

                if open_position['type'] == 'LONG':
                    should_exit, exit_reason = self.strategy.exit_long(
                        current_data,
                        open_position['entry_price'],
                        open_position['entry_time']
                    )
                elif open_position['type'] == 'SHORT':
                    if hasattr(self.strategy, 'exit_short'):
                        should_exit, exit_reason = self.strategy.exit_short(
                            current_data,
                            open_position['entry_price'],
                            open_position['entry_time']
                        )

                if should_exit:
                    # Chiudi posizione
                    exit_price = current_data['close'] * (1 - self.slippage if open_position['type'] == 'LONG' else 1 + self.slippage)

                    # Calcola PnL
                    if open_position['type'] == 'LONG':
                        pnl = (exit_price - open_position['entry_price']) * open_position['quantity']
                    else:  # SHORT
                        pnl = (open_position['entry_price'] - exit_price) * open_position['quantity']

                    # Sottrai commissione uscita
                    exit_value = exit_price * open_position['quantity']
                    commission_cost = exit_value * self.commission
                    pnl -= commission_cost
                    pnl -= open_position['commission']

                    # Aggiorna portfolio
                    portfolio_value += exit_value + pnl

                    # Salva trade
                    trade = {
                        'type': open_position['type'],
                        'entry_time': open_position['entry_time'],
                        'entry_price': open_position['entry_price'],
                        'exit_time': current_data['timestamp'],
                        'exit_price': exit_price,
                        'quantity': open_position['quantity'],
                        'pnl': pnl,
                        'pnl_pct': (pnl / (open_position['entry_price'] * open_position['quantity'])) * 100,
                        'reason': exit_reason,
                        'duration': current_data['timestamp'] - open_position['entry_time']
                    }

                    self.trades.append(trade)

                    logger.debug(f"EXIT {open_position['type']} @ {exit_price:.2f} | PnL: ${pnl:.2f} ({trade['pnl_pct']:.2f}%) | Reason: {exit_reason}")

                    open_position = None

            # Aggiorna equity curve
            current_equity = portfolio_value
            if open_position:
                # Include unrealized PnL
                current_price = current_data['close']
                if open_position['type'] == 'LONG':
                    unrealized_pnl = (current_price - open_position['entry_price']) * open_position['quantity']
                else:
                    unrealized_pnl = (open_position['entry_price'] - current_price) * open_position['quantity']

                current_equity = portfolio_value + (current_price * open_position['quantity']) + unrealized_pnl

            self.equity_curve.append(current_equity)

        # Chiudi posizione aperta a fine backtest (se presente)
        if open_position:
            logger.warning("Posizione ancora aperta a fine backtest - chiusa forzatamente")
            # TODO: Chiudi posizione

        # Calcola metriche
        results = self._calculate_metrics()

        logger.info("=" * 70)
        logger.info("BACKTEST COMPLETATO")
        logger.info("=" * 70)

        return results

    def _calculate_metrics(self):
        """Calcola metriche di performance"""
        trades_df = pd.DataFrame(self.trades)

        if len(trades_df) == 0:
            logger.warning("Nessun trade eseguito durante il backtest")
            return {}

        # Metriche base
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # PnL
        total_pnl = trades_df['pnl'].sum()
        avg_pnl = trades_df['pnl'].mean()
        best_trade = trades_df['pnl'].max()
        worst_trade = trades_df['pnl'].min()

        # Wins vs Losses
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] < 0]

        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl'].mean() if len(losses) > 0 else 0

        # Profit Factor
        gross_profit = wins['pnl'].sum() if len(wins) > 0 else 0
        gross_loss = abs(losses['pnl'].sum()) if len(losses) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf

        # Return
        final_capital = self.equity_curve[-1]
        total_return = final_capital - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100

        # Sharpe Ratio (semplificato)
        returns = trades_df['pnl_pct']
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0

        # Max Drawdown
        equity_series = pd.Series(self.equity_curve)
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax * 100
        max_drawdown = drawdown.min()

        # Avg Trade Duration
        avg_duration = trades_df['duration'].mean() if 'duration' in trades_df.columns else None

        results = {
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_return': total_return,
            'total_return_pct': total_return_pct,

            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,

            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'best_trade': best_trade,
            'worst_trade': worst_trade,

            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,

            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_trade_duration': avg_duration,

            'trades': trades_df,
            'equity_curve': self.equity_curve
        }

        return results

    def print_results(self, results):
        """Stampa risultati backtest"""
        print("\n" + "=" * 70)
        print("BACKTEST RESULTS")
        print("=" * 70)

        print(f"\nCapital:")
        print(f"  Initial:  ${results['initial_capital']:,.2f}")
        print(f"  Final:    ${results['final_capital']:,.2f}")
        print(f"  Return:   ${results['total_return']:,.2f} ({results['total_return_pct']:.2f}%)")

        print(f"\nTrades:")
        print(f"  Total:    {results['total_trades']}")
        print(f"  Winners:  {results['winning_trades']}")
        print(f"  Losers:   {results['losing_trades']}")
        print(f"  Win Rate: {results['win_rate']:.2f}%")

        print(f"\nPnL:")
        print(f"  Total:       ${results['total_pnl']:,.2f}")
        print(f"  Avg:         ${results['avg_pnl']:,.2f}")
        print(f"  Best Trade:  ${results['best_trade']:,.2f}")
        print(f"  Worst Trade: ${results['worst_trade']:,.2f}")
        print(f"  Avg Win:     ${results['avg_win']:,.2f}")
        print(f"  Avg Loss:    ${results['avg_loss']:,.2f}")

        print(f"\nMetrics:")
        print(f"  Profit Factor:  {results['profit_factor']:.2f}")
        print(f"  Sharpe Ratio:   {results['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown:   {results['max_drawdown']:.2f}%")

        if results['avg_trade_duration']:
            print(f"  Avg Duration:   {results['avg_trade_duration']}")

        print("=" * 70 + "\n")

    def plot_results(self, results, save_path='backtest_results.png'):
        """Genera grafici dei risultati"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Equity Curve
        axes[0, 0].plot(results['equity_curve'], linewidth=2)
        axes[0, 0].set_title('Equity Curve', fontsize=14, fontweight='bold')
        axes[0, 0].set_xlabel('Trades')
        axes[0, 0].set_ylabel('Portfolio Value ($)')
        axes[0, 0].grid(True, alpha=0.3)

        # Drawdown
        equity_series = pd.Series(results['equity_curve'])
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax * 100
        axes[0, 1].fill_between(range(len(drawdown)), drawdown, 0, alpha=0.3, color='red')
        axes[0, 1].set_title('Drawdown', fontsize=14, fontweight='bold')
        axes[0, 1].set_xlabel('Trades')
        axes[0, 1].set_ylabel('Drawdown (%)')
        axes[0, 1].grid(True, alpha=0.3)

        # Trade PnL Distribution
        trades_df = results['trades']
        axes[1, 0].hist(trades_df['pnl'], bins=30, edgecolor='black', alpha=0.7)
        axes[1, 0].axvline(x=0, color='red', linestyle='--', linewidth=2)
        axes[1, 0].set_title('Trade PnL Distribution', fontsize=14, fontweight='bold')
        axes[1, 0].set_xlabel('PnL ($)')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].grid(True, alpha=0.3)

        # Cumulative PnL
        cumulative_pnl = trades_df['pnl'].cumsum()
        axes[1, 1].plot(cumulative_pnl, linewidth=2, color='green')
        axes[1, 1].set_title('Cumulative PnL', fontsize=14, fontweight='bold')
        axes[1, 1].set_xlabel('Trade Number')
        axes[1, 1].set_ylabel('Cumulative PnL ($)')
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Grafici salvati in: {save_path}")

        plt.show()


# ============================================================================
# MAIN
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Backtesting Engine')

    parser.add_argument('--symbol', type=str, required=True, help='Symbol to backtest (es. BTCUSDT)')
    parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD, default: today)')
    parser.add_argument('--interval', type=str, default='5m', help='Timeframe (default: 5m)')
    parser.add_argument('--data-file', type=str, help='Path to data file (overrides symbol/start/end)')

    return parser.parse_args()


def main():
    args = parse_args()

    # Inizializza engine
    engine = BacktestEngine(strategy=ACTIVE_STRATEGY)

    # Carica dati
    if args.data_file:
        data_path = args.data_file
    else:
        # Costruisci path dati storici
        data_path = f"data/backtest/{args.symbol}_{args.interval}_historical.parquet"

    if not Path(data_path).exists():
        logger.error(f"File dati non trovato: {data_path}")
        logger.info("Scarica dati storici con:")
        logger.info(f"  python extractors/download_historical.py --symbol {args.symbol} --start {args.start}")
        return

    data = engine.load_data(data_path)

    # Filtra per date
    if 'timestamp' in data.columns:
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data = data[data['timestamp'] >= args.start]
        if args.end:
            data = data[data['timestamp'] <= args.end]

    # Prepara dati (calcola indicatori)
    data = engine.prepare_data(data)

    # Esegui backtest
    results = engine.run(data)

    # Stampa risultati
    engine.print_results(results)

    # Plot risultati
    engine.plot_results(results)


if __name__ == '__main__':
    main()
