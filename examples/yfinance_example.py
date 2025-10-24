"""
yFinance Paper Trading - Example Usage
=======================================
Demonstrates how to use yFinance broker for paper trading across multiple asset classes.

Features demonstrated:
1. Setting up yFinance paper trading broker
2. Downloading data for stocks, crypto, ETFs
3. Executing paper trades
4. Tracking positions and P&L
5. Multi-asset portfolio management
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from broker.yfinance_broker import YFinanceBroker
from extractors.yfinance_extractor import YFinanceExtractor
from extractors.multi_source_extractor import MultiSourceExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


async def example_1_basic_paper_trading():
    """Example 1: Basic paper trading with stocks"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Paper Trading with Stocks")
    print("="*70)

    # Initialize broker with $10,000
    broker = YFinanceBroker(initial_capital=10000)
    await broker.initialize()

    # Buy 10 shares of Apple
    print("\n--- Buying 10 shares of AAPL ---")
    result = await broker.place_market_order('AAPL', 'BUY', 10)

    if result.success:
        print(f"✓ Order filled at ${result.avg_price:.2f}")
        print(f"  Total cost: ${result.avg_price * result.quantity:.2f}")
    else:
        print(f"✗ Order failed: {result.error_message}")

    # Buy 5 shares of Microsoft
    print("\n--- Buying 5 shares of MSFT ---")
    result = await broker.place_market_order('MSFT', 'BUY', 5)

    if result.success:
        print(f"✓ Order filled at ${result.avg_price:.2f}")

    # Check positions
    print("\n--- Current Positions ---")
    positions = await broker.get_positions()
    for pos in positions:
        pnl_str = f"${pos.unrealized_pnl:+.2f}" if pos.unrealized_pnl else "N/A"
        print(f"  {pos.symbol}: {pos.quantity} shares @ ${pos.entry_price:.2f} | P&L: {pnl_str}")

    # Check balance
    print("\n--- Account Balance ---")
    balances = await broker.get_account_balance()
    print(f"  Cash (USD): ${balances['USD'].total:,.2f}")
    print(f"  Portfolio Value: ${broker._calculate_total_portfolio_value():,.2f}")

    # Statistics
    print("\n--- Trading Statistics ---")
    stats = broker.get_statistics()
    print(f"  Total Trades: {stats['total_trades']}")
    print(f"  Total P&L: ${stats['total_pnl']:+.2f}")
    print(f"  Total Return: {stats['total_return_pct']:+.2f}%")

    await broker.shutdown()


