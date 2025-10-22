"""
Test script for Adaptive SuperTrend implementation

This script tests the Adaptive SuperTrend indicator and strategy
to ensure they work correctly.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from etl.indicator_calculator import IndicatorCalculator
from config.trading_rules import AdaptiveSupertrendStrategy


def generate_sample_data(n_rows=200):
    """Generate sample OHLCV data for testing"""
    np.random.seed(42)

    # Generate timestamps
    start_date = datetime(2024, 1, 1)
    timestamps = [start_date + timedelta(minutes=i) for i in range(n_rows)]

    # Generate price data with trend
    base_price = 100
    trend = np.linspace(0, 20, n_rows)  # Upward trend
    noise = np.random.randn(n_rows) * 2  # Random noise

    close = base_price + trend + noise

    # Generate OHLC from close
    high = close + np.abs(np.random.randn(n_rows)) * 0.5
    low = close - np.abs(np.random.randn(n_rows)) * 0.5
    open_price = close + np.random.randn(n_rows) * 0.3

    # Generate volume
    volume = np.random.randint(1000, 10000, n_rows)

    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })

    return df


def test_indicator_calculation():
    """Test the Adaptive SuperTrend indicator calculation"""
    print("=" * 70)
    print("TEST 1: Adaptive SuperTrend Indicator Calculation")
    print("=" * 70)

    # Generate sample data
    df = generate_sample_data(200)
    print(f"\n✓ Generated {len(df)} rows of sample data")

    # Calculate indicators
    calculator = IndicatorCalculator()

    try:
        # Calculate adaptive supertrend
        (supertrend,
         direction,
         multiplier,
         entry_long,
         entry_short,
         exit_long,
         exit_short) = calculator.calculate_adaptive_supertrend(df)

        print("✓ Adaptive SuperTrend calculated successfully")
        print(f"  - SuperTrend values: {supertrend.iloc[-5:].values}")
        print(f"  - Direction values: {direction.iloc[-5:].values}")
        print(f"  - Entry long signals: {entry_long.sum()}")
        print(f"  - Entry short signals: {entry_short.sum()}")
        print(f"  - Exit long signals: {exit_long.sum()}")
        print(f"  - Exit short signals: {exit_short.sum()}")

        return True
    except Exception as e:
        print(f"✗ Error calculating Adaptive SuperTrend: {e}")
        return False


def test_strategy_logic():
    """Test the Adaptive SuperTrend strategy logic"""
    print("\n" + "=" * 70)
    print("TEST 2: Adaptive SuperTrend Strategy Logic")
    print("=" * 70)

    # Create strategy
    strategy = AdaptiveSupertrendStrategy(
        stop_loss_pct=2.0,
        take_profit_pct=4.0,
        use_volume_filter=True,
        use_volatility_filter=True
    )

    print(f"\n✓ Strategy created: {strategy.name}")
    print(f"  - Stop Loss: {strategy.stop_loss_pct}%")
    print(f"  - Take Profit: {strategy.take_profit_pct}%")

    # Test entry long
    test_data_long = {
        'close': 100,
        'adapt_supertrend_entry_long': True,
        'adaptive_supertrend_direction': 1,
        'adaptive_supertrend': 98,
        'volume': 5000,
        'volume_sma_20': 4000,
        'atr': 1.5
    }

    entry_long = strategy.entry_long(test_data_long)
    print(f"\n✓ Entry Long Test: {entry_long}")

    # Test exit long
    test_data_exit = {
        'close': 104,  # 4% profit
        'adapt_supertrend_exit_long': False,
        'adaptive_supertrend_direction': 1,
        'adaptive_supertrend': 102
    }

    should_exit, reason = strategy.exit_long(test_data_exit, entry_price=100)
    print(f"✓ Exit Long Test: {should_exit}, Reason: {reason}")

    # Test can_open_position
    can_open, reason = strategy.can_open_position(test_data_long, current_positions=[])
    print(f"✓ Can Open Position Test: {can_open}, Reason: {reason}")

    return True


def test_full_pipeline():
    """Test the full pipeline from data to signals"""
    print("\n" + "=" * 70)
    print("TEST 3: Full Pipeline Test")
    print("=" * 70)

    # Generate sample data
    df = generate_sample_data(200)

    # Calculate all indicators
    calculator = IndicatorCalculator()

    try:
        # Add basic indicators
        df['sma_20'] = calculator.calculate_sma(df, period=20)
        df['rsi'] = calculator.calculate_rsi(df, period=14)
        df['atr'] = calculator.calculate_atr(df, period=14)
        df['volume_sma_20'] = calculator.calculate_volume_sma(df, period=20)

        # Add adaptive supertrend
        (df['adaptive_supertrend'],
         df['adaptive_supertrend_direction'],
         df['adaptive_multiplier'],
         df['adapt_supertrend_entry_long'],
         df['adapt_supertrend_entry_short'],
         df['adapt_supertrend_exit_long'],
         df['adapt_supertrend_exit_short']) = calculator.calculate_adaptive_supertrend(df)

        print("\n✓ All indicators calculated successfully")

        # Create strategy
        strategy = AdaptiveSupertrendStrategy()

        # Simulate trading signals
        signals = []
        for idx, row in df.iterrows():
            data = row.to_dict()

            entry_long = strategy.entry_long(data)
            entry_short = strategy.entry_short(data)

            if entry_long:
                signals.append(('LONG', idx, data['close']))
            if entry_short:
                signals.append(('SHORT', idx, data['close']))

        print(f"✓ Generated {len(signals)} trading signals")

        # Show first 5 signals
        if signals:
            print("\nFirst 5 signals:")
            for sig in signals[:5]:
                print(f"  {sig[0]} at {sig[1]} @ ${sig[2]:.2f}")

        return True

    except Exception as e:
        print(f"✗ Error in full pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n🚀 Starting Adaptive SuperTrend Tests\n")

    results = []

    # Run tests
    results.append(("Indicator Calculation", test_indicator_calculation()))
    results.append(("Strategy Logic", test_strategy_logic()))
    results.append(("Full Pipeline", test_full_pipeline()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 All tests passed successfully!")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")

    print()
