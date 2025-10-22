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


class AdaptiveSupertrendStrategy:
    """
    Strategia basata su Adaptive SuperTrend

    L'Adaptive SuperTrend si adatta dinamicamente alla volatilità del mercato,
    fornendo segnali più affidabili in diverse condizioni di mercato.

    Features:
    - Entry automatici su cambio di trend
    - Exit su inversione di trend
    - Stop loss e take profit configurabili
    - Filtri opzionali su volume e volatilità
    """

    def __init__(self, stop_loss_pct=2.0, take_profit_pct=4.0,
                 use_volume_filter=True, use_volatility_filter=True):
        self.name = "Adaptive SuperTrend Strategy"
        self.description = "Trend following with adaptive volatility adjustment"
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.use_volume_filter = use_volume_filter
        self.use_volatility_filter = use_volatility_filter

    def entry_long(self, data):
        """
        Entry LONG quando Adaptive SuperTrend segnala uptrend

        Condizioni:
        - Adaptive SuperTrend genera segnale entry_long
        - Prezzo sopra SuperTrend line
        - (Opzionale) Volume conforme
        - (Opzionale) Volatilità adeguata
        """
        # Segnale primario: Adaptive SuperTrend entry long
        primary_signal = data.get('adapt_supertrend_entry_long', False)

        if not primary_signal:
            return False

        # Conferma: prezzo in uptrend
        trend_confirm = (
            data.get('adaptive_supertrend_direction', 0) == 1 and
            data['close'] > data.get('adaptive_supertrend', data['close'])
        )

        # Filtro volume (opzionale)
        volume_ok = True
        if self.use_volume_filter and 'volume_sma_20' in data:
            volume_ok = data['volume'] > data['volume_sma_20'] * 0.8

        # Filtro volatilità (opzionale)
        volatility_ok = True
        if self.use_volatility_filter and 'atr' in data:
            # ATR non troppo basso (mercato non troppo piatto)
            atr_pct = (data['atr'] / data['close']) * 100
            volatility_ok = atr_pct > 0.3  # Almeno 0.3% di volatilità

        return primary_signal and trend_confirm and volume_ok and volatility_ok

    def entry_short(self, data):
        """
        Entry SHORT quando Adaptive SuperTrend segnala downtrend

        Condizioni:
        - Adaptive SuperTrend genera segnale entry_short
        - Prezzo sotto SuperTrend line
        - (Opzionale) Volume conforme
        - (Opzionale) Volatilità adeguata
        """
        # Segnale primario: Adaptive SuperTrend entry short
        primary_signal = data.get('adapt_supertrend_entry_short', False)

        if not primary_signal:
            return False

        # Conferma: prezzo in downtrend
        trend_confirm = (
            data.get('adaptive_supertrend_direction', 0) == -1 and
            data['close'] < data.get('adaptive_supertrend', data['close'])
        )

        # Filtro volume (opzionale)
        volume_ok = True
        if self.use_volume_filter and 'volume_sma_20' in data:
            volume_ok = data['volume'] > data['volume_sma_20'] * 0.8

        # Filtro volatilità (opzionale)
        volatility_ok = True
        if self.use_volatility_filter and 'atr' in data:
            # ATR non troppo basso
            atr_pct = (data['atr'] / data['close']) * 100
            volatility_ok = atr_pct > 0.3

        return primary_signal and trend_confirm and volume_ok and volatility_ok

    def exit_long(self, data, entry_price, entry_time=None):
        """
        Exit da posizione LONG

        Condizioni:
        1. Adaptive SuperTrend segnala exit_long (inversione trend)
        2. Take profit raggiunto
        3. Stop loss hit
        4. Trend si indebolisce (prezzo cross sotto SuperTrend)
        """
        current_price = data['close']
        profit_pct = (current_price - entry_price) / entry_price * 100

        # 1. Segnale SuperTrend exit
        if data.get('adapt_supertrend_exit_long', False):
            return True, 'supertrend_exit_signal'

        # 2. Take Profit
        if profit_pct >= self.take_profit_pct:
            return True, 'take_profit'

        # 3. Stop Loss
        if profit_pct <= -self.stop_loss_pct:
            return True, 'stop_loss'

        # 4. Trend reversal: direction cambia o prezzo cross sotto
        if data.get('adaptive_supertrend_direction', 1) == -1:
            return True, 'trend_reversal'

        if data['close'] < data.get('adaptive_supertrend', 0):
            return True, 'price_cross_below'

        # Nessuna condizione di exit
        return False, None

    def exit_short(self, data, entry_price, entry_time=None):
        """
        Exit da posizione SHORT

        Condizioni:
        1. Adaptive SuperTrend segnala exit_short (inversione trend)
        2. Take profit raggiunto
        3. Stop loss hit
        4. Trend si indebolisce (prezzo cross sopra SuperTrend)
        """
        current_price = data['close']
        # Per short: profitto quando prezzo scende
        profit_pct = (entry_price - current_price) / entry_price * 100

        # 1. Segnale SuperTrend exit
        if data.get('adapt_supertrend_exit_short', False):
            return True, 'supertrend_exit_signal'

        # 2. Take Profit
        if profit_pct >= self.take_profit_pct:
            return True, 'take_profit'

        # 3. Stop Loss
        if profit_pct <= -self.stop_loss_pct:
            return True, 'stop_loss'

        # 4. Trend reversal: direction cambia o prezzo cross sopra
        if data.get('adaptive_supertrend_direction', -1) == 1:
            return True, 'trend_reversal'

        if data['close'] > data.get('adaptive_supertrend', float('inf')):
            return True, 'price_cross_above'

        # Nessuna condizione di exit
        return False, None

    def can_open_position(self, data, current_positions):
        """
        Filtri aggiuntivi prima di aprire una posizione

        Args:
            data: Dictionary con indicatori
            current_positions: Lista posizioni aperte

        Returns:
            tuple: (can_open: bool, reason: str)
        """
        # Non aprire se ATR troppo basso (mercato troppo piatto)
        if data.get('atr'):
            atr_pct = (data['atr'] / data['close']) * 100
            if atr_pct < 0.2:
                return False, 'extremely_low_volatility'

        # Non aprire se troppe posizioni aperte
        if len(current_positions) >= 3:
            return False, 'max_positions_reached'

        # Non aprire se RSI in zona estrema (overbought/oversold)
        if data.get('rsi'):
            if data['rsi'] > 85 or data['rsi'] < 15:
                return False, 'rsi_extreme'

        return True, 'ok'


# ============================================================================
# SELEZIONE STRATEGIA
# ============================================================================

# Scegli quale strategia usare (cambia qui per testare strategie diverse)
# ACTIVE_STRATEGY = TradingRules()
# ACTIVE_STRATEGY = MeanReversionStrategy()
# ACTIVE_STRATEGY = TrendFollowingStrategy()

# Strategia ATTIVA: Adaptive SuperTrend
ACTIVE_STRATEGY = AdaptiveSupertrendStrategy(
    stop_loss_pct=2.0,           # Stop loss al 2%
    take_profit_pct=4.0,          # Take profit al 4%
    use_volume_filter=True,       # Abilita filtro volume
    use_volatility_filter=True    # Abilita filtro volatilità
)
