# Crypto Trading System

Sistema di trading automatizzato per criptovalute con architettura modulare, supporto per backtesting, plugin LLM per consenso ai trade, e sistema completo di notifiche.

## Caratteristiche Principali

- **Trading Realtime**: Connessione a Binance WebSocket per dati live
- **Architettura Modulare**: Extractors → ETL → Engine → Broker
- **TP/SL Avanzato**: Stop Loss e Take Profit normali + FINAL (con blocco sistema)
- **LLM Advisory**: Chiedi consenso a un LLM (Claude/GPT/Llama/Gemini via OpenRouter) prima di ogni trade
- **Notifiche Complete**: Audio + Telegram con statistiche e grafici
- **Backtesting**: Testa strategie su dati storici
- **Scheduling**: Imposta giorni e orari di trading
- **Multi-Symbol**: Gestisci più crypto contemporaneamente

## Architettura

```
Extractors (Binance) → data/raw → ETL → data/processed → Engine (Signals)
                                                              ↓
                                                         LLM Plugin
                                                              ↓
                                                   Broker (Execution)
                                                              ↓
                                              Notifications (Audio + Telegram)
```

Vedi [ARCHITECTURE.md](ARCHITECTURE.md) per dettagli completi.

## Installazione

### Opzione 1: Anaconda (RACCOMANDATO - più semplice)

Se usi Anaconda o Miniconda, l'installazione è molto più semplice (specialmente su Windows):

```bash
# Crea l'ambiente con tutte le dipendenze
conda env create -f environment.yml

# Attiva l'ambiente
conda activate trading-system
```

Vedi la [Guida Completa Anaconda](INSTALL_ANACONDA.md) per istruzioni dettagliate in italiano.

**Vantaggi**: TA-Lib si installa automaticamente senza problemi, niente compilatori necessari!

### Opzione 2: Installazione Automatica con Script

**Windows**:
```powershell
# Esegui lo script di installazione automatica
.\install_windows.ps1
```

**Linux/macOS**:
```bash
# Rendi eseguibile e lancia lo script
chmod +x install_linux_mac.sh
./install_linux_mac.sh
```

### Opzione 3: Installazione Manuale

**IMPORTANTE per utenti Windows**: L'installazione di TA-Lib richiede passaggi specifici. Consulta la [guida dettagliata di installazione](INSTALL.md).

### 1. Requisiti
- Python 3.9+ (3.10 o 3.11 consigliato)
- TA-Lib (per indicatori tecnici)

### 2. Installa TA-Lib

**Windows**: Usa i wheel pre-compilati (consigliato)
```powershell
# Python 3.9
pip install https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp39-cp39-win_amd64.whl

# Python 3.10
pip install https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp310-cp310-win_amd64.whl

# Python 3.11
pip install https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp311-cp311-win_amd64.whl
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get update
sudo apt-get install -y build-essential wget
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
sudo ldconfig
```

**macOS**:
```bash
brew install ta-lib
```

Per istruzioni dettagliate e troubleshooting, vedi [INSTALL.md](INSTALL.md).

### 3. Installa altre dipendenze
```bash
pip install -r requirements.txt
```

### 4. Configura variabili d'ambiente
Crea un file `.env`:
```env
# Binance API
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret

# LLM - scegli uno dei seguenti provider:
# Anthropic (Claude)
ANTHROPIC_API_KEY=your_anthropic_key
# OpenAI (GPT)
# OPENAI_API_KEY=your_openai_key
# OpenRouter (accesso a molti modelli)
# OPENROUTER_API_KEY=your_openrouter_key

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 5. Configura trading
Modifica i file in `config/`:
- `symbols.yaml`: Crypto da tradare
- `schedule.yaml`: Orari di trading
- `trading_rules.py`: Regole di entry/exit
- `settings.py`: Impostazioni generali

## Utilizzo

### Modalità Live Trading
```bash
python main.py --mode live
```

### Backtesting
```bash
# Prima scarica dati storici
python extractors/download_historical.py --symbol BTCUSDT --start 2024-01-01

# Poi esegui backtest
python backtest.py --symbol BTCUSDT --start 2024-01-01 --end 2024-12-31
```

### Sblocco dopo FINAL TP/SL
Quando il sistema raggiunge il Take Profit o Stop Loss FINAL giornaliero, si blocca automaticamente.
Per sbloccarlo:
```bash
python main.py --unlock
```

## Definire Strategie

Le regole di trading sono definite in modo semplice in `config/trading_rules.py`:

```python
class TradingRules:
    def entry_long(self, data):
        """Quando entrare LONG"""
        return (
            data['rsi'] < 30 and              # RSI oversold
            data['close'] > data['sma_20'] and # Prezzo sopra media
            data['macd'] > data['signal']      # MACD positivo
        )

    def exit_long(self, data, entry_price):
        """Quando uscire da posizione LONG"""
        current_price = data['close']
        profit_pct = (current_price - entry_price) / entry_price * 100

        # Take profit 2%
        if profit_pct >= 2.0:
            return True, 'take_profit'

        # Stop loss 1%
        if profit_pct <= -1.0:
            return True, 'stop_loss'

        return False, None
```

## Configurazione Schedule

In `config/schedule.yaml`:
```yaml
trading_schedule:
  enabled: true
  timezone: 'Europe/Rome'

  active_days:
    - monday
    - tuesday
    - wednesday
    - thursday
    - friday

  trading_hours:
    start: "09:00"  # Inizio trading
    end: "18:00"    # Fine trading
