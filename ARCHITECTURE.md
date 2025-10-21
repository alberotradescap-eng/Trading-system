# Trading System Architecture - Crypto Trading Platform

## Panoramica del Sistema

Sistema di trading automatizzato per criptovalute con focus su Binance, che include:
- Estrazione dati realtime
- Regole di trading personalizzabili
- Sistema di notifiche sonore e Telegram
- Plugin LLM per consenso ai trade
- Backtesting engine
- Gestione avanzata di TP/SL con sistema di blocco finale

## Architettura dei Componenti

```
trading-system/
├── config/                          # Configurazioni
│   ├── trading_rules.py            # Regole di entry/exit
│   ├── symbols.yaml                # Crypto da tradare
│   ├── schedule.yaml               # Orari di trading
│   └── settings.py                 # Impostazioni generali
│
├── extractors/                      # Estrazione dati da Binance
│   ├── __init__.py
│   ├── binance_extractor.py        # Connessione Binance WebSocket/REST
│   ├── kline_extractor.py          # Estrazione candele
│   ├── orderbook_extractor.py      # Estrazione order book
│   └── trades_extractor.py         # Estrazione trades
│
├── data/                            # Dati estratti (output extractors)
│   ├── raw/                        # Dati grezzi da Binance
│   │   ├── klines/
│   │   ├── orderbook/
│   │   └── trades/
│   ├── processed/                  # Dati processati da ETL
│   │   ├── indicators/
│   │   ├── signals/
│   │   └── aggregated/
│   └── backtest/                   # Dati per backtesting
│
├── etl/                             # Trasformazione dati
│   ├── __init__.py
│   ├── data_cleaner.py             # Pulizia dati
│   ├── indicator_calculator.py     # Calcolo indicatori tecnici
│   ├── feature_engineering.py      # Feature engineering
│   └── data_aggregator.py          # Aggregazione timeframes
│
├── engine/                          # Motore di calcolo e decisioni
│   ├── __init__.py
│   ├── signal_generator.py         # Generazione segnali buy/sell
│   ├── position_manager.py         # Gestione posizioni
│   ├── risk_manager.py             # Gestione rischio (TP/SL)
│   └── portfolio_manager.py        # Gestione portfolio
│
├── broker/                          # Interfaccia con broker
│   ├── __init__.py
│   ├── binance_client.py           # Client Binance
│   ├── order_executor.py           # Esecuzione ordini
│   └── account_monitor.py          # Monitoraggio account
│
├── plugins/                         # Sistema plugin LLM
│   ├── __init__.py
│   ├── llm_advisor.py              # Interfaccia con LLM
│   ├── prompt_templates.py         # Template prompt per LLM
│   └── consent_manager.py          # Gestione consenso trade
│
├── notifications/                   # Sistema notifiche
│   ├── __init__.py
│   ├── audio_notifier.py           # Notifiche sonore
│   ├── telegram_notifier.py        # Notifiche Telegram
│   └── report_generator.py         # Generazione report e grafici
│
├── backtesting/                     # Motore backtesting
│   ├── __init__.py
│   ├── backtest_engine.py          # Engine principale
│   ├── performance_analyzer.py     # Analisi performance
│   └── visualizer.py               # Visualizzazione risultati
│
├── utils/                           # Utilities
│   ├── __init__.py
│   ├── logger.py                   # Logging
│   ├── file_manager.py             # Gestione file
│   └── scheduler.py                # Scheduling operazioni
│
├── sounds/                          # File audio
│   ├── order_filled_buy.wav
│   └── order_filled_sell.wav
│
├── main.py                          # Entry point principale
├── backtest.py                      # Entry point backtesting
└── requirements.txt                 # Dipendenze Python
```

---

## 1. Extractors (Estrazione Dati)

### Funzionalità
- Connessione a Binance WebSocket per dati realtime
- Estrazione di:
  - Candele (klines) multi-timeframe
  - Order book depth
  - Trade execution stream
- Salvataggio dati in `data/raw/` in formato CSV/Parquet

### Esempio: `extractors/binance_extractor.py`
```python
class BinanceExtractor:
    def __init__(self, symbols, output_dir='data/raw'):
        self.symbols = symbols
        self.output_dir = output_dir

    def start_kline_stream(self, symbol, interval='1m'):
        # WebSocket stream per candele realtime
        # Salva su data/raw/klines/{symbol}_{interval}_{date}.csv
        pass

    def start_orderbook_stream(self, symbol):
        # Stream order book
        # Salva su data/raw/orderbook/{symbol}_{date}.csv
        pass
```

