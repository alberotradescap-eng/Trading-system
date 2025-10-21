"""
Regole di trading - Entry e Exit

Qui definisci le tue strategie di trading in modo semplice e leggibile.
"""

class TradingRules:
    """
    Classe che definisce le regole di entry e exit per il trading.

    Personalizza questi metodi per implementare la tua strategia.
    """

    def __init__(self):
        self.name = "RSI + MACD Strategy"
        self.description = "Entry su RSI oversold/overbought + MACD confirmation"

    # ========================================================================
    # ENTRY RULES - LONG
    # ========================================================================

    def entry_long(self, data):
        """
        Condizioni per entrare in posizione LONG (BUY)

        Args:
            data: Dictionary con indicatori e prezzi
                  - close: prezzo corrente
                  - rsi: RSI
                  - macd: MACD line
                  - signal: MACD signal line
                  - sma_20, sma_50: Simple Moving Averages
                  - volume: volume
                  etc.

        Returns:
            bool: True se le condizioni di entry sono soddisfatte
        """
        return (
            # RSI oversold
            data['rsi'] < 30 and

            # MACD bullish crossover
            data['macd'] > data['signal'] and

            # Prezzo sopra SMA 20 (trend rialzista)
            data['close'] > data['sma_20'] and

            # Volume sopra media (conferma movimento)
            data['volume'] > data['volume_sma_20'] * 1.5
        )

    # ========================================================================
    # ENTRY RULES - SHORT
    # ========================================================================

    def entry_short(self, data):
        """
        Condizioni per entrare in posizione SHORT (SELL)

        Args:
            data: Dictionary con indicatori e prezzi

        Returns:
            bool: True se le condizioni di entry sono soddisfatte
        """
        return (
            # RSI overbought
            data['rsi'] > 70 and

            # MACD bearish crossover
            data['macd'] < data['signal'] and

            # Prezzo sotto SMA 20 (trend ribassista)
            data['close'] < data['sma_20'] and

            # Volume sopra media (conferma movimento)
            data['volume'] > data['volume_sma_20'] * 1.5
        )

    # ========================================================================
    # EXIT RULES - LONG
    # ========================================================================

    def exit_long(self, data, entry_price, entry_time=None):
        """
        Condizioni per uscire da posizione LONG

        Args:
            data: Dictionary con indicatori e prezzi
            entry_price: Prezzo di entrata
            entry_time: Timestamp di entrata (opzionale)

        Returns:
            tuple: (should_exit: bool, reason: str)
                   reason può essere: 'take_profit', 'stop_loss', 'signal', 'time'
        """
        current_price = data['close']
        profit_pct = (current_price - entry_price) / entry_price * 100

        # Take Profit: 2% di profitto
        if profit_pct >= 2.0:
            return True, 'take_profit'

        # Stop Loss: 1% di perdita
        if profit_pct <= -1.0:
            return True, 'stop_loss'

        # Exit su segnale tecnico: RSI overbought
        if data['rsi'] > 75:
            return True, 'signal_rsi_overbought'

        # Exit su MACD bearish crossover
        if data['macd'] < data['signal']:
            return True, 'signal_macd_bearish'

        # Exit se prezzo rompe sotto SMA 50
        if data['close'] < data['sma_50']:
            return True, 'signal_sma_break'

        # Nessuna condizione di exit
        return False, None

    # ========================================================================
    # EXIT RULES - SHORT
    # ========================================================================

    def exit_short(self, data, entry_price, entry_time=None):
        """
        Condizioni per uscire da posizione SHORT

        Args:
            data: Dictionary con indicatori e prezzi
            entry_price: Prezzo di entrata
            entry_time: Timestamp di entrata (opzionale)

        Returns:
            tuple: (should_exit: bool, reason: str)
        """
        current_price = data['close']
        # Per short: profitto quando prezzo scende
        profit_pct = (entry_price - current_price) / entry_price * 100

        # Take Profit: 2% di profitto
        if profit_pct >= 2.0:
            return True, 'take_profit'

        # Stop Loss: 1% di perdita
        if profit_pct <= -1.0:
            return True, 'stop_loss'

        # Exit su segnale tecnico: RSI oversold
        if data['rsi'] < 25:
            return True, 'signal_rsi_oversold'

        # Exit su MACD bullish crossover
        if data['macd'] > data['signal']:
            return True, 'signal_macd_bullish'

        # Exit se prezzo rompe sopra SMA 50
        if data['close'] > data['sma_50']:
            return True, 'signal_sma_break'

        # Nessuna condizione di exit
        return False, None

    # ========================================================================
    # FILTERS (opzionali)
    # ========================================================================

    def can_open_position(self, data, current_positions):
        """
        Filtri aggiuntivi prima di aprire una posizione.

        Args:
            data: Dictionary con indicatori
            current_positions: Lista posizioni attualmente aperte

        Returns:
            tuple: (can_open: bool, reason: str)
        """
        # Non aprire se ATR troppo basso (mercato poco volatile)
        if data.get('atr') and data['atr'] < 0.5:
            return False, 'low_volatility'

        # Non aprire se mercato in consolidamento (Bollinger Bands strette)
        if data.get('bb_upper') and data.get('bb_lower'):
            bb_width = (data['bb_upper'] - data['bb_lower']) / data['close']
            if bb_width < 0.02:  # Meno del 2%
                return False, 'consolidation'

        # Non aprire se ci sono già troppe posizioni aperte
        if len(current_positions) >= 3:
            return False, 'max_positions_reached'

        return True, 'ok'