async def example_2_crypto_paper_trading():
    """Example 2: Paper trading with crypto via yFinance"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Crypto Paper Trading (yFinance)")
    print("="*70)

    broker = YFinanceBroker(initial_capital=10000)
    await broker.initialize()

    # Buy 0.1 BTC
    print("\n--- Buying 0.1 BTC-USD ---")
    result = await broker.place_market_order('BTC-USD', 'BUY', 0.1)

    if result.success:
        print(f"✓ Order filled at ${result.avg_price:,.2f}")
        print(f"  Total cost: ${result.avg_price * result.quantity:,.2f}")

    # Buy 1 ETH
    print("\n--- Buying 1 ETH-USD ---")
    result = await broker.place_market_order('ETH-USD', 'BUY', 1.0)

    if result.success:
        print(f"✓ Order filled at ${result.avg_price:,.2f}")

    # Check positions
    print("\n--- Crypto Positions ---")
    positions = await broker.get_positions()
    for pos in positions:
        pnl_str = f"${pos.unrealized_pnl:+.2f}" if pos.unrealized_pnl else "N/A"
        print(f"  {pos.symbol}: {pos.quantity} @ ${pos.entry_price:,.2f} | P&L: {pnl_str}")

    await broker.shutdown()


async def example_3_multi_asset_portfolio():
    """Example 3: Multi-asset portfolio (stocks + ETFs + crypto)"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Multi-Asset Portfolio")
    print("="*70)

    broker = YFinanceBroker(initial_capital=50000, commission_pct=0.001)
    await broker.initialize()

    # Portfolio allocation
    trades = [
        ('AAPL', 'stock', 20),      # 20 shares Apple
        ('MSFT', 'stock', 15),      # 15 shares Microsoft
        ('SPY', 'etf', 10),         # 10 shares S&P 500 ETF
        ('QQQ', 'etf', 10),         # 10 shares NASDAQ ETF
        ('BTC-USD', 'crypto', 0.05), # 0.05 BTC
        ('ETH-USD', 'crypto', 0.5),  # 0.5 ETH
    ]

    print("\n--- Building Multi-Asset Portfolio ---")
    for symbol, asset_type, quantity in trades:
        result = await broker.place_market_order(symbol, 'BUY', quantity)
        if result.success:
            print(f"  ✓ {symbol:10} ({asset_type:10}): {quantity:6} @ ${result.avg_price:10,.2f}")
        else:
            print(f"  ✗ {symbol}: {result.error_message}")

    # Portfolio summary
    print("\n--- Portfolio Summary ---")
    positions = await broker.get_positions()
    total_value = 0

    for pos in positions:
        value = pos.quantity * (pos.current_price or pos.entry_price)
        total_value += value
        pnl_pct = ((pos.current_price / pos.entry_price) - 1) * 100 if pos.current_price else 0

        print(f"  {pos.symbol:10} | Qty: {pos.quantity:8.4f} | "
              f"Value: ${value:10,.2f} | P&L: {pnl_pct:+6.2f}%")

    balances = await broker.get_account_balance()
    cash = balances['USD'].total
    portfolio_value = cash + total_value

    print(f"\n  Cash:            ${cash:,.2f}")
    print(f"  Invested:        ${total_value:,.2f}")
    print(f"  Portfolio Value: ${portfolio_value:,.2f}")

    stats = broker.get_statistics()
    print(f"  Total Return:    {stats['total_return_pct']:+.2f}%")

    await broker.shutdown()


async def example_4_data_extraction():
    """Example 4: Using yFinance extractor for data"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Data Extraction with yFinance")
    print("="*70)

    extractor = YFinanceExtractor()

    # Download historical data for AAPL
    print("\n--- Downloading AAPL Historical Data (1 month, 1 day) ---")
    aapl_data = await extractor.download_historical(
        symbol='AAPL',
        period='1mo',
        interval='1d',
        asset_type='stock'
    )
    print(f"  Downloaded {len(aapl_data)} candles")
    print(aapl_data[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail())

    # Get current price
    print("\n--- Current Prices ---")
    symbols = ['AAPL', 'MSFT', 'BTC-USD', 'ETH-USD', 'SPY']
    for symbol in symbols:
        asset_type = 'crypto' if '-USD' in symbol else 'stock'
        price = await extractor.get_current_price(symbol, asset_type)
        print(f"  {symbol:10}: ${price:,.2f}")

    # Get ticker info
    print("\n--- Ticker Information ---")
    info = await extractor.get_ticker_info('AAPL', 'stock')
    print(f"  Name:     {info.get('name')}")
    print(f"  Exchange: {info.get('exchange')}")
    print(f"  Sector:   {info.get('sector')}")
    print(f"  Industry: {info.get('industry')}")


async def example_5_multi_source_extractor():
    """Example 5: Using multi-source extractor (Binance + yFinance)"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Multi-Source Data Extraction")
    print("="*70)

    extractor = MultiSourceExtractor()

    # Test symbol detection
    print("\n--- Symbol Detection ---")
    test_symbols = ['BTCUSDT', 'AAPL', 'BTC-USD', 'SPY', 'EURUSD=X', 'ETHUSDT']
    for symbol in test_symbols:
        source, asset_type = extractor.detect_source(symbol)
        print(f"  {symbol:12} -> {source:10} ({asset_type})")

    # Download from multiple sources
    print("\n--- Downloading from Multiple Sources ---")

    # Binance crypto
    print("\n  Downloading BTCUSDT from Binance...")
    try:
        btc_binance = await extractor.download_historical(
            symbol='BTCUSDT',
            interval='1d'
        )
        print(f"  ✓ Downloaded {len(btc_binance)} candles from Binance")
    except Exception as e:
        print(f"  ✗ Binance error: {e}")

    # yFinance stock
    print("\n  Downloading AAPL from yFinance...")
    aapl_yf = await extractor.download_historical(
        symbol='AAPL',
        period='1mo',
        interval='1d'
    )
    print(f"  ✓ Downloaded {len(aapl_yf)} candles from yFinance")

    # Get current prices
    print("\n--- Current Prices (Multi-Source) ---")
    for symbol in ['BTCUSDT', 'AAPL', 'BTC-USD']:
        try:
            price = await extractor.get_current_price(symbol)
            source, _ = extractor.detect_source(symbol)
            print(f"  {symbol:12} (${price:12,.2f}) <- {source}")
        except Exception as e:
            print(f"  {symbol:12} Error: {e}")


