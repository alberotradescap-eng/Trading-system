"""
Signal Generator - Genera segnali di trading

Analizza i dati con indicatori e applica le regole di trading
per generare segnali BUY/SELL.
"""

from datetime import datetime
from loguru import logger


class SignalGenerator:
    """
    Genera segnali di trading basati su regole definite dall'utente
    """

    def __init__(self, strategy):
        """
        Args:
            strategy: Oggetto con metodi entry_long, entry_short, etc.
                     (es. TradingRules da config.trading_rules)
        """
        self.strategy = strategy
        logger.info(f"SignalGenerator inizializzato con strategia: {strategy.name}")

    def generate_signal(self, data, symbol, current_positions=None):
        """
        Genera segnale per un singolo simbolo

        Args:
            data: Dictionary con indicatori (close, rsi, macd, etc.)
            symbol: Simbolo trading (es. 'BTCUSDT')
            current_positions: Lista posizioni aperte (per filtri)

        Returns:
            dict o None: Segnale generato o None se nessun segnale
                {
                    'symbol': 'BTCUSDT',
                    'type': 'BUY' o 'SELL',
                    'price': float,
                    'timestamp': datetime,
                    'reason': 'entry_long' o 'entry_short',
                    'confidence': float (0-1),
                    'indicators': dict
                }
        """
        if current_positions is None:
            current_positions = []

        # Controlla filtri aggiuntivi (se la strategia li implementa)
        if hasattr(self.strategy, 'can_open_position'):
            can_open, reason = self.strategy.can_open_position(data, current_positions)
            if not can_open:
                logger.debug(f"Filtro blocca apertura posizione per {symbol}: {reason}")
                return None

        # Controlla entry LONG
        if self.strategy.entry_long(data):
            signal = {
                'symbol': symbol,
                'type': 'BUY',
                'price': data['close'],
                'timestamp': data.get('timestamp', datetime.now()),
                'reason': 'entry_long',
                'confidence': self._calculate_confidence(data, 'long'),
                'indicators': {
                    'rsi': data.get('rsi'),
                    'macd': data.get('macd'),
                    'signal': data.get('signal'),
                    'sma_20': data.get('sma_20'),
                    'sma_50': data.get('sma_50'),
                    'volume': data.get('volume'),
                    'atr': data.get('atr'),
                }
            }
            logger.info(f"📈 SEGNALE BUY generato per {symbol} @ {signal['price']:.2f}")
            return signal

        # Controlla entry SHORT
        if self.strategy.entry_short(data):
            signal = {
                'symbol': symbol,
                'type': 'SELL',
                'price': data['close'],
                'timestamp': data.get('timestamp', datetime.now()),
                'reason': 'entry_short',
                'confidence': self._calculate_confidence(data, 'short'),
                'indicators': {
                    'rsi': data.get('rsi'),
                    'macd': data.get('macd'),
                    'signal': data.get('signal'),
                    'sma_20': data.get('sma_20'),
                    'sma_50': data.get('sma_50'),
                    'volume': data.get('volume'),
                    'atr': data.get('atr'),
                }
            }
            logger.info(f"📉 SEGNALE SELL generato per {symbol} @ {signal['price']:.2f}")
            return signal

        # Nessun segnale
        return None

    def check_exit_signal(self, position, current_data):
        """
        Controlla se una posizione aperta deve essere chiusa

        Args:
            position: Dictionary con informazioni posizione
                {
                    'symbol': str,
                    'type': 'LONG' o 'SHORT',
                    'entry_price': float,
                    'entry_time': datetime,
                    'quantity': float,
                    ...
                }
            current_data: Dictionary con dati correnti e indicatori

        Returns:
            tuple: (should_exit: bool, reason: str)
        """
        entry_price = position['entry_price']
        entry_time = position.get('entry_time')

        if position['type'] == 'LONG':
            # Usa regole di exit per LONG
            should_exit, reason = self.strategy.exit_long(
                current_data,
                entry_price,
                entry_time
            )
        elif position['type'] == 'SHORT':
            # Usa regole di exit per SHORT
            should_exit, reason = self.strategy.exit_short(
                current_data,
                entry_price,
                entry_time
            )
        else:
            logger.error(f"Tipo posizione sconosciuto: {position['type']}")
            return False, None

        if should_exit:
            logger.info(f"🚪 EXIT signal per {position['symbol']}: {reason}")

        return should_exit, reason

    def _calculate_confidence(self, data, direction):
        """
        Calcola livello di confidenza del segnale (0-1)

        Più indicatori confermano il segnale, maggiore la confidenza.

        Args:
            data: Dictionary con indicatori
            direction: 'long' o 'short'

        Returns:
            float: Confidence score (0-1)
        """
        confidence = 0.5  # Base confidence
        checks = 0
        confirmations = 0

        if direction == 'long':
            # Controlla vari indicatori per LONG
            if data.get('rsi') is not None:
                checks += 1
                if data['rsi'] < 40:  # Oversold
                    confirmations += 1

            if data.get('macd') is not None and data.get('signal') is not None:
                checks += 1
                if data['macd'] > data['signal']:  # Bullish
                    confirmations += 1

            if data.get('close') and data.get('sma_50'):
                checks += 1
                if data['close'] > data['sma_50']:  # Sopra media
                    confirmations += 1

            if data.get('volume') and data.get('volume_sma_20'):
                checks += 1
                if data['volume'] > data['volume_sma_20']:  # Volume alto
                    confirmations += 1

        elif direction == 'short':
            # Controlla vari indicatori per SHORT
            if data.get('rsi') is not None:
                checks += 1
                if data['rsi'] > 60:  # Overbought
                    confirmations += 1

            if data.get('macd') is not None and data.get('signal') is not None:
                checks += 1
                if data['macd'] < data['signal']:  # Bearish
                    confirmations += 1

            if data.get('close') and data.get('sma_50'):
                checks += 1
                if data['close'] < data['sma_50']:  # Sotto media
                    confirmations += 1

            if data.get('volume') and data.get('volume_sma_20'):
                checks += 1
                if data['volume'] > data['volume_sma_20']:  # Volume alto
                    confirmations += 1

        # Calcola confidence finale
        if checks > 0:
            confidence = confirmations / checks

        return round(confidence, 2)

    def generate_signals_batch(self, data_dict, current_positions=None):
        """
        Genera segnali per multipli simboli in batch

        Args:
            data_dict: Dictionary {symbol: data_with_indicators}
            current_positions: Lista posizioni aperte

        Returns:
            list: Lista di segnali generati
        """
        signals = []

        for symbol, data in data_dict.items():
            signal = self.generate_signal(data, symbol, current_positions)
            if signal:
                signals.append(signal)

        if signals:
            logger.info(f"Generati {len(signals)} segnali totali")

        return signals

    def get_signal_summary(self, signal):
        """
        Crea un sommario leggibile del segnale per logging/notifiche

        Args:
            signal: Dictionary segnale

        Returns:
            str: Sommario formattato
        """
        summary = f"""
🎯 NUOVO SEGNALE
━━━━━━━━━━━━━━━━━━━━━━━━━━
Symbol:     {signal['symbol']}
Type:       {signal['type']}
Price:      ${signal['price']:.2f}
Confidence: {signal['confidence']*100:.0f}%
Reason:     {signal['reason']}

Indicatori:
  RSI:      {signal['indicators'].get('rsi', 'N/A')}
  MACD:     {signal['indicators'].get('macd', 'N/A')}
  Signal:   {signal['indicators'].get('signal', 'N/A')}
  Volume:   {signal['indicators'].get('volume', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        return summary.strip()
