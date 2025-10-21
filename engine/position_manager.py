"""
Position Manager - Gestisce le posizioni aperte

Tiene traccia di tutte le posizioni attive, calcola PnL,
e gestisce l'apertura/chiusura delle posizioni.
"""

from datetime import datetime
from loguru import logger


class PositionManager:
    """
    Gestisce le posizioni di trading aperte
    """

    def __init__(self, config):
        """
        Args:
            config: Dictionary con configurazione trading
        """
        self.config = config
        self.positions = {}  # {symbol: position_data}
        self.position_history = []  # Storico posizioni chiuse
        self.is_blocked = False  # Blocco per FINAL TP/SL
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.total_trades = 0

        # Statistiche
        self.stats = {
            'wins': 0,
            'losses': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
        }

        logger.info("PositionManager inizializzato")

    # ========================================================================
    # APERTURA POSIZIONI
    # ========================================================================

    def can_open_position(self, symbol):
        """
        Controlla se è possibile aprire una nuova posizione

        Args:
            symbol: Simbolo da tradare

        Returns:
            tuple: (can_open: bool, reason: str)
        """
        # Controlla se sistema è bloccato per FINAL TP/SL
        if self.is_blocked:
            return False, 'system_blocked_final_limit'

        # Controlla se posizione già aperta per questo simbolo
        if symbol in self.positions:
            return False, 'position_already_open'

        # Controlla numero massimo posizioni
        max_positions = self.config['trading'].get('max_positions', 3)
        if len(self.positions) >= max_positions:
            return False, 'max_positions_reached'

        # Controlla numero massimo trade giornalieri
        max_daily_trades = self.config['trading'].get('max_daily_trades', 20)
        if self.daily_trades >= max_daily_trades:
            return False, 'max_daily_trades_reached'

        return True, 'ok'

    def open_position(self, signal, order_info):
        """
        Apre una nuova posizione

        Args:
            signal: Dictionary con segnale generato
            order_info: Dictionary con info ordine eseguito da broker
                {
                    'order_id': str,
                    'symbol': str,
                    'side': 'BUY' o 'SELL',
                    'quantity': float,
                    'price': float,
                    'executed_qty': float,
                    'status': 'FILLED',
                    'commission': float,
                }

        Returns:
            dict: Position data
        """
        symbol = signal['symbol']

        # Determina tipo posizione
        position_type = 'LONG' if signal['type'] == 'BUY' else 'SHORT'

        # Crea posizione
        position = {
            'symbol': symbol,
            'type': position_type,
            'entry_price': order_info['price'],
            'entry_time': datetime.now(),
            'quantity': order_info['executed_qty'],
            'order_id': order_info['order_id'],
            'commission': order_info.get('commission', 0),
            'signal': signal,  # Salva segnale originale

            # TP/SL per questa posizione
            'take_profit_pct': self.config['trading'].get('take_profit_pct', 2.0),
            'stop_loss_pct': self.config['trading'].get('stop_loss_pct', 1.0),

            # Tracking
            'unrealized_pnl': 0.0,
            'realized_pnl': 0.0,
            'current_price': order_info['price'],
            'peak_price': order_info['price'],  # Per trailing stop
            'lowest_price': order_info['price'],
        }

        # Salva posizione
        self.positions[symbol] = position
        self.daily_trades += 1
        self.total_trades += 1

        logger.info(f"✅ Posizione aperta: {symbol} {position_type} @ {position['entry_price']:.2f} qty={position['quantity']}")

        return position

    # ========================================================================
    # CHIUSURA POSIZIONI
    # ========================================================================

    def close_position(self, symbol, exit_price, reason, commission=0):
        """
        Chiude una posizione

        Args:
            symbol: Simbolo da chiudere
            exit_price: Prezzo di uscita
            reason: Motivo chiusura ('take_profit', 'stop_loss', 'signal', etc.)
            commission: Commissione su chiusura

        Returns:
            dict: Posizione chiusa con PnL calcolato
        """
        if symbol not in self.positions:
            logger.warning(f"Tentativo di chiudere posizione inesistente: {symbol}")
            return None

        position = self.positions[symbol]
        position['exit_price'] = exit_price
        position['exit_time'] = datetime.now()
        position['exit_reason'] = reason
        position['exit_commission'] = commission

        # Calcola PnL
        entry_price = position['entry_price']
        quantity = position['quantity']
        total_commission = position['commission'] + commission

        if position['type'] == 'LONG':
            # LONG: profitto se prezzo sale
            pnl = (exit_price - entry_price) * quantity - total_commission
        else:  # SHORT
            # SHORT: profitto se prezzo scende
            pnl = (entry_price - exit_price) * quantity - total_commission

        position['realized_pnl'] = pnl
        pnl_pct = (pnl / (entry_price * quantity)) * 100

        # Aggiorna statistiche
        self.daily_pnl += pnl
        if pnl > 0:
            self.stats['wins'] += 1
            self.stats['total_profit'] += pnl
            if pnl > self.stats['best_trade']:
                self.stats['best_trade'] = pnl
        else:
            self.stats['losses'] += 1
            self.stats['total_loss'] += abs(pnl)
            if pnl < self.stats['worst_trade']:
                self.stats['worst_trade'] = pnl

        # Calcola durata
        duration = position['exit_time'] - position['entry_time']

        logger.info(
            f"🏁 Posizione chiusa: {symbol} {position['type']} | "
            f"Entry: {entry_price:.2f} Exit: {exit_price:.2f} | "
            f"PnL: ${pnl:.2f} ({pnl_pct:+.2f}%) | "
            f"Reason: {reason} | Duration: {duration}"
        )

        # Sposta in history e rimuovi da posizioni attive
        self.position_history.append(position)
        del self.positions[symbol]

        return position

    def close_all_positions(self, current_prices, reason='system_shutdown'):
        """
        Chiude tutte le posizioni aperte

        Args:
            current_prices: Dictionary {symbol: current_price}
            reason: Motivo chiusura

        Returns:
            list: Lista posizioni chiuse
        """
        closed_positions = []

        for symbol in list(self.positions.keys()):
            if symbol in current_prices:
                exit_price = current_prices[symbol]
                closed = self.close_position(symbol, exit_price, reason)
                if closed:
                    closed_positions.append(closed)

        logger.info(f"Chiuse {len(closed_positions)} posizioni. Reason: {reason}")
        return closed_positions

    # ========================================================================
    # UPDATE POSIZIONI
    # ========================================================================

    def update_positions(self, current_prices):
        """
        Aggiorna tutte le posizioni con i prezzi correnti

        Args:
            current_prices: Dictionary {symbol: current_price}
        """
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                self._update_position(position, current_price)

    def _update_position(self, position, current_price):
        """
        Aggiorna una singola posizione

        Args:
            position: Dictionary posizione
            current_price: Prezzo corrente
        """
        position['current_price'] = current_price
        entry_price = position['entry_price']
        quantity = position['quantity']

        # Calcola unrealized PnL
        if position['type'] == 'LONG':
            pnl = (current_price - entry_price) * quantity
        else:  # SHORT
            pnl = (entry_price - current_price) * quantity

        position['unrealized_pnl'] = pnl

        # Aggiorna peak/lowest per trailing stop
        if current_price > position['peak_price']:
            position['peak_price'] = current_price
        if current_price < position['lowest_price']:
            position['lowest_price'] = current_price

    def check_tp_sl(self, position):
        """
        Controlla se una posizione ha raggiunto TP o SL

        Args:
            position: Dictionary posizione

        Returns:
            tuple: (should_close: bool, reason: str)
        """
        current_price = position['current_price']
        entry_price = position['entry_price']

        if position['type'] == 'LONG':
            profit_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            profit_pct = ((entry_price - current_price) / entry_price) * 100

        # Check Take Profit
        if profit_pct >= position['take_profit_pct']:
            return True, 'take_profit'

        # Check Stop Loss
        if profit_pct <= -position['stop_loss_pct']:
            return True, 'stop_loss'

        # Check Trailing Stop (se abilitato)
        if self.config['trading'].get('trailing_stop_enabled', False):
            trailing_pct = self.config['trading'].get('trailing_stop_pct', 0.5)

            if position['type'] == 'LONG':
                # Per LONG: trailing da peak
                drop_from_peak = ((position['peak_price'] - current_price) / position['peak_price']) * 100
                if drop_from_peak >= trailing_pct and profit_pct > 0:
                    return True, 'trailing_stop'
            else:  # SHORT
                # Per SHORT: trailing da lowest
                rise_from_lowest = ((current_price - position['lowest_price']) / position['lowest_price']) * 100
                if rise_from_lowest >= trailing_pct and profit_pct > 0:
                    return True, 'trailing_stop'

        return False, None

    # ========================================================================
    # FINAL TP/SL (GIORNALIERO)
    # ========================================================================

    def check_final_limits(self):
        """
        Controlla se sono stati raggiunti i limiti FINAL giornalieri

        Returns:
            tuple: (is_limit_reached: bool, reason: str)
        """
        if not self.config['trading'].get('final_limits_enabled', True):
            return False, None

        take_profit_final = self.config['trading'].get('take_profit_final', 500)
        stop_loss_final = self.config['trading'].get('stop_loss_final', -200)

        # Check Take Profit FINAL
        if self.daily_pnl >= take_profit_final:
            self.is_blocked = True
            logger.warning(f"🎯 TAKE PROFIT FINAL raggiunto! PnL giornaliero: ${self.daily_pnl:.2f}")
            return True, 'TAKE_PROFIT_FINAL'

        # Check Stop Loss FINAL
        if self.daily_pnl <= stop_loss_final:
            self.is_blocked = True
            logger.warning(f"🛑 STOP LOSS FINAL raggiunto! PnL giornaliero: ${self.daily_pnl:.2f}")
            return True, 'STOP_LOSS_FINAL'

        return False, None

    def unlock_system(self):
        """Sblocca il sistema dopo FINAL TP/SL"""
        if not self.is_blocked:
            logger.info("Sistema già sbloccato")
            return

        logger.info("🔓 SBLOCCO SISTEMA dopo FINAL TP/SL")
        self.is_blocked = False
        self.daily_pnl = 0.0
        self.daily_trades = 0

    def reset_daily_stats(self):
        """Reset statistiche giornaliere (chiamare a fine giornata)"""
        logger.info(f"Reset daily stats. PnL finale giornata: ${self.daily_pnl:.2f}")
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.is_blocked = False

    # ========================================================================
    # STATISTICS & REPORTING
    # ========================================================================

    def get_open_positions(self):
        """
        Ritorna lista posizioni aperte

        Returns:
            list: Lista posizioni
        """
        return list(self.positions.values())

    def get_statistics(self):
        """
        Calcola e ritorna statistiche complete

        Returns:
            dict: Statistiche
        """
        total_trades = self.stats['wins'] + self.stats['losses']
        win_rate = (self.stats['wins'] / total_trades * 100) if total_trades > 0 else 0

        # Calcola profit factor
        profit_factor = (
            self.stats['total_profit'] / self.stats['total_loss']
            if self.stats['total_loss'] > 0 else float('inf')
        )

        return {
            'total_trades': total_trades,
            'daily_trades': self.daily_trades,
            'open_positions': len(self.positions),
            'wins': self.stats['wins'],
            'losses': self.stats['losses'],
            'win_rate': win_rate,
            'daily_pnl': self.daily_pnl,
            'total_profit': self.stats['total_profit'],
            'total_loss': self.stats['total_loss'],
            'net_pnl': self.stats['total_profit'] - self.stats['total_loss'],
            'profit_factor': profit_factor,
            'best_trade': self.stats['best_trade'],
            'worst_trade': self.stats['worst_trade'],
            'avg_win': self.stats['total_profit'] / self.stats['wins'] if self.stats['wins'] > 0 else 0,
            'avg_loss': self.stats['total_loss'] / self.stats['losses'] if self.stats['losses'] > 0 else 0,
            'is_blocked': self.is_blocked,
        }

    def print_summary(self):
        """Stampa sommario posizioni e statistiche"""
        stats = self.get_statistics()

        summary = f"""
╔═══════════════════════════════════════════════════════════╗
║               POSITION MANAGER SUMMARY                    ║
╠═══════════════════════════════════════════════════════════╣
║ Posizioni Aperte:       {stats['open_positions']:>3}                            ║
║ Trade Giornalieri:      {stats['daily_trades']:>3}                            ║
║ PnL Giornaliero:        ${stats['daily_pnl']:>10.2f}                  ║
║                                                           ║
║ Total Trades:           {stats['total_trades']:>3}                            ║
║ Wins:                   {stats['wins']:>3} ({stats['win_rate']:>5.1f}%)                  ║
║ Losses:                 {stats['losses']:>3}                            ║
║                                                           ║
║ Net PnL:                ${stats['net_pnl']:>10.2f}                  ║
║ Profit Factor:          {stats['profit_factor']:>6.2f}                        ║
║ Best Trade:             ${stats['best_trade']:>10.2f}                  ║
║ Worst Trade:            ${stats['worst_trade']:>10.2f}                  ║
║                                                           ║
║ Sistema Bloccato:       {'SÌ' if stats['is_blocked'] else 'NO':>3}                            ║
╚═══════════════════════════════════════════════════════════╝
        """
        print(summary)
        return summary
