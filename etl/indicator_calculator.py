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
    # ADAPTIVE SUPERTREND
    # ========================================================================

    @staticmethod
    def _kmeans_volatility_clustering(atr_series, training_period=100, max_iterations=20):
        """
        Classifica la volatilità (ATR) in 3 cluster usando K-Means custom

        Args:
            atr_series: Series con valori ATR
            training_period: Numero di periodi per training window
            max_iterations: Max iterazioni K-Means per convergenza

        Returns:
            tuple: (low_centroid, mid_centroid, high_centroid, cluster_index)
                   cluster_index è una Series con valori 0 (low), 1 (mid), 2 (high)
        """
        result_low = pd.Series(index=atr_series.index, dtype=float)
        result_mid = pd.Series(index=atr_series.index, dtype=float)
        result_high = pd.Series(index=atr_series.index, dtype=float)
        result_cluster_idx = pd.Series(index=atr_series.index, dtype=float)

        for i in range(len(atr_series)):
            if i < training_period - 1:
                continue

            # Finestra di training
            window_start = i - training_period + 1
            window = atr_series.iloc[window_start:i+1].dropna()

            if len(window) < training_period or window.std() < 1e-9:
                # Copia valori precedenti se esistono
                if i > 0:
                    result_low.iloc[i] = result_low.iloc[i-1]
                    result_mid.iloc[i] = result_mid.iloc[i-1]
                    result_high.iloc[i] = result_high.iloc[i-1]
                    result_cluster_idx.iloc[i] = result_cluster_idx.iloc[i-1]
                continue

            # Inizializza centroidi con percentili
            v_min, v_max = window.min(), window.max()
            v_range = v_max - v_min

            # Guess iniziali
            low_c = v_min + v_range * 0.25
            mid_c = v_min + v_range * 0.50
            high_c = v_min + v_range * 0.75

            # K-Means iterations
            for _ in range(max_iterations):
                # Assegna ogni punto al cluster più vicino
                distances = pd.DataFrame({
                    'low': abs(window - low_c),
                    'mid': abs(window - mid_c),
                    'high': abs(window - high_c)
                })
                assignments = distances.idxmin(axis=1)

                # Calcola nuovi centroidi
                new_low = window[assignments == 'low'].mean() if (assignments == 'low').any() else low_c
                new_mid = window[assignments == 'mid'].mean() if (assignments == 'mid').any() else mid_c
                new_high = window[assignments == 'high'].mean() if (assignments == 'high').any() else high_c

                # Check convergenza
                if (abs(new_low - low_c) < 1e-9 and
                    abs(new_mid - mid_c) < 1e-9 and
                    abs(new_high - high_c) < 1e-9):
                    break

                low_c, mid_c, high_c = new_low, new_mid, new_high

            # Ordina centroidi (low < mid < high)
            centroids = sorted([low_c, mid_c, high_c])
            result_low.iloc[i] = centroids[0]
            result_mid.iloc[i] = centroids[1]
            result_high.iloc[i] = centroids[2]

            # Assegna il punto corrente al cluster più vicino
            current_atr = atr_series.iloc[i]
            distances_current = [abs(current_atr - c) for c in centroids]
            result_cluster_idx.iloc[i] = distances_current.index(min(distances_current))

        return result_low, result_mid, result_high, result_cluster_idx

    @staticmethod
    def calculate_adaptive_supertrend(data, atr_period=10, multiplier=3.0, training_period=100):
        """
        Adaptive SuperTrend usando K-Means clustering della volatilità

        Il SuperTrend si adatta dinamicamente alla volatilità del mercato usando
        i centroidi dei cluster di volatilità invece di un ATR fisso.

        Args:
            data: DataFrame con colonne OHLC
            atr_period: Periodo per calcolo ATR
            multiplier: Moltiplicatore per le bande SuperTrend
            training_period: Finestra di training per K-Means

        Returns:
            tuple: (supertrend_line, direction, buy_signals, sell_signals,
                    cluster_index, adaptive_atr)
                - supertrend_line: Linea SuperTrend
                - direction: 1=downtrend, -1=uptrend
                - buy_signals: Boolean series per segnali BUY
                - sell_signals: Boolean series per segnali SELL
                - cluster_index: Indice cluster volatilità (0=low, 1=mid, 2=high)
                - adaptive_atr: ATR adattivo usato (centroide del cluster corrente)
        """
        # Calcola ATR base
        atr = IndicatorCalculator.calculate_atr(data, period=atr_period)

        # K-Means clustering della volatilità
        low_c, mid_c, high_c, cluster_idx = IndicatorCalculator._kmeans_volatility_clustering(
            atr, training_period=training_period
        )

        # Crea ATR adattivo basato sul cluster corrente
        adaptive_atr = pd.Series(index=data.index, dtype=float)
        for i in range(len(data)):
            if pd.notna(cluster_idx.iloc[i]):
                cluster = int(cluster_idx.iloc[i])
                if cluster == 0:
                    adaptive_atr.iloc[i] = low_c.iloc[i]
                elif cluster == 1:
                    adaptive_atr.iloc[i] = mid_c.iloc[i]
                else:  # cluster == 2
                    adaptive_atr.iloc[i] = high_c.iloc[i]

        # Calcola SuperTrend usando ATR adattivo
        high = data['high']
        low = data['low']
        close = data['close']

        hl2 = (high + low) / 2

        # Bande base
        basic_upper = hl2 + multiplier * adaptive_atr
        basic_lower = hl2 - multiplier * adaptive_atr

        # Inizializza output
        final_upper = pd.Series(index=data.index, dtype=float)
        final_lower = pd.Series(index=data.index, dtype=float)
        supertrend = pd.Series(index=data.index, dtype=float)
        direction = pd.Series(index=data.index, dtype=float)

        # Calcola SuperTrend con logica di trend
        for i in range(len(data)):
            if i == 0 or pd.isna(adaptive_atr.iloc[i]):
                final_upper.iloc[i] = basic_upper.iloc[i]
                final_lower.iloc[i] = basic_lower.iloc[i]
                direction.iloc[i] = -1  # Inizia uptrend
                supertrend.iloc[i] = final_lower.iloc[i]
                continue

            # Update upper band
            if basic_upper.iloc[i] < final_upper.iloc[i-1] or close.iloc[i-1] > final_upper.iloc[i-1]:
                final_upper.iloc[i] = basic_upper.iloc[i]
            else:
                final_upper.iloc[i] = final_upper.iloc[i-1]

            # Update lower band
            if basic_lower.iloc[i] > final_lower.iloc[i-1] or close.iloc[i-1] < final_lower.iloc[i-1]:
                final_lower.iloc[i] = basic_lower.iloc[i]
            else:
                final_lower.iloc[i] = final_lower.iloc[i-1]

            # Determina direction
            prev_direction = direction.iloc[i-1]
            if prev_direction == 1:  # Was downtrend
                if close.iloc[i] > final_upper.iloc[i]:
                    direction.iloc[i] = -1  # Switch to uptrend
                else:
                    direction.iloc[i] = 1
            else:  # Was uptrend
                if close.iloc[i] < final_lower.iloc[i]:
                    direction.iloc[i] = 1  # Switch to downtrend
                else:
                    direction.iloc[i] = -1

            # SuperTrend line
            if direction.iloc[i] == -1:  # Uptrend
                supertrend.iloc[i] = final_lower.iloc[i]
            else:  # Downtrend
                supertrend.iloc[i] = final_upper.iloc[i]

        # Genera segnali
        buy_signals = pd.Series(False, index=data.index)
        sell_signals = pd.Series(False, index=data.index)

        for i in range(1, len(data)):
            # BUY: direction passa da 1 (downtrend) a -1 (uptrend)
            if direction.iloc[i] == -1 and direction.iloc[i-1] == 1:
                buy_signals.iloc[i] = True

            # SELL: direction passa da -1 (uptrend) a 1 (downtrend)
            elif direction.iloc[i] == 1 and direction.iloc[i-1] == -1:
                sell_signals.iloc[i] = True

        return supertrend, direction, buy_signals, sell_signals, cluster_idx, adaptive_atr

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
        (df['supertrend'], df['supertrend_direction'],
         df['supertrend_buy'], df['supertrend_sell'],
         df['volatility_cluster'], df['adaptive_atr']) = self.calculate_adaptive_supertrend(
            df, atr_period=10, multiplier=3.0, training_period=100
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

        # Calcola Adaptive SuperTrend
        (df['supertrend'], df['supertrend_direction'],
         df['supertrend_buy'], df['supertrend_sell'],
         df['volatility_cluster'], df['adaptive_atr']) = self.calculate_adaptive_supertrend(
            df, atr_period=10, multiplier=3.0, training_period=100
        )

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
            # Adaptive SuperTrend indicators
            'supertrend': last['supertrend'],
            'supertrend_direction': last['supertrend_direction'],
            'supertrend_buy': last['supertrend_buy'],
            'supertrend_sell': last['supertrend_sell'],
            'volatility_cluster': last['volatility_cluster'],
            'adaptive_atr': last['adaptive_atr'],
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
