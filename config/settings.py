"""
Configurazione principale del Trading System
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# BINANCE CONFIGURATION
# ============================================================================
BINANCE_CONFIG = {
    'api_key': os.getenv('BINANCE_API_KEY'),
    'api_secret': os.getenv('BINANCE_API_SECRET'),
    'testnet': False,  # True per testare su Binance Testnet
}

# ============================================================================
# TRADING CONFIGURATION
# ============================================================================
TRADING_CONFIG = {
    # Capital Management
    'initial_capital': 10000,           # Capitale iniziale ($)
    'position_size_pct': 2.0,           # % del capitale per singolo trade
    'max_positions': 3,                 # Massimo posizioni contemporanee
    'min_trade_size_usdt': 10,          # Minimo size trade in USDT

    # Take Profit / Stop Loss per singolo trade
    'take_profit_pct': 2.0,             # 2% profit → chiudi trade
    'stop_loss_pct': 1.0,               # 1% loss → chiudi trade

    # Take Profit / Stop Loss FINAL (giornaliero)
    'take_profit_final': 500,           # $ di profitto → blocco sistema
    'stop_loss_final': -200,            # $ di perdita → blocco sistema
    'final_limits_enabled': True,       # Abilita TP/SL final

    # Trailing Stop
    'trailing_stop_enabled': False,
    'trailing_stop_pct': 0.5,           # Trailing stop al 0.5%

    # Risk Management
    'max_daily_trades': 20,             # Max trade al giorno
    'max_drawdown_pct': 10,             # Max drawdown consentito (%)
    'risk_per_trade_pct': 1.0,          # Risk per trade (% del capitale)
}

# ============================================================================
# LLM PLUGIN CONFIGURATION
# ============================================================================
LLM_CONFIG = {
    'enabled': True,                    # Abilita plugin LLM
    'provider': 'anthropic',            # 'anthropic' o 'openai'
    'api_key': os.getenv('ANTHROPIC_API_KEY'),  # o OPENAI_API_KEY
    'model': 'claude-3-5-sonnet-20241022',      # o 'gpt-4-turbo'
    'temperature': 0.3,                 # Temperatura per risposte
    'max_tokens': 500,                  # Max tokens risposta
    'timeout': 10,                      # Timeout richiesta (secondi)
    'retry_on_error': True,             # Retry se errore
    'fallback_to_approve': False,       # Se LLM offline, approva comunque?
}

# ============================================================================
# TELEGRAM CONFIGURATION
# ============================================================================
TELEGRAM_CONFIG = {
    'enabled': True,
    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
    'chat_id': os.getenv('TELEGRAM_CHAT_ID'),

    # Tipi di notifiche
    'notify_trades': True,              # Notifica ogni trade
    'notify_daily_stats': True,         # Statistiche giornaliere
    'notify_final_limits': True,        # Avviso TP/SL final
    'notify_errors': True,              # Notifica errori

    # Orari report
    'daily_report_time': '18:30',       # Ora report giornaliero
    'send_charts': True,                # Invia grafici
}

# ============================================================================
# AUDIO NOTIFICATIONS
# ============================================================================
AUDIO_CONFIG = {
    'enabled': True,
    'sounds_dir': 'sounds/',
    'volume': 0.7,                      # Volume (0.0 - 1.0)

    # File audio
    'buy_sound': 'order_filled_buy.wav',
    'sell_sound': 'order_filled_sell.wav',
    'alert_sound': 'alert.wav',
}

# ============================================================================
# DATA EXTRACTION
# ============================================================================
EXTRACTION_CONFIG = {
    'data_dir': 'data/',
    'raw_dir': 'data/raw/',
    'processed_dir': 'data/processed/',
    'backtest_dir': 'data/backtest/',

    # Formato salvataggio
    'format': 'parquet',                # 'parquet' o 'csv'
    'compression': 'snappy',            # Compressione parquet

    # Retention dati
    'keep_raw_days': 7,                 # Giorni di retention dati raw
    'keep_processed_days': 30,          # Giorni di retention dati processed

    # WebSocket
    'websocket_reconnect': True,
    'websocket_ping_interval': 20,
}

# ============================================================================
# ETL CONFIGURATION
# ============================================================================
ETL_CONFIG = {
    # Indicatori da calcolare
    'indicators': [
        'sma_20', 'sma_50', 'sma_200',  # Simple Moving Average
        'ema_12', 'ema_26',              # Exponential Moving Average
        'rsi_14',                        # RSI
        'macd',                          # MACD
        'bollinger_bands',               # Bande di Bollinger
        'atr_14',                        # Average True Range
        'volume_sma_20',                 # Volume media
        'adaptive_supertrend',           # Adaptive SuperTrend con K-Means clustering
    ],

    # Parametri indicatori
    'rsi_period': 14,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'bollinger_period': 20,
    'bollinger_std': 2,
    'atr_period': 14,

    # Adaptive SuperTrend parameters
    'adaptive_supertrend_atr_period': 10,      # Periodo ATR per SuperTrend
    'adaptive_supertrend_multiplier': 3.0,     # Moltiplicatore bande SuperTrend
    'adaptive_supertrend_training_period': 100, # Finestra K-Means clustering
}

# ============================================================================
# BACKTESTING
# ============================================================================
BACKTEST_CONFIG = {
    'commission': 0.001,                # 0.1% commissione Binance
    'slippage': 0.0005,                 # 0.05% slippage
    'initial_capital': 10000,
    'position_size_pct': 2.0,

    # Metriche da calcolare
    'calculate_metrics': [
        'total_return',
        'sharpe_ratio',
        'max_drawdown',
        'win_rate',
        'profit_factor',
        'avg_trade_duration',
    ],
}

# ============================================================================
# LOGGING
# ============================================================================
LOGGING_CONFIG = {
    'level': 'INFO',                    # DEBUG, INFO, WARNING, ERROR
    'log_dir': 'logs/',
    'log_file': 'trading.log',
    'max_file_size': 10 * 1024 * 1024,  # 10 MB
    'backup_count': 5,                  # Numero file di backup
    'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}',
}

# ============================================================================
# ADVANCED FEATURES
# ============================================================================
ADVANCED_CONFIG = {
    # Portfolio rebalancing
    'rebalancing_enabled': False,
    'rebalancing_frequency': '1d',      # Ogni giorno

    # Multi-timeframe analysis
    'multi_timeframe_enabled': True,
    'timeframes': ['5m', '15m', '1h'],

    # Volatility adjustment
    'volatility_adjustment': True,
    'reduce_size_on_high_volatility': True,
}

# ============================================================================
# EXPORT COMPLETO
# ============================================================================
CONFIG = {
    'binance': BINANCE_CONFIG,
    'trading': TRADING_CONFIG,
    'llm': LLM_CONFIG,
    'telegram': TELEGRAM_CONFIG,
    'audio': AUDIO_CONFIG,
    'extraction': EXTRACTION_CONFIG,
    'etl': ETL_CONFIG,
    'backtest': BACKTEST_CONFIG,
    'logging': LOGGING_CONFIG,
    'advanced': ADVANCED_CONFIG,
}
