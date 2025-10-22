"""
ETL - Indicator Calculator

Carica dati da data/raw/ e calcola indicatori tecnici.
Salva i risultati in data/processed/
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger

# Nota: Potresti usare librerie come ta-lib, pandas-ta, o ta
# Qui implementiamo alcuni indicatori base manualmente


class IndicatorCalculator:
    """
    Calcola indicatori tecnici su dati OHLCV
    """

    def __init__(self, input_dir='data/raw/klines', output_dir='data/processed/indicators'):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # MOVING AVERAGES
    # ========================================================================

    @staticmethod
    def calculate_sma(data, period=20, column='close'):
        """Simple Moving Average"""
        return data[column].rolling(window=period).mean()

    @staticmethod
    def calculate_ema(data, period=12, column='close'):
        """Exponential Moving Average"""
        return data[column].ewm(span=period, adjust=False).mean()

    # ========================================================================
    # RSI (Relative Strength Index)
    # ========================================================================

    @staticmethod
    def calculate_rsi(data, period=14, column='close'):
        """
        RSI - Relative Strength Index

        Returns:
            Series: RSI values (0-100)
        """
        delta = data[column].diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    # ========================================================================
    # MACD (Moving Average Convergence Divergence)
    # ========================================================================

    @staticmethod
    def calculate_macd(data, fast=12, slow=26, signal=9, column='close'):
        """
        MACD indicator

        Returns:
            tuple: (macd_line, signal_line, histogram)
        """
        ema_fast = data[column].ewm(span=fast, adjust=False).mean()
        ema_slow = data[column].ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    # ========================================================================
    # BOLLINGER BANDS
    # ========================================================================

    @staticmethod
    def calculate_bollinger_bands(data, period=20, std_dev=2, column='close'):
        """
        Bollinger Bands

        Returns:
            tuple: (upper_band, middle_band, lower_band)
        """
        middle_band = data[column].rolling(window=period).mean()
        std = data[column].rolling(window=period).std()

        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)

        return upper_band, middle_band, lower_band

    # ========================================================================
    # ATR (Average True Range)
    # ========================================================================

    @staticmethod
    def calculate_atr(data, period=14):
        """
        ATR - Average True Range (misura volatilità)

        Returns:
            Series: ATR values
        """
        high = data['high']
        low = data['low']
        close = data['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    # ========================================================================
    # STOCHASTIC OSCILLATOR
    # ========================================================================

    @staticmethod
    def calculate_stochastic(data, k_period=14, d_period=3):
        """
        Stochastic Oscillator

        Returns:
            tuple: (%K, %D)
        """
        low_min = data['low'].rolling(window=k_period).min()
        high_max = data['high'].rolling(window=k_period).max()

        k = 100 * (data['close'] - low_min) / (high_max - low_min)
        d = k.rolling(window=d_period).mean()

        return k, d

    # ========================================================================
    # VOLUME INDICATORS
    # ========================================================================

    @staticmethod
    def calculate_volume_sma(data, period=20):
        """Volume Simple Moving Average"""
        return data['volume'].rolling(window=period).mean()

    @staticmethod
    def calculate_obv(data):
        """
        OBV - On Balance Volume

        Returns:
            Series: OBV values
        """
        obv = (np.sign(data['close'].diff()) * data['volume']).fillna(0).cumsum()
        return obv

    # ========================================================================
    # SUPERTREND & ADAPTIVE SUPERTREND
    # ========================================================================

    @staticmethod
    def calculate_supertrend(data, period=10, multiplier=3.0):
        """
        SuperTrend Indicator

        Args:
            data: DataFrame with OHLC data
            period: ATR period (default 10)
            multiplier: ATR multiplier (default 3.0)

        Returns:
            tuple: (supertrend, direction)
                   - supertrend: Series with SuperTrend values
                   - direction: Series with 1 (uptrend) or -1 (downtrend)
        """
        # Calculate ATR
        atr = IndicatorCalculator.calculate_atr(data, period=period)

        # Calculate basic bands
        hl_avg = (data['high'] + data['low']) / 2
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)

        # Initialize arrays
        supertrend = pd.Series(index=data.index, dtype=float)
        direction = pd.Series(index=data.index, dtype=int)

        # Calculate SuperTrend
        for i in range(len(data)):
            if i == 0:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = 1
                continue

            # Adjust bands
            if lower_band.iloc[i] > supertrend.iloc[i-1] or data['close'].iloc[i-1] < supertrend.iloc[i-1]:
                final_lower = lower_band.iloc[i]
            else:
                final_lower = max(lower_band.iloc[i], supertrend.iloc[i-1])

            if upper_band.iloc[i] < supertrend.iloc[i-1] or data['close'].iloc[i-1] > supertrend.iloc[i-1]:
                final_upper = upper_band.iloc[i]
            else:
                final_upper = min(upper_band.iloc[i], supertrend.iloc[i-1])

            # Determine trend direction
            if data['close'].iloc[i] > final_upper:
                supertrend.iloc[i] = final_lower
                direction.iloc[i] = 1  # Uptrend
            elif data['close'].iloc[i] < final_lower:
                supertrend.iloc[i] = final_upper
                direction.iloc[i] = -1  # Downtrend
            else:
                supertrend.iloc[i] = supertrend.iloc[i-1]
                direction.iloc[i] = direction.iloc[i-1]

        return supertrend, direction

    @staticmethod
    def calculate_adaptive_supertrend(data, atr_period=10, factor_base=3.0,
                                     adaptive_period=14, sensitivity=1.0):
        """
        Adaptive SuperTrend - adjusts multiplier based on market volatility

        The adaptive version dynamically adjusts the ATR multiplier based on
        recent price volatility, making it more responsive to market conditions.

        Args:
            data: DataFrame with OHLC data
            atr_period: Period for ATR calculation (default 10)
            factor_base: Base multiplier for ATR (default 3.0)
            adaptive_period: Period for volatility adaptation (default 14)
            sensitivity: Sensitivity factor for adaptation (default 1.0)

        Returns:
            tuple: (supertrend, direction, multiplier_series, entry_long, entry_short, exit_long, exit_short)
        """
        # Calculate ATR
        atr = IndicatorCalculator.calculate_atr(data, period=atr_period)

        # Calculate adaptive multiplier based on price volatility
        close_std = data['close'].rolling(window=adaptive_period).std()
        close_mean = data['close'].rolling(window=adaptive_period).mean()
        volatility_ratio = (close_std / close_mean).fillna(1.0)

        # Adjust multiplier: higher volatility = higher multiplier
        adaptive_multiplier = factor_base * (1 + sensitivity * volatility_ratio)

        # Calculate basic bands with adaptive multiplier
        hl_avg = (data['high'] + data['low']) / 2
        upper_band = hl_avg + (adaptive_multiplier * atr)
        lower_band = hl_avg - (adaptive_multiplier * atr)

        # Initialize arrays
        supertrend = pd.Series(index=data.index, dtype=float)
        direction = pd.Series(index=data.index, dtype=int)

        # Calculate Adaptive SuperTrend
        for i in range(len(data)):
            if i == 0:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = 1
                continue

            # Adjust bands with trend logic
            if lower_band.iloc[i] > supertrend.iloc[i-1] or data['close'].iloc[i-1] < supertrend.iloc[i-1]:
                final_lower = lower_band.iloc[i]
            else:
                final_lower = max(lower_band.iloc[i], supertrend.iloc[i-1])

            if upper_band.iloc[i] < supertrend.iloc[i-1] or data['close'].iloc[i-1] > supertrend.iloc[i-1]:
                final_upper = upper_band.iloc[i]
            else:
                final_upper = min(upper_band.iloc[i], supertrend.iloc[i-1])

            # Determine trend direction
            if data['close'].iloc[i] > final_upper:
                supertrend.iloc[i] = final_lower
                direction.iloc[i] = 1  # Uptrend
            elif data['close'].iloc[i] < final_lower:
                supertrend.iloc[i] = final_upper
                direction.iloc[i] = -1  # Downtrend
            else:
                supertrend.iloc[i] = supertrend.iloc[i-1]
                direction.iloc[i] = direction.iloc[i-1]

        # Generate trading signals
        entry_long = pd.Series(False, index=data.index)
        entry_short = pd.Series(False, index=data.index)
        exit_long = pd.Series(False, index=data.index)
        exit_short = pd.Series(False, index=data.index)

        for i in range(1, len(data)):
            # Long entry: direction changes from -1 to 1
            if direction.iloc[i] == 1 and direction.iloc[i-1] == -1:
                entry_long.iloc[i] = True

            # Short entry: direction changes from 1 to -1
            if direction.iloc[i] == -1 and direction.iloc[i-1] == 1:
                entry_short.iloc[i] = True

            # Long exit: currently in uptrend but price crosses below supertrend
            if direction.iloc[i] == -1 and direction.iloc[i-1] == 1:
                exit_long.iloc[i] = True

            # Short exit: currently in downtrend but price crosses above supertrend
            if direction.iloc[i] == 1 and direction.iloc[i-1] == -1:
                exit_short.iloc[i] = True

        return supertrend, direction, adaptive_multiplier, entry_long, entry_short, exit_long, exit_short

    # ========================================================================
    # MAIN PROCESSING
    # ========================================================================

    def process_file(self, filepath, config=None):
        """
        Processa un file CSV di klines e calcola tutti gli indicatori

        Args:
            filepath: Path al file CSV
            config: Configurazione indicatori (da config.settings)

        Returns:
            DataFrame con indicatori calcolati
        """
        logger.info(f"Processing file: {filepath}")

        # Carica dati
        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Calcola indicatori base
        logger.debug("Calcolando SMA...")
        df['sma_20'] = self.calculate_sma(df, period=20)
        df['sma_50'] = self.calculate_sma(df, period=50)
        df['sma_200'] = self.calculate_sma(df, period=200)

        logger.debug("Calcolando EMA...")
        df['ema_12'] = self.calculate_ema(df, period=12)
        df['ema_26'] = self.calculate_ema(df, period=26)

        logger.debug("Calcolando RSI...")
        df['rsi'] = self.calculate_rsi(df, period=14)

        logger.debug("Calcolando MACD...")
        df['macd'], df['signal'], df['macd_hist'] = self.calculate_macd(df)

        logger.debug("Calcolando Bollinger Bands...")
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.calculate_bollinger_bands(df)

        logger.debug("Calcolando ATR...")
        df['atr'] = self.calculate_atr(df, period=14)

        logger.debug("Calcolando Stochastic...")
        df['stoch_k'], df['stoch_d'] = self.calculate_stochastic(df)

        logger.debug("Calcolando Volume indicators...")
        df['volume_sma_20'] = self.calculate_volume_sma(df, period=20)
        df['obv'] = self.calculate_obv(df)

        logger.debug("Calcolando Adaptive SuperTrend...")
        (df['adaptive_supertrend'],
         df['adaptive_supertrend_direction'],
         df['adaptive_multiplier'],
         df['adapt_supertrend_entry_long'],
         df['adapt_supertrend_entry_short'],
         df['adapt_supertrend_exit_long'],
         df['adapt_supertrend_exit_short']) = self.calculate_adaptive_supertrend(
            df,
            atr_period=10,
            factor_base=3.0,
            adaptive_period=14,
            sensitivity=1.0
        )

        # Rimuovi NaN (prime righe dove indicatori non sono calcolabili)
        df = df.dropna()

        logger.info(f"Processate {len(df)} righe con {len(df.columns)} colonne")

        return df

    def process_and_save(self, input_file, output_file=None):
        """
        Processa un file e salva il risultato

        Args:
            input_file: Path file input
            output_file: Path file output (opzionale)
        """
        df = self.process_file(input_file)

        if output_file is None:
            # Genera nome output
            input_path = Path(input_file)
            output_file = self.output_dir / f"{input_path.stem}_processed.parquet"

        # Salva
        df.to_parquet(output_file)
        logger.info(f"Salvato file processato: {output_file}")

        return df

    def process_directory(self, input_dir=None):
        """
        Processa tutti i file CSV in una directory

        Args:
            input_dir: Directory input (default: self.input_dir)
        """
        if input_dir is None:
            input_dir = self.input_dir

        input_dir = Path(input_dir)
        csv_files = list(input_dir.glob('*.csv'))

        logger.info(f"Trovati {len(csv_files)} file da processare")

        for csv_file in csv_files:
            try:
                self.process_and_save(csv_file)
            except Exception as e:
                logger.error(f"Errore processing {csv_file}: {e}")

    # ========================================================================
    # REAL-TIME PROCESSING
    # ========================================================================

    def calculate_indicators_realtime(self, latest_data, window_size=200):
        """
        Calcola indicatori su dati realtime (ultimi N candles)

        Args:
            latest_data: DataFrame con ultimi dati OHLCV
            window_size: Numero di candles da usare per calcolo

        Returns:
            dict: Dictionary con ultimi valori degli indicatori
        """
        # Prendi ultimi N records
        df = latest_data.tail(window_size).copy()

        # Calcola indicatori
        df['sma_20'] = self.calculate_sma(df, period=20)
        df['sma_50'] = self.calculate_sma(df, period=50)
        df['rsi'] = self.calculate_rsi(df, period=14)
        df['macd'], df['signal'], _ = self.calculate_macd(df)
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.calculate_bollinger_bands(df)
        df['atr'] = self.calculate_atr(df)
        df['volume_sma_20'] = self.calculate_volume_sma(df)

        # Calculate Adaptive SuperTrend
        (df['adaptive_supertrend'],
         df['adaptive_supertrend_direction'],
         df['adaptive_multiplier'],
         df['adapt_supertrend_entry_long'],
         df['adapt_supertrend_entry_short'],
         df['adapt_supertrend_exit_long'],
         df['adapt_supertrend_exit_short']) = self.calculate_adaptive_supertrend(df)

        # Prendi ultimo valore (più recente)
        last = df.iloc[-1]

        return {
            'timestamp': last['timestamp'],
            'close': last['close'],
            'volume': last['volume'],
            'sma_20': last['sma_20'],
            'sma_50': last['sma_50'],
            'rsi': last['rsi'],
            'macd': last['macd'],
            'signal': last['signal'],
            'bb_upper': last['bb_upper'],
            'bb_middle': last['bb_middle'],
            'bb_lower': last['bb_lower'],
            'atr': last['atr'],
            'volume_sma_20': last['volume_sma_20'],
            'adaptive_supertrend': last['adaptive_supertrend'],
            'adaptive_supertrend_direction': last['adaptive_supertrend_direction'],
            'adapt_supertrend_entry_long': last['adapt_supertrend_entry_long'],
            'adapt_supertrend_entry_short': last['adapt_supertrend_entry_short'],
            'adapt_supertrend_exit_long': last['adapt_supertrend_exit_long'],
            'adapt_supertrend_exit_short': last['adapt_supertrend_exit_short'],
        }


# ============================================================================
# ESEMPIO DI UTILIZZO
# ============================================================================

if __name__ == '__main__':
    calculator = IndicatorCalculator()

    # Processa tutti i file in data/raw/klines
    calculator.process_directory()

    # Oppure processa singolo file
    # calculator.process_and_save('data/raw/klines/BTCUSDT_1m_20240101.csv')