---

## 2. ETL (Trasformazione Dati)

### Funzionalità
- Caricamento dati da `data/raw/`
- Calcolo indicatori tecnici (RSI, MACD, Bollinger Bands, etc.)
- Feature engineering
- Salvataggio in `data/processed/`

### Esempio: `etl/indicator_calculator.py`
```python
class IndicatorCalculator:
    def calculate_indicators(self, df):
        # Calcola RSI, MACD, SMA, EMA, etc.
        df['rsi'] = self.calculate_rsi(df['close'])
        df['macd'], df['signal'] = self.calculate_macd(df['close'])
        return df

    def save_processed_data(self, df, output_path):
        # Salva in data/processed/indicators/
        df.to_parquet(output_path)
```

---

## 3. Engine (Motore di Calcolo)

### Signal Generator
Genera segnali di buy/sell basati su regole definite dall'utente.

### Risk Manager
Gestisce:
- **Stop Loss**: Limite di perdita per trade
- **Take Profit**: Limite di profitto per trade
- **Stop Loss FINAL**: Perdita massima giornaliera → blocco sistema
- **Take Profit FINAL**: Profitto target giornaliero → blocco sistema

### Esempio: `config/trading_rules.py`
```python
class TradingRules:
    def entry_long(self, data):
        """
        Definisci regole di entry per posizione LONG
        """
        return (
            data['rsi'] < 30 and
            data['close'] > data['sma_20'] and
            data['macd'] > data['signal']
        )

    def entry_short(self, data):
        """
        Definisci regole di entry per posizione SHORT
        """
        return (
            data['rsi'] > 70 and
            data['close'] < data['sma_20'] and
            data['macd'] < data['signal']
        )

    def exit_long(self, data, entry_price):
        """
        Regole di exit per LONG
        """
        current_price = data['close']
        profit_pct = (current_price - entry_price) / entry_price * 100

        # Take profit
        if profit_pct >= 2.0:
            return True, 'take_profit'

        # Stop loss
        if profit_pct <= -1.0:
            return True, 'stop_loss'

        # Exit su segnale tecnico
        if data['rsi'] > 70:
            return True, 'signal'

        return False, None
```

### Position Manager
```python
class PositionManager:
    def __init__(self):
        self.positions = {}
        self.daily_pnl = 0
        self.is_blocked = False

    def check_final_limits(self, config):
        """
        Controlla TP/SL FINAL
        """
        if self.daily_pnl >= config['take_profit_final']:
            self.is_blocked = True
            return 'TAKE_PROFIT_FINAL_REACHED'

        if self.daily_pnl <= config['stop_loss_final']:
            self.is_blocked = True
            return 'STOP_LOSS_FINAL_REACHED'

        return None

    def unlock_system(self):
        """
        Sblocca il sistema manualmente
        """
        self.is_blocked = False
        self.daily_pnl = 0
```

---

## 4. Plugin LLM (Consenso AI)

### Funzionalità
Prima di eseguire un trade, chiede conferma a un LLM (es. Claude, GPT-4).

### Esempio: `plugins/llm_advisor.py`
```python
class LLMAdvisor:
    def __init__(self, api_key, model='claude-3-5-sonnet'):
        self.api_key = api_key
        self.model = model

    def ask_trade_consent(self, signal_data):
        """
        Chiede consenso all'LLM per il trade
        """
        prompt = f"""
        Analizza questa opportunità di trading:

        Symbol: {signal_data['symbol']}
        Type: {signal_data['type']}  # BUY/SELL
        Price: {signal_data['price']}
        RSI: {signal_data['rsi']}
        MACD: {signal_data['macd']}
        Volume: {signal_data['volume']}

        Market context:
        {signal_data['market_context']}

        Dovrei eseguire questo trade? Rispondi APPROVE o REJECT con motivazione.
        """

        response = self.call_llm(prompt)
        return 'APPROVE' in response, response
```

---

## 5. Broker Interface

