# Adaptive SuperTrend Trading Engine - Version 17

## 🎉 Bug-Fixed and Enhanced Trading System

This is a **completely refactored and bug-fixed** version of the original Jupyter Notebook trading system. All critical bugs have been resolved, and the code has been restructured into a professional, modular architecture.

---

## ✨ What's New in Version 17

### Critical Bug Fixes
- ✅ **Fixed missing `seaborn` import** - Now handles gracefully with fallback
- ✅ **Implemented missing `compute_trailing_stop` function** - Complete trailing stop functionality
- ✅ **Replaced hardcoded Windows paths** - Now cross-platform compatible (Windows, Linux, macOS)
- ✅ **Added comprehensive error handling** - Better error messages and graceful degradation
- ✅ **Fixed global variable issues** - Proper encapsulation in classes
- ✅ **Resolved deprecation warnings** - Updated pandas methods (ffill vs fillna)

### Code Improvements
- 🏗️ **Modular architecture** - Split into logical modules
- 📝 **Complete documentation** - Docstrings for all functions
- ⚙️ **YAML configuration** - No more hardcoded parameters
- 🧪 **Comprehensive tests** - 12 automated tests verifying all functionality
- 📊 **Enhanced visualizations** - Better charts with fallback options
- 🔒 **Type hints** - Better IDE support and code clarity

---

## 📁 Project Structure

```
Trading-system/
├── engine/
│   ├── adaptive_supertrend_engine.py  # Core trading engine (NEW)
│   ├── performance_analytics.py       # Performance calculations (NEW)
│   └── __init__.py
├── config/
│   └── adaptive_supertrend_config.yaml  # Configuration file (NEW)
├── examples/
│   └── adaptive_supertrend_example.py   # Complete usage example (NEW)
├── data/                                # Data directory
├── reports/                             # Report output
├── logs/                                # Log files
├── test_bugfixes.py                     # Automated tests (NEW)
├── BUGFIXES.md                          # Detailed bug fix documentation (NEW)
└── requirements.txt                     # Updated dependencies
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
cd Trading-system

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Example

```bash
# Run the complete example with sample data
python examples/adaptive_supertrend_example.py
```

### 3. Run Tests

```bash
# Verify all bug fixes with automated tests
python test_bugfixes.py
```

---

## 💻 Usage Example

### Basic Usage

```python
from engine.adaptive_supertrend_engine import TradingEngine, TradingEngineConfig
from engine.performance_analytics import PerformanceAnalytics
import pandas as pd

# Initialize engine
config = TradingEngineConfig(base_path='.')
engine = TradingEngine(config=config)
analytics = PerformanceAnalytics(config=config)

# Load your data (OHLCV format)
dataset = pd.read_csv('your_data.csv')

# Define trading rules
enter_rules = dataset['adapt_supertrend_entry_long'] == 1
exit_rules = dataset['adapt_supertrend_exit_long'] == 1
enter_level = dataset['close']

# Apply trading system
trading_system = engine.apply_trading_system(
    imported_dataframe=dataset,
    bigpointvalue=5,
    tick=0.1,
    direction='long',
    order_type='market',
    enter_level=enter_level,
    enter_rules=enter_rules,
    exit_rules=exit_rules,
    operation_money=50000,
    costs=0,
    instrument=1,
    ticker='YOUR_SYMBOL',
    export_filename='trading_system.csv',
    simulation=True
)

# Generate performance report
operations = trading_system['operations'].dropna()
if len(operations) > 0:
    analytics.performance_report_console(
        trading_system,
        operations,
        trading_system['closed_equity'],
        trading_system['open_equity']
    )

    # Generate charts
    fig = analytics.plot_equity(trading_system['open_equity'])
    fig.savefig('equity_curve.png')
```

### With Configuration File

```python
import yaml

# Load configuration
with open('config/adaptive_supertrend_config.yaml', 'r') as f:
    config_dict = yaml.safe_load(f)

# Run trading system with config
# See examples/adaptive_supertrend_example.py for complete implementation
```

---

## 🔧 Configuration

Edit `config/adaptive_supertrend_config.yaml` to customize:

```yaml
trading:
  ticker: 'YOUR_SYMBOL'
  direction: 'long'  # or 'short'
  order_type: 'market'  # 'market', 'stop', 'limit', 'special'

risk:
  operation_money: 50000
  stop_loss:
    enabled: true
    percentage: 0.10  # 10%
  take_profit:
    enabled: true
    multiplier: 2.0  # 2x operation_money
  trailing_stop:
    enabled: false
    percentage: 0.003  # 0.3%

data:
  source_type: 'Adaptive-supertrend'
  filename: 'your_data.csv'
```

---

## 📊 Features

### Core Trading Engine
- ✅ Market position tracking
- ✅ Entry/exit signal processing
- ✅ Multiple order types (market, limit, stop, special)
- ✅ Support for stocks and futures
- ✅ Equity curve calculation
- ✅ P&L tracking

### Risk Management
- ✅ Stop loss
- ✅ Take profit
- ✅ Trailing stop
- ✅ Position sizing

### Performance Analytics
- ✅ Comprehensive metrics (profit factor, win rate, etc.)
- ✅ Drawdown analysis
- ✅ Equity curve visualization
- ✅ Trading signal charts
- ✅ Monthly/annual performance reports
- ✅ CSV export

### Visualization
- ✅ Equity curves
- ✅ Drawdown charts
- ✅ Trading signals on price charts
- ✅ Annual performance histograms
- ✅ Monthly performance heatmaps

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_bugfixes.py
```

