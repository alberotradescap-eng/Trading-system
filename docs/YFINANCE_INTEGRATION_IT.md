# Integrazione yFinance - Guida Completa

## Indice
1. [Introduzione](#introduzione)
2. [Caratteristiche](#caratteristiche)
3. [Installazione](#installazione)
4. [Architettura](#architettura)
5. [Componenti Principali](#componenti-principali)
6. [Guida Utilizzo](#guida-utilizzo)
7. [Esempi Pratici](#esempi-pratici)
8. [Paper Trading vs Live Trading](#paper-trading-vs-live-trading)
9. [Asset Supportati](#asset-supportati)
10. [Configurazione](#configurazione)
11. [FAQ](#faq)

---

## Introduzione

L'integrazione yFinance aggiunge al sistema di trading la possibilità di operare su **multiple asset class** (stocks, ETFs, crypto, forex, commodity) attraverso **paper trading** (simulazione senza rischi reali).

### Perché yFinance?

- **Multi-Asset**: Trade su azioni, ETF, crypto, forex, commodities
- **Paper Trading**: Testa strategie senza rischiare denaro reale
- **Dati Gratuiti**: Nessun costo per dati storici e real-time
- **Facile Integrazione**: Si integra perfettamente con il sistema esistente

### Broker Supportati

| Broker | Asset Type | Trading Mode | Status |
|--------|------------|--------------|--------|
| **Binance** | Crypto (BTCUSDT, ETHUSDT, etc.) | Live (Real Money) | ✅ Attivo |
| **yFinance** | Stocks, ETFs, Crypto, Forex | Paper Trading | ✅ Attivo |

---

## Caratteristiche

### ✅ Paper Trading Completo
- Simulazione realistica di ordini market, limit, stop-loss
- Commissioni e slippage configurabili
- Tracking P&L in tempo reale
- Report dettagliati

### ✅ Multi-Asset Support
- **Stocks**: AAPL, MSFT, GOOGL, TSLA, NVDA, etc.
- **ETFs**: SPY, QQQ, IWM, DIA, VOO, etc.
- **Crypto**: BTC-USD, ETH-USD, SOL-USD, etc.
- **Forex**: EURUSD=X, GBPUSD=X, USDJPY=X, etc.
- **Commodities**: GC=F (Gold), CL=F (Oil), etc.

### ✅ Data Extraction
- Dati storici (1m, 5m, 15m, 1h, 1d, 1wk, 1mo)
- Prezzi real-time
- Ticker info (nome, exchange, sector, etc.)
- Cache intelligente per limitare richieste

### ✅ Compatibilità
- Interfaccia comune con Binance broker
- Riutilizza indicatori tecnici esistenti
- Compatibile con strategie esistenti
- Notifiche Telegram/Audio

---

## Installazione

### 1. Installare Dipendenze

```bash
pip install -r requirements.txt
```

Le nuove dipendenze aggiunte:
```
yfinance==0.2.35          # yFinance API
pandas-datareader==0.10.0 # Alternative data sources
```

### 2. Verificare Installazione

```bash
python examples/yfinance_example.py
```

---

## Architettura

```
┌─────────────────────────────────────────────────────┐
│                  TRADING SYSTEM                      │
└─────────────────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────┐            ┌─────────────────┐
│ BINANCE BROKER  │            │ YFINANCE BROKER │
│  (Live Trading) │            │ (Paper Trading) │
└─────────────────┘            └─────────────────┘
         │                               │
         ▼                               ▼
┌─────────────────┐            ┌─────────────────┐
│ Binance API     │            │ yFinance API    │
│ • BTCUSDT       │            │ • AAPL, MSFT    │
│ • ETHUSDT       │            │ • BTC-USD       │
│ • SOLUSDT       │            │ • SPY, QQQ      │
│                 │            │ • EURUSD=X      │
└─────────────────┘            └─────────────────┘
```

### Multi-Source Extractor

```
┌────────────────────────────────┐
│   MultiSourceExtractor         │
│   (Smart Router)               │
└────────────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌──────────────┐  ┌──────────────┐
│   Binance    │  │   yFinance   │
│  Extractor   │  │  Extractor   │
└──────────────┘  └──────────────┘
```

---

## Componenti Principali

### 1. `broker/base_broker.py`
Classe base astratta per tutti i broker.

**Metodi principali:**
- `place_market_order()` - Ordine market
- `place_limit_order()` - Ordine limit
- `place_stop_loss()` - Stop loss
- `get_account_balance()` - Saldo account
- `get_positions()` - Posizioni aperte
- `get_current_price()` - Prezzo corrente

### 2. `broker/yfinance_broker.py`
Broker per paper trading con yFinance.

**Caratteristiche:**
- Paper trading simulato
- Commissioni: 0.1% default
- Slippage: 0.05% default
- Tracking P&L real-time
- Report dettagliati

**Esempio:**
```python
from broker.yfinance_broker import YFinanceBroker

# Inizializza broker
broker = YFinanceBroker(initial_capital=10000)
await broker.initialize()

# Compra 10 azioni Apple
result = await broker.place_market_order('AAPL', 'BUY', 10)
print(f"Prezzo: ${result.avg_price:.2f}")

# Controlla posizioni
positions = await broker.get_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.quantity} @ ${pos.entry_price:.2f}")
```

### 3. `extractors/yfinance_extractor.py`
Estrattore dati da yFinance.

**Metodi principali:**
- `download_historical()` - Dati storici OHLCV
- `get_current_price()` - Prezzo corrente
- `get_latest_data()` - Ultima candela
- `get_ticker_info()` - Info ticker

**Esempio:**
```python
from extractors.yfinance_extractor import YFinanceExtractor

extractor = YFinanceExtractor()

# Scarica dati storici
data = await extractor.download_historical(
    symbol='AAPL',
    period='1mo',
    interval='1d',
    asset_type='stock'
)

# Prezzo corrente
price = await extractor.get_current_price('AAPL', 'stock')
print(f"AAPL: ${price:.2f}")
```

### 4. `extractors/multi_source_extractor.py`
Router intelligente Binance + yFinance.

**Auto-detection simboli:**
- `BTCUSDT` → Binance (crypto)
- `AAPL` → yFinance (stock)
- `BTC-USD` → yFinance (crypto)
- `SPY` → yFinance (ETF)
- `EURUSD=X` → yFinance (forex)

**Esempio:**
```python
from extractors.multi_source_extractor import MultiSourceExtractor

extractor = MultiSourceExtractor()

# Auto-routing
source, asset_type = extractor.detect_source('BTCUSDT')
print(f"BTCUSDT -> {source} ({asset_type})")  # binance (crypto)

# Download automatico dalla fonte corretta
data = await extractor.download_historical('AAPL', period='1mo')
```

---

## Guida Utilizzo

### Quick Start - Paper Trading

```python
import asyncio
from broker.yfinance_broker import YFinanceBroker

async def main():
    # 1. Inizializza broker con $10,000
    broker = YFinanceBroker(initial_capital=10000)
    await broker.initialize()

    # 2. Compra 10 azioni Apple
    result = await broker.place_market_order('AAPL', 'BUY', 10)

    if result.success:
        print(f"✓ Comprato {result.quantity} AAPL @ ${result.avg_price:.2f}")

    # 3. Controlla posizioni
    positions = await broker.get_positions()
    for pos in positions:
        print(f"{pos.symbol}: {pos.quantity} shares")
        print(f"  Entry: ${pos.entry_price:.2f}")
        print(f"  Current: ${pos.current_price:.2f}")
        print(f"  P&L: ${pos.unrealized_pnl:+.2f}")

    # 4. Statistiche
    stats = broker.get_statistics()
    print(f"\nPortfolio Value: ${stats['portfolio_value']:,.2f}")
    print(f"Total Return: {stats['total_return_pct']:+.2f}%")
    print(f"Win Rate: {stats['win_rate']:.1f}%")

    await broker.shutdown()

asyncio.run(main())
```

### Configurazione Simboli

Modifica `config/symbols.yaml`:

```yaml
symbols_by_type:
  # Crypto - Binance (trading reale)
  crypto_binance:
    - BTCUSDT
    - ETHUSDT

  # Crypto - yFinance (paper trading)
  crypto_yfinance:
    - BTC-USD
    - ETH-USD

  # Stocks - yFinance (paper trading)
  stocks:
    - AAPL
    - MSFT
    - GOOGL

  # ETFs - yFinance (paper trading)
  etfs:
    - SPY
    - QQQ
```

### Configurazione Broker

Modifica `config/settings.py`:

```python
YFINANCE_CONFIG = {
    'enabled': True,
    'initial_capital': 10000,       # Capitale iniziale
    'commission_pct': 0.001,        # Commissione 0.1%
    'slippage_pct': 0.0005,         # Slippage 0.05%
    'data_dir': 'data/paper_trading',
}
```

---

## Esempi Pratici

### Esempio 1: Portfolio Multi-Asset

```python
async def create_diversified_portfolio():
    broker = YFinanceBroker(initial_capital=50000)
    await broker.initialize()

    # Allocazione portfolio
    trades = [
        ('AAPL', 20),     # 20 shares Apple
        ('MSFT', 15),     # 15 shares Microsoft
        ('SPY', 10),      # 10 shares S&P 500 ETF
        ('QQQ', 10),      # 10 shares NASDAQ ETF
        ('BTC-USD', 0.1), # 0.1 Bitcoin
        ('ETH-USD', 1.0), # 1 Ethereum
    ]

    for symbol, quantity in trades:
        result = await broker.place_market_order(symbol, 'BUY', quantity)
        if result.success:
            print(f"✓ {symbol}: {quantity} @ ${result.avg_price:.2f}")

    # Report
    positions = await broker.get_positions()
    for pos in positions:
        value = pos.quantity * pos.current_price
        print(f"{pos.symbol:10} | Value: ${value:10,.2f} | P&L: ${pos.unrealized_pnl:+.2f}")
```

### Esempio 2: Strategy Backtesting

```python
async def backtest_rsi_strategy():
    broker = YFinanceBroker(initial_capital=10000)
    extractor = YFinanceExtractor()

    # Download dati
    data = await extractor.download_historical(
        symbol='AAPL',
        period='3mo',
        interval='1d'
    )

    # Calcola RSI
    # ... (calcolo RSI)

    # Simula trading
    for i in range(len(data)):
        if data['rsi'].iloc[i] < 30:  # Oversold
            await broker.place_market_order('AAPL', 'BUY', 10)
        elif data['rsi'].iloc[i] > 70:  # Overbought
            await broker.place_market_order('AAPL', 'SELL', 10)

    # Risultati
    stats = broker.get_statistics()
    print(f"Final P&L: ${stats['total_pnl']:+.2f}")
    print(f"Win Rate: {stats['win_rate']:.1f}%")
```

### Esempio 3: Download Dati Multi-Asset

```python
async def download_multi_asset_data():
    extractor = MultiSourceExtractor()

    symbols = ['BTCUSDT', 'AAPL', 'BTC-USD', 'SPY', 'EURUSD=X']

    for symbol in symbols:
        # Auto-routing
        source, asset_type = extractor.detect_source(symbol)
        print(f"{symbol} -> {source} ({asset_type})")

        # Download
        data = await extractor.download_historical(
            symbol=symbol,
            period='1mo',
            interval='1d'
        )

        print(f"  Downloaded {len(data)} candles")
        print(f"  Last price: ${data['close'].iloc[-1]:.2f}")
```

---

## Paper Trading vs Live Trading

| Aspetto | Paper Trading (yFinance) | Live Trading (Binance) |
|---------|-------------------------|------------------------|
| **Rischio** | ❌ Nessuno (simulazione) | ⚠️ Denaro reale |
| **Costi** | ✅ Gratuito | 💰 Commissioni reali |
| **Asset** | Stocks, ETFs, Crypto, Forex | Solo Crypto |
| **Velocità** | ⚡ Istantanea | 🐢 Dipende da mercato |
| **Dati** | ✅ Gratuiti | ✅ API Binance |
| **Slippage** | 🎯 Simulato (0.05%) | 📊 Reale (variabile) |
| **Test Strategie** | ✅ Ideale | ❌ Costoso |

### Quando Usare Paper Trading?

✅ **Usalo per:**
- Testare nuove strategie
- Imparare a tradare senza rischi
- Validare indicatori tecnici
- Diversificare su stocks/ETFs (se non hai broker reale)
- Simulare portafogli multi-asset

❌ **Non usarlo per:**
- Trading reale di crypto (usa Binance)
- Eseguire ordini veri su stocks (serve broker reale: Interactive Brokers, etc.)

---

## Asset Supportati

### 🔹 Stocks (Azioni)

**US Stocks:**
```python
symbols = [
    'AAPL',   # Apple
    'MSFT',   # Microsoft
    'GOOGL',  # Google
    'AMZN',   # Amazon
    'TSLA',   # Tesla
    'NVDA',   # NVIDIA
    'META',   # Meta
    'NFLX',   # Netflix
]
```

### 🔹 ETFs

**Major ETFs:**
```python
etfs = [
    'SPY',    # S&P 500
    'QQQ',    # NASDAQ 100
    'IWM',    # Russell 2000
    'DIA',    # Dow Jones
    'VOO',    # Vanguard S&P 500
    'VTI',    # Total Stock Market
]
```

### 🔹 Crypto

**Via yFinance:**
```python
crypto = [
    'BTC-USD',  # Bitcoin
    'ETH-USD',  # Ethereum
    'SOL-USD',  # Solana
    'BNB-USD',  # Binance Coin
]
```

**Via Binance (Live):**
```python
crypto_binance = [
    'BTCUSDT',
    'ETHUSDT',
    'SOLUSDT',
    'BNBUSDT',
]
```

### 🔹 Forex

**Coppie Forex:**
```python
forex = [
    'EURUSD=X',  # EUR/USD
    'GBPUSD=X',  # GBP/USD
    'USDJPY=X',  # USD/JPY
    'AUDUSD=X',  # AUD/USD
]
```

### 🔹 Commodities

**Futures su commodity:**
```python
commodities = [
    'GC=F',   # Gold
    'CL=F',   # Crude Oil
    'SI=F',   # Silver
    'NG=F',   # Natural Gas
]
```

---

## Configurazione

### config/settings.py

```python
# yFinance Broker Config
YFINANCE_CONFIG = {
    'enabled': True,
    'initial_capital': 10000,
    'commission_pct': 0.001,      # 0.1% commissione
    'slippage_pct': 0.0005,       # 0.05% slippage
    'data_dir': 'data/paper_trading',
    'cache_ttl': 60,              # Cache 60 secondi
    'market_hours_check': True,   # Controlla orari mercato
}

# Multi-Broker Config
MULTI_BROKER_CONFIG = {
    'enabled': True,
    'broker_mapping': {
        'crypto_binance': 'binance',
        'crypto_yfinance': 'yfinance',
        'stocks': 'yfinance',
        'etfs': 'yfinance',
        'forex': 'yfinance',
    }
}
```

### config/symbols.yaml

```yaml
symbols_by_type:
  crypto_binance:
    - BTCUSDT
    - ETHUSDT

  stocks:
    - AAPL
    - MSFT

  etfs:
    - SPY
    - QQQ

allocation:
  BTCUSDT: 40  # 40% su Bitcoin
  AAPL: 20     # 20% su Apple
  SPY: 20      # 20% su S&P 500
  QQQ: 20      # 20% su NASDAQ
```

---

## FAQ

### 1. yFinance supporta trading live?

**No.** yFinance fornisce solo **dati** (storici e real-time). Per trading live su stocks/ETFs serve un broker reale come Interactive Brokers, Alpaca, TD Ameritrade, etc.

Il `YFinanceBroker` è un **simulatore** per paper trading.

### 2. Posso usare yFinance per crypto live trading?

**No.** Per crypto live trading usa **Binance** (già integrato nel sistema).

yFinance crypto (`BTC-USD`) è solo per **paper trading**.

### 3. I prezzi yFinance sono real-time?

**Quasi.** yFinance ha un ritardo di ~15 minuti per stocks durante market hours. Per crypto è più real-time.

Per **paper trading** va benissimo. Per **live trading** serve un data feed professionale.

### 4. Quali sono i limiti di yFinance?

**Rate Limits:**
- Non ufficiali, ma circa **2000 richieste/ora**
- Usa la cache interna per ridurre chiamate

**Dati:**
- 1m data: solo ultimi 7 giorni
- 5m data: solo ultimi 60 giorni
- 1h/1d data: storia completa

### 5. Come passo da paper trading a live trading?

**Stocks/ETFs:**
1. Apri account con broker reale (Interactive Brokers, etc.)
2. Integra API del broker nel sistema
3. Crea nuovo broker class (es. `IBBroker`)

**Crypto:**
Già pronto! Usa `BinanceBroker` per live trading crypto.

### 6. Posso mixare Binance (live) + yFinance (paper)?

**Sì!** Il sistema supporta multi-broker:

```python
# Binance per crypto live
binance_broker = BinanceBroker(api_key, api_secret)

# yFinance per stocks paper
yf_broker = YFinanceBroker(initial_capital=10000)

# Trade simultaneo
await binance_broker.place_market_order('BTCUSDT', 'BUY', 0.01)
await yf_broker.place_market_order('AAPL', 'BUY', 10)
```

### 7. Come testo una strategia su più asset?

Usa il `MultiSourceExtractor`:

```python
extractor = MultiSourceExtractor()

symbols = ['BTCUSDT', 'AAPL', 'SPY', 'BTC-USD']

# Download automatico da fonte corretta
for symbol in symbols:
    data = await extractor.download_historical(symbol, period='1y')
    # Testa strategia su data
```

### 8. Dove vengono salvati i log del paper trading?

Directory: `data/paper_trading/`

File:
- `broker_state.json` - Stato broker (balance, positions)
- `trading_report.txt` - Report finale

### 9. Come resetto il paper trading?

```python
# Opzione 1: Elimina directory
import shutil
shutil.rmtree('data/paper_trading')

# Opzione 2: Crea nuovo broker
broker = YFinanceBroker(initial_capital=10000)
```

### 10. yFinance funziona fuori dagli USA?

**Sì!** yFinance funziona globalmente. Supporta:
- US stocks (NASDAQ, NYSE)
- European stocks (LSE, XETRA, etc.)
- Asian stocks (TSE, HKEX, etc.)
- Crypto (globale)
- Forex (globale)

---

## Troubleshooting

### Errore: "No data returned for symbol"

**Causa:** Simbolo non valido o mercato chiuso

**Soluzione:**
```python
# Verifica simbolo
valid = await extractor.validate_symbol('AAPL', 'stock')
if not valid:
    print("Simbolo non valido")

# Prova con period più lungo
data = await extractor.download_historical('AAPL', period='1y')
```

### Errore: "Rate limit exceeded"

**Causa:** Troppe richieste a yFinance

**Soluzione:**
```python
# Aumenta cache TTL
extractor = YFinanceExtractor(cache_ttl=300)  # 5 minuti

# Usa sleep tra richieste
import asyncio
for symbol in symbols:
    data = await extractor.download_historical(symbol)
    await asyncio.sleep(1)  # Pausa 1 secondo
```

### Prezzi non aggiornati

**Causa:** Cache

**Soluzione:**
```python
# Pulisci cache
extractor.clear_cache()

# Disabilita cache
extractor = YFinanceExtractor(cache_ttl=0)
```

---

## Prossimi Passi

1. **Testa Paper Trading**: Esegui `python examples/yfinance_example.py`
2. **Crea Strategia**: Sviluppa la tua strategia su stocks/crypto
3. **Backtest**: Testa su dati storici
4. **Live Paper Trading**: Esegui in real-time (simulato)
5. **Live Trading**: Quando sei pronto, passa a Binance (crypto) o broker reale (stocks)

---

## Risorse

- **yFinance Docs**: https://pypi.org/project/yfinance/
- **Yahoo Finance**: https://finance.yahoo.com/
- **Binance API**: https://binance-docs.github.io/apidocs/spot/en/

---

## Supporto

Per domande o problemi:
1. Controlla questa documentazione
2. Esegui esempi in `examples/yfinance_example.py`
3. Controlla log in `logs/trading.log`

**Buon Trading! 🚀📈**