### Esempio: `broker/order_executor.py`
```python
class OrderExecutor:
    def __init__(self, binance_client):
        self.client = binance_client

    def execute_market_order(self, symbol, side, quantity):
        """
        Esegue ordine di mercato
        """
        order = self.client.create_order(
            symbol=symbol,
            side=side,  # BUY/SELL
            type='MARKET',
            quantity=quantity
        )
        return order

    def execute_limit_order(self, symbol, side, quantity, price):
        """
        Esegue ordine limit con TP/SL
        """
        order = self.client.create_order(
            symbol=symbol,
            side=side,
            type='LIMIT',
            quantity=quantity,
            price=price,
            stopPrice=stop_price,
            takeProfitPrice=take_profit_price
        )
        return order
```

---

## 6. Notifications (Notifiche)

### Audio Notifier
```python
import pygame

class AudioNotifier:
    def __init__(self, sounds_dir='sounds/'):
        pygame.mixer.init()
        self.buy_sound = pygame.mixer.Sound(f'{sounds_dir}order_filled_buy.wav')
        self.sell_sound = pygame.mixer.Sound(f'{sounds_dir}order_filled_sell.wav')

    def play_buy_filled(self):
        self.buy_sound.play()

    def play_sell_filled(self):
        self.sell_sound.play()
```

### Telegram Notifier
```python
import telegram

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot = telegram.Bot(token=bot_token)
        self.chat_id = chat_id

    def send_trade_notification(self, order_info):
        message = f"""
        🤖 TRADE EXECUTED

        Symbol: {order_info['symbol']}
        Type: {order_info['side']}
        Price: {order_info['price']}
        Quantity: {order_info['quantity']}
        Time: {order_info['timestamp']}
        """
        self.bot.send_message(chat_id=self.chat_id, text=message)

    def send_daily_stats(self, stats):
        message = f"""
        📊 DAILY STATISTICS

        Total Trades: {stats['total_trades']}
        Win Rate: {stats['win_rate']}%
        PnL: ${stats['pnl']:.2f}
        Best Trade: ${stats['best_trade']:.2f}
        Worst Trade: ${stats['worst_trade']:.2f}
        """
        self.bot.send_message(chat_id=self.chat_id, text=message)

    def send_chart(self, chart_path):
        with open(chart_path, 'rb') as f:
            self.bot.send_photo(chat_id=self.chat_id, photo=f)
```

---

## 7. Backtesting Engine

### Esempio: `backtesting/backtest_engine.py`
```python
class BacktestEngine:
    def __init__(self, data_path, strategy, initial_capital=10000):
        self.data = pd.read_parquet(data_path)
        self.strategy = strategy
        self.initial_capital = initial_capital

    def run(self):
        """
        Esegue backtest su dati storici
        """
        portfolio_value = self.initial_capital
        positions = []

        for idx, row in self.data.iterrows():
            # Controlla segnali entry
            if self.strategy.entry_long(row):
                positions.append({
                    'type': 'LONG',
                    'entry_price': row['close'],
                    'entry_time': row['timestamp']
                })

            # Controlla exit per posizioni aperte
            for pos in positions:
                should_exit, reason = self.strategy.exit_long(row, pos['entry_price'])
                if should_exit:
                    pnl = self.calculate_pnl(pos, row['close'])
                    portfolio_value += pnl
                    positions.remove(pos)

        return self.generate_report(portfolio_value, positions)
```

---

## 8. Configurazione Trading

### `config/symbols.yaml`
```yaml
symbols:
  - BTCUSDT
  - ETHUSDT
  - SOLUSDT
  - BNBUSDT

timeframes:
  - 1m
  - 5m
  - 15m
  - 1h
```

### `config/schedule.yaml`
```yaml
trading_schedule:
  enabled: true
  timezone: 'Europe/Rome'

  # Trading attivo solo in questi giorni
  active_days:
    - monday
    - tuesday
    - wednesday
    - thursday
    - friday

  # Orari di trading (ogni giorno)
  trading_hours:
    start: "09:00"
    end: "18:00"

  # Pausa pranzo (opzionale)
  pause:
    enabled: true
    start: "12:00"
    end: "13:00"
```

