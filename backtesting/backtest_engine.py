"""
Backtest Engine - Testa strategie su dati storici

Simula il trading system su dati storici per valutare performance
prima del deploy in produzione.
"""

import pandas as pd
from datetime import datetime
from loguru import logger
from engine.signal_generator import SignalGenerator
from engine.position_manager import PositionManager
from engine.risk_manager import RiskManager


class BacktestEngine:
    """
    Motore di backtesting per strategie di trading
    """

    def __init__(self, strategy, config, initial_capital=10000):
        """
        Args:
            strategy: Strategia da testare (es. TradingRules)
            config: Dictionary configurazione
            initial_capital: Capitale iniziale per backtest
        """
        self.strategy = strategy
        self.config = config
        self.initial_capital = initial_capital
        self.current_capital = initial_capital

        # Componenti
        self.signal_gen = SignalGenerator(strategy)
        self.position_mgr = PositionManager(config)
        self.risk_mgr = RiskManager(config, initial_capital)

        # Tracking
        self.equity_curve = []
        self.all_trades = []
        self.metrics = {}

        logger.info(f"BacktestEngine inizializzato | Strategia: {strategy.name} | Capital: ${initial_capital}")

    # ========================================================================
    # CORE BACKTEST
    # ========================================================================

    def run(self, data, symbol='BACKTEST'):
        """
        Esegue backtest su dati storici

        Args:
            data: DataFrame con OHLCV + indicatori
            symbol: Nome simbolo (per logging)

        Returns:
            dict: Risultati backtest
        """
        logger.info(f"Avvio backtest su {len(data)} candles | Symbol: {symbol}")

        # Reset state
        self.current_capital = self.initial_capital
        self.equity_curve = []
        self.all_trades = []

        # Simula trading row by row
        for idx, row in data.iterrows():
            self._process_candle(row, symbol)

        # Chiudi tutte le posizioni aperte alla fine
        open_positions = self.position_mgr.get_open_positions()
        if open_positions:
            logger.info(f"Chiusura {len(open_positions)} posizioni aperte a fine backtest")
            for pos in open_positions:
                self._close_position(pos, row, 'backtest_end')

        # Calcola metriche finali
        self.metrics = self._calculate_metrics()

        logger.info(f"Backtest completato | Final capital: ${self.current_capital:.2f}")

        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
            'equity_curve': pd.DataFrame(self.equity_curve),
            'trades': pd.DataFrame(self.all_trades) if self.all_trades else pd.DataFrame(),
            'metrics': self.metrics,
        }

    def _process_candle(self, candle, symbol):
        """
        Processa una singola candle

        Args:
            candle: Row del DataFrame (Series)
            symbol: Symbol name
        """
        # Converti candle in dictionary
        data = candle.to_dict()
        data['symbol'] = symbol

        # 1. Aggiorna posizioni esistenti con prezzo corrente
        current_price = candle['close']
        self.position_mgr.update_positions({symbol: current_price})

        # 2. Controlla exit per posizioni aperte
        open_positions = self.position_mgr.get_open_positions()
        for pos in open_positions:
            # Check TP/SL
            should_close_tpsl, reason_tpsl = self.position_mgr.check_tp_sl(pos)
            if should_close_tpsl:
                self._close_position(pos, candle, reason_tpsl)
                continue

            # Check exit signal dalla strategia
            should_close_signal, reason_signal = self.signal_gen.check_exit_signal(pos, data)
            if should_close_signal:
                self._close_position(pos, candle, reason_signal)

        # 3. Genera nuovo segnale (solo se non abbiamo già posizione su questo symbol)
        if symbol not in self.position_mgr.positions:
            signal = self.signal_gen.generate_signal(data, symbol, open_positions)

            if signal:
                # Valida e apri posizione
                self._open_position(signal, candle)

        # 4. Aggiorna equity curve
        self._update_equity(candle)

    def _open_position(self, signal, candle):
        """
        Apre una posizione nel backtest

        Args:
            signal: Segnale generato
            candle: Candle corrente
        """
        symbol = signal['symbol']

        # Check se possiamo aprire
        can_open, reason = self.position_mgr.can_open_position(symbol)
        if not can_open:
            logger.debug(f"Cannot open position: {reason}")
            return

        # Calcola position sizing
        sizing = self.risk_mgr.calculate_position_size(
            symbol,
            signal['price'],
            self.current_capital
        )

        # Simula commissione
        commission_rate = self.config['backtest'].get('commission', 0.001)
        commission = sizing['position_value'] * commission_rate

        # Simula slippage
        slippage_rate = self.config['backtest'].get('slippage', 0.0005)
        if signal['type'] == 'BUY':
            executed_price = signal['price'] * (1 + slippage_rate)
        else:
            executed_price = signal['price'] * (1 - slippage_rate)

        # Crea fake order info
        order_info = {
            'order_id': f"backtest_{datetime.now().timestamp()}",
            'symbol': symbol,
            'side': signal['type'],
            'quantity': sizing['quantity'],
            'price': executed_price,
            'executed_qty': sizing['quantity'],
            'commission': commission,
            'status': 'FILLED'
        }

        # Apri posizione
        position = self.position_mgr.open_position(signal, order_info)

        # Sottrai da capitale disponibile
        self.current_capital -= (sizing['position_value'] + commission)

        logger.debug(f"Opened {signal['type']} position: {symbol} @ {executed_price:.2f}")

    def _close_position(self, position, candle, reason):
        """
        Chiude una posizione nel backtest

        Args:
            position: Posizione da chiudere
            candle: Candle corrente
            reason: Motivo chiusura
        """
        symbol = position['symbol']
        exit_price = candle['close']

        # Simula slippage
        slippage_rate = self.config['backtest'].get('slippage', 0.0005)
        if position['type'] == 'LONG':
            executed_exit_price = exit_price * (1 - slippage_rate)
        else:
            executed_exit_price = exit_price * (1 + slippage_rate)

        # Simula commissione
        commission_rate = self.config['backtest'].get('commission', 0.001)
        position_value = position['entry_price'] * position['quantity']
        commission = position_value * commission_rate

        # Chiudi posizione
        closed = self.position_mgr.close_position(
            symbol,
            executed_exit_price,
            reason,
            commission
        )

        if closed:
            # Aggiungi capitale dal close
            exit_value = executed_exit_price * position['quantity']
            self.current_capital += exit_value

            # Aggiungi trade a storico
            self.all_trades.append({
                'timestamp': candle['timestamp'],
                'symbol': symbol,
                'type': position['type'],
                'entry_price': position['entry_price'],
                'exit_price': executed_exit_price,
                'quantity': position['quantity'],
                'pnl': closed['realized_pnl'],
                'pnl_pct': (closed['realized_pnl'] / position_value * 100) if position_value > 0 else 0,
                'reason': reason,
                'duration': closed['exit_time'] - closed['entry_time'],
            })

            logger.debug(
                f"Closed {position['type']} position: {symbol} | "
                f"PnL: ${closed['realized_pnl']:.2f} | Reason: {reason}"
            )

    def _update_equity(self, candle):
        """
        Aggiorna equity curve

        Args:
            candle: Candle corrente
        """
        # Calcola unrealized PnL dalle posizioni aperte
        unrealized_pnl = sum(
            pos.get('unrealized_pnl', 0)
            for pos in self.position_mgr.positions.values()
        )

        total_equity = self.current_capital + unrealized_pnl

        self.equity_curve.append({
            'timestamp': candle['timestamp'],
            'equity': total_equity,
            'cash': self.current_capital,
            'unrealized_pnl': unrealized_pnl,
            'num_positions': len(self.position_mgr.positions)
        })

    # ========================================================================
    # METRICS CALCULATION
    # ========================================================================

    def _calculate_metrics(self):
        """
        Calcola metriche di performance

        Returns:
            dict: Metriche
        """
        if not self.all_trades:
            return {
                'total_trades': 0,
                'total_return': 0,
                'total_return_pct': 0,
            }

        trades_df = pd.DataFrame(self.all_trades)

        # Basic metrics
        total_trades = len(trades_df)
        wins = len(trades_df[trades_df['pnl'] > 0])
        losses = len(trades_df[trades_df['pnl'] <= 0])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

        # Returns
        total_return_usd = self.current_capital - self.initial_capital
        total_return_pct = (total_return_usd / self.initial_capital * 100) if self.initial_capital > 0 else 0

        # PnL metrics
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if wins > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] <= 0]['pnl'].mean() if losses > 0 else 0
        best_trade = trades_df['pnl'].max()
        worst_trade = trades_df['pnl'].min()

        # Profit factor
        gross_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(trades_df[trades_df['pnl'] <= 0]['pnl'].sum())
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')

        # Drawdown
        equity_df = pd.DataFrame(self.equity_curve)
        if not equity_df.empty:
            running_max = equity_df['equity'].cummax()
            drawdown = (equity_df['equity'] - running_max) / running_max * 100
            max_drawdown = abs(drawdown.min())
        else:
            max_drawdown = 0

        # Sharpe Ratio (simplified)
        if not equity_df.empty and len(equity_df) > 1:
            returns = equity_df['equity'].pct_change().dropna()
            sharpe_ratio = (returns.mean() / returns.std() * (252 ** 0.5)) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0

        # Average trade duration
        if 'duration' in trades_df.columns:
            avg_duration = trades_df['duration'].mean()
        else:
            avg_duration = pd.Timedelta(0)

        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_return': total_return_usd,
            'total_return_pct': total_return_pct,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_trade_duration': avg_duration,
        }

    # ========================================================================
    # REPORTING
    # ========================================================================

    def print_results(self):
        """Stampa risultati backtest"""
        m = self.metrics

        output = f"""
╔═══════════════════════════════════════════════════════════╗
║                  BACKTEST RESULTS                         ║
╠═══════════════════════════════════════════════════════════╣
║ Strategy:               {self.strategy.name:<30} ║
║                                                           ║
║ CAPITAL                                                   ║
║ Initial:                ${self.initial_capital:>10.2f}                  ║
║ Final:                  ${self.current_capital:>10.2f}                  ║
║ Total Return:           ${m['total_return']:>10.2f} ({m['total_return_pct']:>+6.2f}%)      ║
║                                                           ║
║ TRADES                                                    ║
║ Total:                  {m['total_trades']:>5}                         ║
║ Wins:                   {m['wins']:>5} ({m['win_rate']:>5.1f}%)                  ║
║ Losses:                 {m['losses']:>5}                         ║
║                                                           ║
║ PERFORMANCE                                               ║
║ Profit Factor:          {m['profit_factor']:>6.2f}                        ║
║ Sharpe Ratio:           {m['sharpe_ratio']:>6.2f}                        ║
║ Max Drawdown:           {m['max_drawdown']:>6.2f}%                      ║
║                                                           ║
║ TRADE STATS                                               ║
║ Best Trade:             ${m['best_trade']:>10.2f}                  ║
║ Worst Trade:            ${m['worst_trade']:>10.2f}                  ║
║ Avg Win:                ${m['avg_win']:>10.2f}                  ║
║ Avg Loss:               ${m['avg_loss']:>10.2f}                  ║
╚═══════════════════════════════════════════════════════════╝
        """
        print(output)
        return output
