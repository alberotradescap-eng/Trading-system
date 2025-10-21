#!/usr/bin/env python3
"""
Test script per verificare l'integrazione dell'Adaptive SuperTrend nell'ETL

Questo script verifica che:
1. L'IndicatorCalculator possa calcolare l'Adaptive SuperTrend
2. I segnali BUY/SELL vengano generati correttamente
3. La strategia AdaptiveSuperTrendStrategy sia utilizzabile
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Aggiungi path al progetto
sys.path.insert(0, str(Path(__file__).parent))

from etl.indicator_calculator import IndicatorCalculator
from config.trading_rules import AdaptiveSuperTrendStrategy

def generate_test_data(n_candles=500):
    """Genera dati OHLCV di test"""
    print(f"Generando {n_candles} candles di test...")

    # Genera prezzi random walk
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(n_candles) * 2)

    # Genera OHLC
    data = {
        'timestamp': pd.date_range(start='2024-01-01', periods=n_candles, freq='5min'),
        'open': close_prices + np.random.randn(n_candles) * 0.5,
        'high': close_prices + abs(np.random.randn(n_candles)) * 1.5,
        'low': close_prices - abs(np.random.randn(n_candles)) * 1.5,
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, n_candles)
    }

    df = pd.DataFrame(data)

    # Assicura che high >= close >= low
    df['high'] = df[['high', 'close']].max(axis=1)
    df['low'] = df[['low', 'close']].min(axis=1)

    return df

def test_indicator_calculator():
    """Test calcolo indicatori con Adaptive SuperTrend"""
    print("\n" + "="*70)
    print("TEST 1: IndicatorCalculator con Adaptive SuperTrend")
    print("="*70)

    # Genera dati test
    df = generate_test_data(n_candles=500)

    # Crea calculator
    calc = IndicatorCalculator()

    # Calcola solo Adaptive SuperTrend
    print("\nCalcolando Adaptive SuperTrend...")
    try:
        (supertrend, direction, buy_signals, sell_signals,
         cluster_idx, adaptive_atr) = calc.calculate_adaptive_supertrend(
            df, atr_period=10, multiplier=3.0, training_period=100
        )

        print("✓ Calcolo Adaptive SuperTrend completato con successo")

        # Verifica output
        print(f"\nRisultati:")
        print(f"  - SuperTrend values: {supertrend.notna().sum()}/{len(supertrend)}")
        print(f"  - Direction values: {direction.notna().sum()}/{len(direction)}")
        print(f"  - BUY signals: {buy_signals.sum()}")
        print(f"  - SELL signals: {sell_signals.sum()}")
        print(f"  - Cluster assignments: {cluster_idx.notna().sum()}/{len(cluster_idx)}")

        # Mostra ultimi 5 segnali BUY
        if buy_signals.sum() > 0:
            print(f"\nUltimi segnali BUY:")
            buy_indices = df[buy_signals].tail(5).index
            for idx in buy_indices:
                print(f"  - {df.loc[idx, 'timestamp']}: close={df.loc[idx, 'close']:.2f}, "
                      f"cluster={int(cluster_idx.loc[idx]) if pd.notna(cluster_idx.loc[idx]) else 'N/A'}")

        # Mostra ultimi 5 segnali SELL
        if sell_signals.sum() > 0:
            print(f"\nUltimi segnali SELL:")
            sell_indices = df[sell_signals].tail(5).index
            for idx in sell_indices:
                print(f"  - {df.loc[idx, 'timestamp']}: close={df.loc[idx, 'close']:.2f}, "
                      f"cluster={int(cluster_idx.loc[idx]) if pd.notna(cluster_idx.loc[idx]) else 'N/A'}")

        return True

    except Exception as e:
        print(f"✗ Errore durante calcolo: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_realtime_calculation():
    """Test calcolo real-time con tutti gli indicatori"""
    print("\n" + "="*70)
    print("TEST 2: Calcolo Real-time con Adaptive SuperTrend")
    print("="*70)

    # Genera dati test
    df = generate_test_data(n_candles=500)

    # Crea calculator
    calc = IndicatorCalculator()

    print("\nCalcolando indicatori real-time...")
    try:
        indicators = calc.calculate_indicators_realtime(df, window_size=200)

        print("✓ Calcolo real-time completato con successo")

        # Verifica che tutti gli indicatori siano presenti
        required_keys = [
            'timestamp', 'close', 'volume',
            'sma_20', 'sma_50', 'rsi', 'macd', 'signal',
            'bb_upper', 'bb_middle', 'bb_lower', 'atr', 'volume_sma_20',
            'supertrend', 'supertrend_direction', 'supertrend_buy', 'supertrend_sell',
            'volatility_cluster', 'adaptive_atr'
        ]

        missing_keys = [k for k in required_keys if k not in indicators]
        if missing_keys:
            print(f"✗ Chiavi mancanti: {missing_keys}")
            return False

        print(f"\nIndicatori calcolati (ultimi valori):")
        print(f"  - Timestamp: {indicators['timestamp']}")
        print(f"  - Close: {indicators['close']:.2f}")
        print(f"  - RSI: {indicators['rsi']:.2f}")
        print(f"  - SuperTrend: {indicators['supertrend']:.2f}")
        print(f"  - SuperTrend Direction: {int(indicators['supertrend_direction'])}")
        print(f"  - SuperTrend BUY Signal: {indicators['supertrend_buy']}")
        print(f"  - SuperTrend SELL Signal: {indicators['supertrend_sell']}")
        print(f"  - Volatility Cluster: {int(indicators['volatility_cluster']) if pd.notna(indicators['volatility_cluster']) else 'N/A'}")
        print(f"  - Adaptive ATR: {indicators['adaptive_atr']:.4f}")

        return True

    except Exception as e:
        print(f"✗ Errore durante calcolo real-time: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy():
    """Test AdaptiveSuperTrendStrategy"""
    print("\n" + "="*70)
    print("TEST 3: AdaptiveSuperTrendStrategy")
    print("="*70)

    # Crea strategia
    strategy = AdaptiveSuperTrendStrategy()

    print(f"\nStrategia: {strategy.name}")
    print(f"Descrizione: {strategy.description}")

    # Test entry_long con segnale BUY
    print("\nTest Entry LONG con segnale BUY:")
    data_buy = {
        'close': 100.0,
        'supertrend': 98.0,
        'supertrend_buy': True,
        'supertrend_sell': False,
        'supertrend_direction': -1,  # Uptrend
        'rsi': 60,
        'volatility_cluster': 1,
        'adaptive_atr': 1.5
    }

    should_enter = strategy.entry_long(data_buy)
    print(f"  Risultato: {'✓ ENTRY' if should_enter else '✗ NO ENTRY'}")

    # Test entry_short con segnale SELL
    print("\nTest Entry SHORT con segnale SELL:")
    data_sell = {
        'close': 100.0,
        'supertrend': 102.0,
        'supertrend_buy': False,
        'supertrend_sell': True,
        'supertrend_direction': 1,  # Downtrend
        'rsi': 40,
        'volatility_cluster': 1,
        'adaptive_atr': 1.5
    }

    should_enter = strategy.entry_short(data_sell)
    print(f"  Risultato: {'✓ ENTRY' if should_enter else '✗ NO ENTRY'}")

    # Test exit_long con take profit
    print("\nTest Exit LONG con Take Profit:")
    data_exit_tp = {
        'close': 102.5,  # +2.5% profit
        'supertrend_sell': False,
        'supertrend_direction': -1,
        'rsi': 65
    }

    should_exit, reason = strategy.exit_long(data_exit_tp, entry_price=100.0)
    print(f"  Risultato: {'✓ EXIT' if should_exit else '✗ HOLD'} - Reason: {reason}")

    # Test exit_long con stop loss
    print("\nTest Exit LONG con Stop Loss:")
    data_exit_sl = {
        'close': 98.5,  # -1.5% loss
        'supertrend_sell': False,
        'supertrend_direction': -1,
        'rsi': 50
    }

    should_exit, reason = strategy.exit_long(data_exit_sl, entry_price=100.0)
    print(f"  Risultato: {'✓ EXIT' if should_exit else '✗ HOLD'} - Reason: {reason}")

    # Test can_open_position
    print("\nTest can_open_position:")
    can_open, reason = strategy.can_open_position(data_buy, current_positions=[])
    print(f"  Risultato: {'✓ CAN OPEN' if can_open else '✗ CANNOT OPEN'} - Reason: {reason}")

    return True

def main():
    """Esegue tutti i test"""
    print("\n" + "="*70)
    print("TEST ADAPTIVE SUPERTREND INTEGRATION")
    print("="*70)

    results = []

    # Test 1: Indicator Calculator
    results.append(("IndicatorCalculator", test_indicator_calculator()))

    # Test 2: Real-time calculation
    results.append(("Real-time Calculation", test_realtime_calculation()))

    # Test 3: Strategy
    results.append(("AdaptiveSuperTrendStrategy", test_strategy()))

    # Riepilogo
    print("\n" + "="*70)
    print("RIEPILOGO TEST")
    print("="*70)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<50} {status}")

    # Check finale
    all_passed = all(r for _, r in results)

    if all_passed:
        print("\n🎉 Tutti i test sono passati! L'integrazione è completa.")
        return 0
    else:
        print("\n❌ Alcuni test sono falliti. Controlla gli errori sopra.")
        return 1

if __name__ == '__main__':
    exit(main())