### `config/settings.py`
```python
TRADING_CONFIG = {
    # Risk Management
    'position_size_pct': 2.0,  # % del capitale per trade
    'max_positions': 3,         # Massimo posizioni contemporanee

    # Take Profit / Stop Loss per trade
    'take_profit_pct': 2.0,
    'stop_loss_pct': 1.0,

    # Take Profit / Stop Loss FINAL (giornaliero)
    'take_profit_final': 500,   # $ profitto → blocco
    'stop_loss_final': -200,    # $ perdita → blocco

    # LLM Plugin
    'llm_enabled': True,
    'llm_provider': 'anthropic',  # o 'openai'
    'llm_api_key': 'your-api-key',

    # Telegram
    'telegram_enabled': True,
    'telegram_bot_token': 'your-bot-token',
    'telegram_chat_id': 'your-chat-id',

    # Audio
    'audio_enabled': True,
}
```

---

## 9. Main Entry Point

### `main.py`
```python
import asyncio
from extractors.binance_extractor import BinanceExtractor
from etl.indicator_calculator import IndicatorCalculator
from engine.signal_generator import SignalGenerator
from engine.position_manager import PositionManager
from broker.order_executor import OrderExecutor
from plugins.llm_advisor import LLMAdvisor
from notifications.audio_notifier import AudioNotifier
from notifications.telegram_notifier import TelegramNotifier
from utils.scheduler import TradingScheduler
from config.settings import TRADING_CONFIG
from config.trading_rules import TradingRules

class TradingSystem:
    def __init__(self, config):
        self.config = config

        # Inizializza componenti
        self.extractor = BinanceExtractor(symbols=config['symbols'])
        self.etl = IndicatorCalculator()
        self.signal_gen = SignalGenerator(TradingRules())
        self.position_mgr = PositionManager()
        self.order_exec = OrderExecutor()
        self.llm = LLMAdvisor(config['llm_api_key'])
        self.audio = AudioNotifier()
        self.telegram = TelegramNotifier(
            config['telegram_bot_token'],
            config['telegram_chat_id']
        )
        self.scheduler = TradingScheduler(config['schedule'])

    async def run(self):
        """
        Loop principale del sistema
        """
        # 1. Avvia extractors in background
        await self.extractor.start_streams()

        while True:
            # 2. Controlla se siamo in orario di trading
            if not self.scheduler.is_trading_time():
                await asyncio.sleep(60)
                continue

            # 3. Controlla blocco FINAL TP/SL
            if self.position_mgr.is_blocked:
                print("Sistema bloccato per TP/SL FINAL raggiunto")
                await asyncio.sleep(60)
                continue

            # 4. Carica ultimi dati
            raw_data = self.load_latest_data()

            # 5. Processa con ETL
            processed_data = self.etl.calculate_indicators(raw_data)

            # 6. Genera segnali
            signals = self.signal_gen.generate_signals(processed_data)

            # 7. Per ogni segnale
            for signal in signals:
                # 7a. Chiedi consenso LLM
                if self.config['llm_enabled']:
                    approved, reason = self.llm.ask_trade_consent(signal)
                    if not approved:
                        print(f"Trade rifiutato da LLM: {reason}")
                        continue

                # 7b. Esegui ordine
                order = self.order_exec.execute_market_order(
                    symbol=signal['symbol'],
                    side=signal['side'],
                    quantity=signal['quantity']
                )

                # 7c. Notifiche
                if signal['side'] == 'BUY':
                    self.audio.play_buy_filled()
                else:
                    self.audio.play_sell_filled()

                self.telegram.send_trade_notification(order)

                # 7d. Aggiorna posizioni
                self.position_mgr.add_position(order)

            # 8. Gestisci posizioni aperte (check TP/SL)
            self.position_mgr.manage_positions(processed_data)

            # 9. Controlla TP/SL FINAL
            final_status = self.position_mgr.check_final_limits(self.config)
            if final_status:
                self.telegram.send_message(f"⚠️ {final_status}")

            # 10. Sleep
            await asyncio.sleep(1)

    def load_latest_data(self):
        # Carica ultimi dati da data/raw/
        pass

if __name__ == '__main__':
    system = TradingSystem(TRADING_CONFIG)
    asyncio.run(system.run())
```

---

## 10. Backtesting Entry Point