# ============================================================================
# STRATEGIE ALTERNATIVE (esempi)
# ============================================================================

class MeanReversionStrategy:
    """Strategia Mean Reversion con Bollinger Bands"""

    def __init__(self):
        self.name = "Bollinger Bands Mean Reversion"

    def entry_long(self, data):
        """Entry quando prezzo tocca banda inferiore"""
        return (
            data['close'] < data['bb_lower'] and
            data['rsi'] < 35
        )

    def entry_short(self, data):
        """Entry quando prezzo tocca banda superiore"""
        return (
            data['close'] > data['bb_upper'] and
            data['rsi'] > 65
        )

    def exit_long(self, data, entry_price, entry_time=None):
        """Exit quando prezzo torna a media"""
        if data['close'] > data['sma_20']:
            return True, 'mean_reversion'

        profit_pct = (data['close'] - entry_price) / entry_price * 100
        if profit_pct <= -2.0:
            return True, 'stop_loss'

        return False, None

    def exit_short(self, data, entry_price, entry_time=None):
        """Exit quando prezzo torna a media"""
        if data['close'] < data['sma_20']:
            return True, 'mean_reversion'

        profit_pct = (entry_price - data['close']) / entry_price * 100
        if profit_pct <= -2.0:
            return True, 'stop_loss'

        return False, None


class TrendFollowingStrategy:
    """Strategia Trend Following con multiple SMA"""

    def __init__(self):
        self.name = "Multi-SMA Trend Following"

    def entry_long(self, data):
        """Entry su trend rialzista confermato"""
        return (
            data['sma_20'] > data['sma_50'] and
            data['sma_50'] > data['sma_200'] and
            data['close'] > data['sma_20'] and
            data['rsi'] > 50 and data['rsi'] < 70
        )

    def entry_short(self, data):
        """Entry su trend ribassista confermato"""
        return (
            data['sma_20'] < data['sma_50'] and
            data['sma_50'] < data['sma_200'] and
            data['close'] < data['sma_20'] and
            data['rsi'] < 50 and data['rsi'] > 30
        )

    def exit_long(self, data, entry_price, entry_time=None):
        """Exit quando trend si inverte"""
        if data['close'] < data['sma_50']:
            return True, 'trend_reversal'

        profit_pct = (data['close'] - entry_price) / entry_price * 100
        if profit_pct >= 5.0:
            return True, 'take_profit'
        if profit_pct <= -2.0:
            return True, 'stop_loss'

        return False, None

    def exit_short(self, data, entry_price, entry_time=None):
        """Exit quando trend si inverte"""
        if data['close'] > data['sma_50']:
            return True, 'trend_reversal'

        profit_pct = (entry_price - data['close']) / entry_price * 100
        if profit_pct >= 5.0:
            return True, 'take_profit'
        if profit_pct <= -2.0:
            return True, 'stop_loss'

        return False, None


# ============================================================================
# SELEZIONE STRATEGIA
# ============================================================================

# Scegli quale strategia usare (cambia qui per testare strategie diverse)
ACTIVE_STRATEGY = TradingRules()
# ACTIVE_STRATEGY = MeanReversionStrategy()
# ACTIVE_STRATEGY = TrendFollowingStrategy()