Tests verify:
1. ✅ Module imports
2. ✅ Engine initialization
3. ✅ Sample data generation
4. ✅ Crossover/crossunder functions
5. ✅ Tick correction
6. ✅ Trailing stop calculation
7. ✅ Market position generation
8. ✅ Complete trading system
9. ✅ Performance analytics
10. ✅ Visualization functions
11. ✅ Stop loss/take profit
12. ✅ Path configuration

---

## 📈 Performance Metrics

The engine calculates:

- **Profit/Loss**: Total and per operation
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / gross loss
- **Average Trade**: Mean P&L per trade
- **Max Gain/Loss**: Best and worst trades
- **Drawdown**: Maximum and average drawdown
- **Peak Delay**: Time to recover from drawdowns
- **Reward/Risk Ratio**: Average win / average loss

---

## 🔍 Debugging

### Enable Verbose Mode

```python
# In your configuration
behavior:
  verbose: true
  debug_parameters: true
```

### Check Logs

```bash
# View logs directory
ls -la logs/

# View specific log
cat logs/trading_parameters_YOUR_SYMBOL.log
```

---

## 🛠️ Advanced Features

### Custom Indicators

```python
# Add your own indicators to the dataset
dataset['my_indicator'] = calculate_my_indicator(dataset)

# Use in entry/exit rules
enter_rules = dataset['my_indicator'] > threshold
```

### Multiple Strategies

```python
# Load different configurations for different strategies
strategy1_config = load_config('config/strategy1.yaml')
strategy2_config = load_config('config/strategy2.yaml')

# Run both strategies
results1 = run_trading_system(strategy1_config)
results2 = run_trading_system(strategy2_config)
```

### Portfolio Analysis

```python
# Combine multiple trading systems
portfolio_equity = (
    trading_system1['open_equity'] +
    trading_system2['open_equity'] +
    trading_system3['open_equity']
)

analytics.plot_equity(portfolio_equity)
```

---

## 📚 Documentation

- **[BUGFIXES.md](BUGFIXES.md)** - Detailed list of all bug fixes
- **[examples/adaptive_supertrend_example.py](examples/adaptive_supertrend_example.py)** - Complete usage example
- **[config/adaptive_supertrend_config.yaml](config/adaptive_supertrend_config.yaml)** - Configuration reference

---

## 🐛 Known Limitations

1. **Live Trading**: Broker integration functions are stubs and need implementation
2. **Telegram Bot**: Requires separate configuration
3. **Audio Notifications**: Requires pygame and sound files

---

## 🔮 Future Enhancements

Planned features for future versions:

- [ ] Complete broker integrations (Alpaca, Binance, Interactive Brokers)
- [ ] Web dashboard for real-time monitoring
- [ ] Walk-forward analysis for optimization
- [ ] Monte Carlo simulation
- [ ] Portfolio-level risk management
- [ ] Backtesting engine improvements
- [ ] Machine learning signal integration

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

This project is provided as-is for educational and research purposes.

---

## ⚠️ Disclaimer

**IMPORTANT**: This software is for educational and research purposes only.

- Past performance does not guarantee future results
- Trading involves risk of loss
- Test thoroughly in simulation before live trading
- Not financial advice - consult a financial advisor
- Use at your own risk

---

## 📞 Support

If you encounter issues:

1. Check the [BUGFIXES.md](BUGFIXES.md) documentation
2. Review the example code
3. Run the test suite to verify installation
4. Check data format matches expectations

---

## 🏆 Changelog

### Version 17 (Current) - 2025-10-22
- ✅ Fixed all critical bugs from Version 16
- ✅ Complete refactor to modular architecture
- ✅ Added comprehensive error handling
- ✅ Implemented missing functions
- ✅ Cross-platform compatibility
- ✅ YAML configuration system
- ✅ 12 automated tests
- ✅ Enhanced documentation

### Version 16 (Original)
- ❌ Multiple critical bugs
- ❌ Monolithic Jupyter notebook
- ❌ Windows-specific paths
- ❌ Missing functions
- ❌ Limited documentation

---

## 📊 Test Results

Latest test run (2025-10-22):

```
✅ All 12 tests passed successfully!

Bug fixes verified:
  1. ✅ Missing seaborn handled gracefully
  2. ✅ compute_trailing_stop function implemented
  3. ✅ Cross-platform path handling
  4. ✅ Proper error handling
  5. ✅ Modular code structure
  6. ✅ Performance analytics working
  7. ✅ Visualization functions working
  8. ✅ Stop loss/take profit implemented
  9. ✅ Market position generator working
 10. ✅ Tick correction functions working

🎉 Trading Engine V17 is ready for production use!
```

---

**Made with ❤️ for the trading community**

**Version**: 17.0.0
**Last Updated**: 2025-10-22
**Status**: ✅ Production Ready