### `backtest.py`
```python
from backtesting.backtest_engine import BacktestEngine
from config.trading_rules import TradingRules
import matplotlib.pyplot as plt

def run_backtest():
    # Carica dati storici
    data_path = 'data/backtest/BTCUSDT_2024.parquet'

    # Inizializza backtest
    engine = BacktestEngine(
        data_path=data_path,
        strategy=TradingRules(),
        initial_capital=10000
    )

    # Esegui backtest
    results = engine.run()

    # Visualizza risultati
    print(f"Initial Capital: ${results['initial_capital']}")
    print(f"Final Capital: ${results['final_capital']}")
    print(f"Total Return: {results['total_return_pct']}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']}")
    print(f"Max Drawdown: {results['max_drawdown']}%")
    print(f"Win Rate: {results['win_rate']}%")

    # Plot equity curve
    plt.figure(figsize=(12, 6))
    plt.plot(results['equity_curve'])
    plt.title('Equity Curve')
    plt.xlabel('Time')
    plt.ylabel('Portfolio Value ($)')
    plt.savefig('backtest_results.png')

if __name__ == '__main__':
    run_backtest()
```

---

## Dipendenze Python

### `requirements.txt`
```
# Binance
python-binance==1.0.19
ccxt==4.2.0

# Data processing
pandas==2.1.4
numpy==1.26.2
ta-lib==0.4.28  # Indicatori tecnici
pyarrow==14.0.1  # Per Parquet

# Backtesting
backtrader==1.9.78.123
vectorbt==0.26.0

# LLM
anthropic==0.18.1
openai==1.12.0

# Notifications
python-telegram-bot==20.7
pygame==2.5.2  # Audio

# Visualization
matplotlib==3.8.2
plotly==5.18.0
seaborn==0.13.0

# Utils
pyyaml==6.0.1
python-dotenv==1.0.0
schedule==1.2.0
aiohttp==3.9.1
websockets==12.0

# Logging
loguru==0.7.2
```

---

## Flusso di Esecuzione

### 1. **Modalità Live Trading**
```
Extractors → data/raw → ETL → data/processed → Engine → Segnali
                                                           ↓
                                                    LLM Plugin (consenso)
                                                           ↓
                                          Broker → Esecuzione ordini
                                                           ↓
                                          Notifiche (Audio + Telegram)
```

### 2. **Modalità Backtesting**
```
data/backtest → Backtest Engine → Performance Analysis → Report + Charts
```

---

## Features Avanzate

### 1. **Sistema di Blocco FINAL**
- Quando il PnL giornaliero raggiunge il TP/SL FINAL, il sistema si blocca
- Non vengono eseguiti nuovi trade
- Richiede sblocco manuale via comando o API

### 2. **LLM Trading Advisor**
- Prima di ogni trade, invia contesto al LLM
- LLM analizza: indicatori tecnici, sentiment, contesto di mercato
- LLM risponde: APPROVE/REJECT
- Trade eseguito solo se approvato

### 3. **Scheduling Intelligente**
- Trading solo in giorni/orari specifici
- Supporto timezone
- Pause automatiche
- Stop weekend/festivi

### 4. **Multi-Symbol Trading**
- Gestione simultanea di multiple crypto
- Correlazione tra asset
- Diversificazione automatica

### 5. **Notifiche Complete**
- Audio immediato all'esecuzione
- Telegram per ogni trade
- Report giornalieri automatici
- Grafici equity curve e drawdown

---

## Comandi Utili

### Avvio Sistema Live
```bash
python main.py --mode live --symbols BTCUSDT,ETHUSDT
```

### Backtesting
```bash
python backtest.py --symbol BTCUSDT --start 2024-01-01 --end 2024-12-31
```

### Sblocco Sistema dopo FINAL TP/SL
```bash
python main.py --unlock
```

### Download Dati Storici
```bash
python extractors/download_historical.py --symbol BTCUSDT --start 2023-01-01
```

---

## Sicurezza

1. **API Keys**: Memorizzate in `.env`, mai in codice
2. **Logging**: Tutti i trade loggati per audit
3. **Rate Limiting**: Rispetto limiti API Binance
4. **Error Handling**: Retry automatici con exponential backoff
5. **Position Limits**: Massimo capitale allocato per trade
6. **Final TP/SL**: Protezione da perdite eccessive

---

## Estensibilità

- **Nuovi Extractors**: Aggiungi connettori per altri exchange
- **Nuovi Indicatori**: Estendi `etl/indicator_calculator.py`
- **Nuove Strategie**: Modifica `config/trading_rules.py`
- **Nuovi Plugin**: Crea plugin in `plugins/` per altre AI o servizi
- **Nuovi Notificatori**: Discord, Email, SMS, etc.

---

Questa architettura fornisce un sistema completo, modulare e scalabile per crypto trading con tutte le funzionalità richieste!