```

## Take Profit / Stop Loss FINAL

Il sistema ha due livelli di TP/SL:

1. **Per Trade**: Ogni singolo trade ha il suo TP/SL
2. **FINAL (Giornaliero)**: Limiti globali giornalieri

In `config/settings.py`:
```python
TRADING_CONFIG = {
    # TP/SL per trade
    'take_profit_pct': 2.0,   # 2% profitto → chiudi trade
    'stop_loss_pct': 1.0,     # 1% perdita → chiudi trade

    # TP/SL FINAL (blocca sistema)
    'take_profit_final': 500,   # $500 profitto giornaliero → BLOCCO
    'stop_loss_final': -200,    # $200 perdita giornaliera → BLOCCO
}
```

Quando raggiunti i limiti FINAL, il sistema:
- Chiude tutte le posizioni aperte
- Si blocca e non esegue nuovi trade
- Invia notifica Telegram
- Richiede sblocco manuale

## Plugin LLM

Prima di ogni trade, il sistema può chiedere consenso a un LLM per validare la decisione basandosi su analisi tecnica e contesto di mercato.

### Provider Supportati

1. **Anthropic** (Claude): Accesso diretto ai modelli Claude
2. **OpenAI** (GPT): Accesso diretto ai modelli GPT
3. **OpenRouter**: Accesso a molti modelli diversi con una sola API key
   - Claude (Anthropic)
   - GPT (OpenAI)
   - Llama (Meta)
   - Gemini (Google)
   - Mistral, DeepSeek, e molti altri

### Configurazione

In `config/settings.py`:
```python
LLM_CONFIG = {
    'enabled': True,
    'provider': 'openrouter',  # 'anthropic', 'openai', o 'openrouter'
    'api_key': os.getenv('OPENROUTER_API_KEY'),
    'model': 'anthropic/claude-3.5-sonnet',  # vedi esempi sotto
    'temperature': 0.3,
}
```

**Esempi di modelli OpenRouter:**
- `anthropic/claude-3.5-sonnet` - Claude Sonnet 3.5
- `openai/gpt-4-turbo` - GPT-4 Turbo
- `meta-llama/llama-3.1-70b-instruct` - Llama 3.1 70B
- `google/gemini-pro-1.5` - Gemini Pro 1.5
- `mistralai/mistral-large` - Mistral Large
- `deepseek/deepseek-chat` - DeepSeek Chat

Ottieni la tua API key OpenRouter su: https://openrouter.ai/keys

### Funzionamento

Il sistema invia al LLM:
- Indicatori tecnici (RSI, MACD, SMA, ATR, etc.)
- Prezzo attuale e volume
- Contesto di mercato multi-timeframe
- Tipo di trade proposto (BUY/SELL)

L'LLM analizza i dati e risponde con **APPROVE** o **REJECT** + motivazione dettagliata.

## Notifiche

### Audio
Segnali sonori immediati:
- `order_filled_buy.wav`: Quando un ordine BUY è eseguito
- `order_filled_sell.wav`: Quando un ordine SELL è eseguito

### Telegram
Messaggi automatici per:
- Ogni trade eseguito (symbol, prezzo, quantità)
- Statistiche giornaliere (PnL, win rate, etc.)
- Grafici equity curve
- Avvisi blocco FINAL TP/SL

## Struttura del Progetto

```
trading-system/
├── config/              # Configurazioni
├── extractors/          # Estrazione dati da Binance
├── data/                # Dati (raw → processed)
├── etl/                 # Trasformazione dati
├── engine/              # Motore decisionale
├── broker/              # Interfaccia broker
├── plugins/             # Plugin LLM
├── notifications/       # Notifiche (audio, Telegram)
├── backtesting/         # Motore backtesting
├── utils/               # Utilities
├── sounds/              # File audio
├── main.py              # Entry point live trading
└── backtest.py          # Entry point backtesting
```

## Esempi d'Uso

### 1. Trading BTC con schedule personalizzato
```bash
# Modifica config/symbols.yaml
symbols:
  - BTCUSDT

# Modifica config/schedule.yaml
trading_hours:
  start: "10:00"
  end: "16:00"

# Avvia
python main.py --mode live
```

### 2. Backtest su multiple crypto
```bash
python backtest.py --symbols BTCUSDT,ETHUSDT,SOLUSDT --start 2024-01-01
```

### 3. Visualizza statistiche
Il sistema genera automaticamente:
- `data/processed/signals/` - Segnali generati
- `backtest_results.png` - Equity curve
- Log completi in `logs/trading.log`

## Sicurezza

- Mai committare `.env` (già in `.gitignore`)
- API keys Binance con permessi limitati (solo trading, no withdraw)
- Limiti di posizione e capitale per trade
- Rate limiting per API Binance
- Logging completo di tutte le operazioni

## Estensioni Future

- [ ] Supporto per altri exchange (Coinbase, Kraken)
- [ ] Web dashboard per monitoraggio live
- [ ] Machine Learning per predizioni
- [ ] Trading di futures e opzioni
- [ ] Portfolio rebalancing automatico
- [ ] Sentiment analysis da Twitter/Reddit
- [ ] Multiple strategie simultanee con A/B testing

## Contribuire

Questo è un sistema modulare. Per aggiungere funzionalità:

1. **Nuovo exchange**: Crea `extractors/new_exchange_extractor.py`
2. **Nuovo indicatore**: Estendi `etl/indicator_calculator.py`
3. **Nuova strategia**: Modifica `config/trading_rules.py`
4. **Nuovo notificatore**: Aggiungi in `notifications/`

## Supporto

Per domande o problemi, apri una issue su GitHub.

## Disclaimer

Questo software è fornito "as-is" senza garanzie. Il trading di criptovalute comporta rischi significativi.
Usa questo sistema a tuo rischio e pericolo. Testa sempre con capitale che puoi permetterti di perdere.

---

**Happy Trading!**