async def example_6_trading_strategy_simulation():
    """Example 6: Simple trading strategy simulation"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Trading Strategy Simulation")
    print("="*70)

    broker = YFinanceBroker(initial_capital=10000)
    await broker.initialize()

    extractor = YFinanceExtractor()

    # Simulate a simple strategy: buy AAPL if RSI < 30 (oversold)
    symbol = 'AAPL'
    print(f"\n--- Simulating Strategy for {symbol} ---")

    # Download historical data
    data = await extractor.download_historical(
        symbol=symbol,
        period='3mo',
        interval='1d',
        asset_type='stock'
    )

    # Simple RSI calculation (14-period)
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    data['rsi'] = rsi

    # Get latest RSI
    latest_rsi = data['rsi'].iloc[-1]
    latest_price = data['close'].iloc[-1]

    print(f"\n  Latest Price: ${latest_price:.2f}")
    print(f"  Latest RSI:   {latest_rsi:.2f}")

    # Trading decision
    if latest_rsi < 30:
        print(f"\n  → RSI < 30 (Oversold) - BUY SIGNAL")
        result = await broker.place_market_order(symbol, 'BUY', 10)
        if result.success:
            print(f"  ✓ Bought 10 shares at ${result.avg_price:.2f}")
    elif latest_rsi > 70:
        print(f"\n  → RSI > 70 (Overbought) - SELL SIGNAL")
        # Check if we have position
        positions = await broker.get_positions()
        if any(p.symbol == symbol for p in positions):
            result = await broker.place_market_order(symbol, 'SELL', 10)
            if result.success:
                print(f"  ✓ Sold 10 shares at ${result.avg_price:.2f}")
    else:
        print(f"\n  → RSI neutral ({latest_rsi:.1f}) - NO SIGNAL")

    # Final stats
    stats = broker.get_statistics()
    print(f"\n--- Final Statistics ---")
    print(f"  Total Trades: {stats['total_trades']}")
    print(f"  P&L:          ${stats['total_pnl']:+.2f}")

    await broker.shutdown()


async def main():
    """Run all examples"""
    print("\n" + "="*70)
    print(" yFinance Paper Trading - Examples")
    print("="*70)

    examples = [
        ("Basic Paper Trading", example_1_basic_paper_trading),
        ("Crypto Paper Trading", example_2_crypto_paper_trading),
        ("Multi-Asset Portfolio", example_3_multi_asset_portfolio),
        ("Data Extraction", example_4_data_extraction),
        ("Multi-Source Extractor", example_5_multi_source_extractor),
        ("Trading Strategy Simulation", example_6_trading_strategy_simulation),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print(f"  0. Run all examples")

    choice = input("\nSelect example (0-6): ").strip()

    if choice == '0':
        for name, func in examples:
            try:
                await func()
            except Exception as e:
                logger.error(f"Error in {name}: {e}", exc_info=True)
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        name, func = examples[int(choice) - 1]
        try:
            await func()
        except Exception as e:
            logger.error(f"Error in {name}: {e}", exc_info=True)
    else:
        print("Invalid choice")

    print("\n" + "="*70)
    print(" Examples completed!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
