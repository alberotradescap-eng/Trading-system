"""
Adaptive SuperTrend Trading System - Complete Example
Version 17 - Enhanced and Bug-Fixed

This example demonstrates how to use the corrected trading engine
with the Adaptive SuperTrend strategy.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import yaml
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from engine.adaptive_supertrend_engine import TradingEngine, TradingEngineConfig
from engine.performance_analytics import PerformanceAnalytics


def load_config(config_path='config/adaptive_supertrend_config.yaml'):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def load_data_adaptive_supertrend(file_path, resampling=False, resample_rate='10T'):
    """
    Load data for Adaptive SuperTrend strategy

    Args:
        file_path: Path to CSV file
        resampling: Whether to resample data
        resample_rate: Resampling rate (e.g., '10T' for 10 minutes)

    Returns:
        DataFrame with OHLCV data and strategy signals
    """
    # Load CSV
    df = pd.read_csv(file_path)

    # Convert time column to datetime and set as index
    if 'date_time' in df.columns:
        df['date_time'] = pd.to_datetime(df['date_time'])
        df.set_index('date_time', inplace=True)
    elif 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
    else:
        # Try to infer datetime column
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        if date_cols:
            df[date_cols[0]] = pd.to_datetime(df[date_cols[0]])
            df.set_index(date_cols[0], inplace=True)

    # Ensure required columns exist
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Replace NaN in strategy columns with -1
    strategy_cols = [
        'adapt_supertrend_entry_long',
        'adapt_supertrend_entry_short',
        'adapt_supertrend_exit_long',
        'adapt_supertrend_exit_short'
    ]

    for col in strategy_cols:
        if col in df.columns:
            df[col] = df[col].fillna(-1)

    # Resample if requested
    if resampling and resample_rate:
        df = df.resample(resample_rate).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            **{col: 'last' for col in strategy_cols if col in df.columns}
        })

    # Drop any remaining NaN rows
    df.dropna(inplace=True)

    return df


def create_sample_data(num_bars=1000):
    """
    Create sample data for testing

    Args:
        num_bars: Number of bars to generate

    Returns:
        DataFrame with sample OHLCV data and strategy signals
    """
    print("⚠️  No data file found. Creating sample data for demonstration...")

    # Generate datetime index
    start_date = datetime.now() - timedelta(days=num_bars//24)
    dates = pd.date_range(start=start_date, periods=num_bars, freq='1H')

    # Generate random price data
    np.random.seed(42)
    base_price = 100
    returns = np.random.normal(0.0001, 0.02, num_bars)
    prices = base_price * np.exp(np.cumsum(returns))

    # Create OHLCV data
    df = pd.DataFrame({
        'open': prices,
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, num_bars))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, num_bars))),
        'close': prices * (1 + np.random.normal(0, 0.005, num_bars)),
        'volume': np.random.randint(100000, 1000000, num_bars)
    }, index=dates)

    # Generate simple strategy signals (trend following with moving averages)
    df['sma_fast'] = df['close'].rolling(20).mean()
    df['sma_slow'] = df['close'].rolling(50).mean()

    # Entry signals: fast MA crosses above slow MA
    df['adapt_supertrend_entry_long'] = np.where(
        (df['sma_fast'] > df['sma_slow']) &
        (df['sma_fast'].shift(1) <= df['sma_slow'].shift(1)),
        1, -1
    )

    # Exit signals: fast MA crosses below slow MA
    df['adapt_supertrend_exit_long'] = np.where(
        (df['sma_fast'] < df['sma_slow']) &
        (df['sma_fast'].shift(1) >= df['sma_slow'].shift(1)),
        1, -1
    )

    # Short signals (opposite)
    df['adapt_supertrend_entry_short'] = np.where(
        (df['sma_fast'] < df['sma_slow']) &
        (df['sma_fast'].shift(1) >= df['sma_slow'].shift(1)),
        1, -1
    )

    df['adapt_supertrend_exit_short'] = np.where(
        (df['sma_fast'] > df['sma_slow']) &
        (df['sma_fast'].shift(1) <= df['sma_slow'].shift(1)),
        1, -1
    )

    # Drop helper columns
    df.drop(['sma_fast', 'sma_slow'], axis=1, inplace=True)

    return df


def run_trading_system(config_dict=None):
    """
    Main function to run the trading system

    Args:
        config_dict: Configuration dictionary (if None, loads from file)
    """
    # Load configuration
    if config_dict is None:
        print("Loading configuration...")
        config_dict = load_config()

    # Extract configuration values
    cfg_trading = config_dict['trading']
    cfg_risk = config_dict['risk']
    cfg_data = config_dict['data']
    cfg_sim = config_dict['simulation']
    cfg_behavior = config_dict['behavior']
    cfg_strategy = config_dict['strategy']

    # Initialize engine components
    print("Initializing trading engine...")
    engine_config = TradingEngineConfig(base_path=cfg_data['paths']['base'])
    engine = TradingEngine(config=engine_config)
    analytics = PerformanceAnalytics(config=engine_config)

    # Load data
    print(f"\nLoading data for {cfg_trading['ticker']}...")

    data_path = engine_config.get_path('data', cfg_sim['enabled'])
    data_file = data_path / cfg_data['filename']

    if data_file.exists():
        dataset = load_data_adaptive_supertrend(
            data_file,
            cfg_data['resampling']['enabled'],
            cfg_data['resampling']['rate']
        )
        print(f"✓ Loaded {len(dataset)} bars from {data_file}")
    else:
        # Create sample data if file doesn't exist
        dataset = create_sample_data()
        print(f"✓ Created {len(dataset)} bars of sample data")

    # Define entry and exit rules based on strategy
    print("\nDefining trading rules...")

    direction = cfg_trading['direction']
    strategy_cfg = cfg_strategy['adaptive_supertrend']

    if direction == 'long':
        entry_col = strategy_cfg['entry_long_column']
        exit_col = strategy_cfg['exit_long_column']
    else:  # short
        entry_col = strategy_cfg['entry_short_column']
        exit_col = strategy_cfg['exit_short_column']

    # Convert strategy columns to boolean rules
    enter_rules = dataset[entry_col] == 1
    exit_rules = dataset[exit_col] == 1

    # Entry level (use close price)
    enter_level = dataset['close']

    print(f"✓ Entry signals: {enter_rules.sum()}")
    print(f"✓ Exit signals: {exit_rules.sum()}")

    # Apply trading system
    print("\nApplying trading system...")

    trading_system = engine.apply_trading_system(
        imported_dataframe=dataset,
        bigpointvalue=cfg_risk['bigpointvalue'],
        tick=cfg_risk['tick'],
        direction=direction,
        order_type=cfg_trading['order_type'],
        enter_level=enter_level,
        enter_rules=enter_rules,
        exit_rules=exit_rules,
        operation_money=cfg_risk['operation_money'],
        costs=cfg_risk['costs'],
        instrument=cfg_trading['instrument'],
        ticker=cfg_trading['ticker'],
        export_filename=cfg_sim['export_filename'],
        simulation=cfg_sim['enabled'],
        eliminate_same_bar_entry_exit=cfg_behavior['eliminate_same_bar_entry_exit']
    )

    # Apply stop loss and take profit if enabled
    if cfg_risk['stop_loss']['enabled']:
        print("\nApplying stop loss rules...")
        stop_loss_rules = trading_system['open_equity'] < \
                         -cfg_risk['operation_money'] * cfg_risk['stop_loss']['percentage']

        enter_rules, exit_rules = engine.compute_stop_loss(
            trading_system, stop_loss_rules, enter_rules, exit_rules
        )

        # Re-apply trading system with updated rules
        trading_system = engine.apply_trading_system(
            imported_dataframe=dataset,
            bigpointvalue=cfg_risk['bigpointvalue'],
            tick=cfg_risk['tick'],
            direction=direction,
            order_type=cfg_trading['order_type'],
            enter_level=enter_level,
            enter_rules=enter_rules,
            exit_rules=exit_rules,
            operation_money=cfg_risk['operation_money'],
            costs=cfg_risk['costs'],
            instrument=cfg_trading['instrument'],
            ticker=cfg_trading['ticker'],
            export_filename=cfg_sim['export_filename'],
            simulation=cfg_sim['enabled'],
            eliminate_same_bar_entry_exit=cfg_behavior['eliminate_same_bar_entry_exit']
        )

    if cfg_risk['take_profit']['enabled']:
        print("Applying take profit rules...")
        take_profit_rules = trading_system['open_equity'] > \
                           cfg_risk['operation_money'] * cfg_risk['take_profit']['multiplier']

        enter_rules, exit_rules = engine.compute_take_profit(
            trading_system, take_profit_rules, enter_rules, exit_rules
        )

        # Re-apply trading system with updated rules
        trading_system = engine.apply_trading_system(
            imported_dataframe=dataset,
            bigpointvalue=cfg_risk['bigpointvalue'],
            tick=cfg_risk['tick'],
            direction=direction,
            order_type=cfg_trading['order_type'],
            enter_level=enter_level,
            enter_rules=enter_rules,
            exit_rules=exit_rules,
            operation_money=cfg_risk['operation_money'],
            costs=cfg_risk['costs'],
            instrument=cfg_trading['instrument'],
            ticker=cfg_trading['ticker'],
            export_filename=cfg_sim['export_filename'],
            simulation=cfg_sim['enabled'],
            eliminate_same_bar_entry_exit=cfg_behavior['eliminate_same_bar_entry_exit']
        )

    # Apply trailing stop if enabled
    if cfg_risk['trailing_stop']['enabled']:
        print("Applying trailing stop rules...")
        trailing_stop_exit = engine.compute_trailing_stop(
            trading_system,
            trail_percent=cfg_risk['trailing_stop']['percentage'],
            direction=direction
        )

        exit_rules = exit_rules | trailing_stop_exit

        # Re-apply trading system with trailing stop
        trading_system = engine.apply_trading_system(
            imported_dataframe=dataset,
            bigpointvalue=cfg_risk['bigpointvalue'],
            tick=cfg_risk['tick'],
            direction=direction,
            order_type=cfg_trading['order_type'],
            enter_level=enter_level,
            enter_rules=enter_rules,
            exit_rules=exit_rules,
            operation_money=cfg_risk['operation_money'],
            costs=cfg_risk['costs'],
            instrument=cfg_trading['instrument'],
            ticker=cfg_trading['ticker'],
            export_filename=cfg_sim['export_filename'],
            simulation=cfg_sim['enabled'],
            eliminate_same_bar_entry_exit=cfg_behavior['eliminate_same_bar_entry_exit']
        )

    # Extract operations
    operations = trading_system['operations'].dropna()

    print(f"\n✓ Trading system applied successfully!")
    print(f"  Total bars processed: {len(trading_system)}")
    print(f"  Completed operations: {len(operations)}")

    # Generate performance report
    if len(operations) > 0:
        print("\n" + "="*60)
        print("PERFORMANCE ANALYSIS")
        print("="*60)

        analytics.performance_report_console(
            trading_system,
            operations,
            trading_system['closed_equity'],
            trading_system['open_equity']
        )

        # Save performance report
        report_path = engine_config.get_path('reports', cfg_sim['enabled'])
        report_file = report_path / f"{cfg_trading['ticker']}_performance_report.csv"

        analytics.save_performance_report_csv(
            cfg_trading['ticker'],
            trading_system,
            operations,
            trading_system['closed_equity'],
            trading_system['open_equity'],
            report_file
        )

        # Generate visualizations
        print("\nGenerating visualizations...")

        # Equity curve
        fig = analytics.plot_equity(trading_system['open_equity'])
        fig.savefig(report_path / f"{cfg_trading['ticker']}_equity.png", dpi=300, bbox_inches='tight')
        print(f"✓ Saved equity curve")

        # Drawdown
        fig = analytics.plot_drawdown(trading_system['open_equity'])
        fig.savefig(report_path / f"{cfg_trading['ticker']}_drawdown.png", dpi=300, bbox_inches='tight')
        print(f"✓ Saved drawdown chart")

        # Trading signals
        fig = analytics.plot_trading_signals(trading_system, cfg_trading['ticker'], direction)
        if fig:
            fig.savefig(report_path / f"{cfg_trading['ticker']}_signals.png", dpi=300, bbox_inches='tight')
            print(f"✓ Saved trading signals chart")

        # Annual performance
        if len(operations) > 12:  # Need at least 1 year of data
            fig = analytics.plot_annual_histogram(operations)
            fig.savefig(report_path / f"{cfg_trading['ticker']}_annual.png", dpi=300, bbox_inches='tight')
            print(f"✓ Saved annual performance chart")

        print(f"\n✅ All reports saved to: {report_path}")

    else:
        print("\n⚠️  No operations completed. Check your entry/exit rules.")

    return trading_system, operations


def main():
    """Main entry point"""
    print("="*60)
    print("ADAPTIVE SUPERTREND TRADING SYSTEM")
    print("Version 17 - Enhanced and Bug-Fixed")
    print("="*60)
    print()

    try:
        trading_system, operations = run_trading_system()
        print("\n✅ Trading system execution completed successfully!")
        return trading_system, operations

    except FileNotFoundError as e:
        print(f"\n❌ Configuration file not found: {e}")
        print("   Creating sample configuration...")

        # Run with sample data
        return run_trading_system()

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    trading_system, operations = main()
