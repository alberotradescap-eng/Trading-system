# Quick Start Guide

Guida rapida per iniziare con il Trading System.

## Setup Iniziale

### 1. Installa dipendenze

```bash
pip install -r requirements.txt
```

**Nota su TA-Lib**: Su Linux potrebbe essere necessario:
```bash
# Ubuntu/Debian
sudo apt-get install ta-lib

# O compila da source
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
```

### 2. Configura API Keys

Copia il file di esempio e inserisci le tue chiavi:

```bash
cp .env.example .env
nano .env  # o usa il tuo editor preferito
```

Inserisci:
- **Binance API**: Crea su https://www.binance.com/en/my/settings/api-management
  - Abilita solo "Enable Reading" e "Enable Spot & Margin Trading"
  - NO "Enable Withdrawals"!

- **Anthropic API** (per LLM plugin): https://console.anthropic.com/

- **Telegram Bot**:
  1. Parla con @BotFather su Telegram
  2. Usa `/newbot` e segui le istruzioni
  3. Copia il token
  4. Per chat_id: parla con @userinfobot

### 3. Configura Trading

Modifica i file in `config/`:

#### Simboli da tradare (`config/symbols.yaml`)
```yaml
symbols:
  - BTCUSDT
  - ETHUSDT

timeframes:
  - 1m
  - 5m
```

#### Orari di trading (`config/schedule.yaml`)
```yaml
trading_hours:
  start: "09:00"
  end: "18:00"

active_days:
  - monday
  - tuesday
  - wednesday
  - thursday
  - friday
```

#### Regole di trading (`config/trading_rules.py`)
```python
def entry_long(self, data):
    return (
        data['rsi'] < 30 and          # RSI oversold
        data['macd'] > data['signal']  # MACD bullish
    )

def exit_long(self, data, entry_price, entry_time):
    profit_pct = (data['close'] - entry_price) / entry_price * 100

    if profit_pct >= 2.0:
        return True, 'take_profit'  # TP al 2%

    if profit_pct <= -1.0:
        return True, 'stop_loss'    # SL all'1%

    return False, None
```

---

## Workflow

### A. Backtesting (prima di tradare live!)

#### 1. Scarica dati storici

```bash
python extractors/download_historical.py --symbol BTCUSDT --start 2024-01-01
```

Questo scarica dati da Binance e li salva in `data/backtest/`.

#### 2. Esegui backtest

```bash
python backtest.py --symbol BTCUSDT --start 2024-01-01 --end 2024-12-31
```

Output:
```
==================================================
BACKTEST RESULTS
==================================================

Capital:
  Initial:  $10,000.00
  Final:    $12,350.00
  Return:   $2,350.00 (23.50%)

Trades:
  Total:    42
  Winners:  28
  Losers:   14
  Win Rate: 66.67%

PnL:
  Total:       $2,350.00
  Best Trade:  $185.50
  Worst Trade: -$95.20

Metrics:
  Profit Factor:  2.15
  Sharpe Ratio:   1.85
  Max Drawdown:   -8.5%
==================================================
```

Ti verrà anche mostrato un grafico con:
- Equity curve
- Drawdown
- Distribuzione PnL
- PnL cumulativo

#### 3. Ottimizza la strategia

Se i risultati non sono soddisfacenti, modifica `config/trading_rules.py` e ri-testa.

---

### B. Live Trading

⚠️ **ATTENZIONE**: Inizia con capitale piccolo e monitora attentamente!

#### 1. Verifica configurazione

```bash
# Controlla che API keys siano corrette
python -c "from config.settings import CONFIG; print('Binance API:', 'OK' if CONFIG['binance']['api_key'] else 'MISSING')"
```

#### 2. Avvia sistema

```bash
python main.py --mode live
```

Output:
```
2024-01-15 10:00:00 | INFO | Trading System STARTED
2024-01-15 10:00:00 | INFO | Strategia attiva: RSI + MACD Strategy
2024-01-15 10:00:00 | INFO | LLM Advisor inizializzato: anthropic - claude-3-5-sonnet
2024-01-15 10:00:00 | INFO | Connesso a Binance API
2024-01-15 10:00:00 | INFO | Avvio stream per 2 simboli: ['BTCUSDT', 'ETHUSDT']
```

Il sistema ora:
1. Estrae dati realtime da Binance
2. Calcola indicatori tecnici
3. Genera segnali di trading
4. Chiede consenso a Claude (se abilitato)
5. Esegue trade
6. Invia notifiche audio + Telegram

#### 3. Monitoraggio

- **Console**: Vedi log in tempo reale
- **Telegram**: Ricevi notifiche su ogni trade
- **File log**: `logs/trading.log`

#### 4. Stop

Premi `Ctrl+C` per fermare il sistema in modo pulito (chiude posizioni aperte).

---

## Features Speciali

### TP/SL FINAL (Blocco Sistema)

In `config/settings.py`:
```python
'take_profit_final': 500,   # $500 profitto → BLOCCO
'stop_loss_final': -200,    # $200 perdita → BLOCCO
```

Quando raggiunti questi limiti giornalieri:
- Il sistema si blocca automaticamente
- Chiude tutte le posizioni
- Invia notifica Telegram
- Non esegue più trade fino a sblocco manuale

**Sblocco**:
```bash
python main.py --unlock
```

### LLM Trading Advisor

Prima di ogni trade, il sistema chiede consenso a Claude:

```
Analizza questa opportunità di trading:

Symbol: BTCUSDT
Type: BUY
Price: $43,250.50
RSI: 28.5
MACD: bullish cross
Volume: sopra media

Dovrei eseguire questo trade?
```

Claude risponde:
```
APPROVE - RSI in oversold (28.5) indica condizione di ipervenduto.
MACD bullish cross conferma momentum rialzista.
Volume elevato supporta il movimento. Trade valido.
```

**Disabilitare LLM**: In `config/settings.py` → `'llm_enabled': False`

### Notifiche

#### Audio
- `order_filled_buy.wav` → Quando compra
- `order_filled_sell.wav` → Quando vende

Metti i tuoi file `.wav` in `sounds/`

#### Telegram
Ricevi:
- Ogni trade eseguito
- Statistiche giornaliere (ore 18:30)
- Grafici equity curve
- Alert blocco FINAL

---

## Troubleshooting

### Errore: "API key mancante"
```
Errore: Binance API key non configurata
```
→ Verifica `.env` e che le chiavi siano corrette

### Errore: "Insufficient balance"
```
Errore: Saldo insufficiente per eseguire trade
```
→ Riduci `position_size_pct` in `config/settings.py`

### Errore: "TA-Lib not found"
```
ImportError: No module named 'talib'
```
→ Installa TA-Lib (vedi Setup Iniziale)

### Nessun trade eseguito
- Controlla che orari di trading siano corretti (`config/schedule.yaml`)
- Verifica che le condizioni di entry siano raggiungibili
- Controlla i log: `logs/trading.log`

### LLM rifiuta tutti i trade
- Riduci `temperature` in `config/settings.py`
- Oppure disabilita: `'llm_enabled': False`

---

## Best Practices

1. **Testa SEMPRE con backtest** prima di live trading
2. **Inizia con capitale piccolo** (es. $100-500)
3. **Monitora per i primi giorni** senza lasciare incustodito
4. **Usa TP/SL FINAL** per protezione
5. **Controlla daily stats** su Telegram ogni sera
6. **Tieni log** di tutte le modifiche alla strategia

---

## Prossimi Passi

### Strategie Avanzate

In `config/trading_rules.py` trovi 3 strategie pronte:
- `TradingRules` - RSI + MACD
- `MeanReversionStrategy` - Bollinger Bands
- `TrendFollowingStrategy` - Multiple SMA

Cambia `ACTIVE_STRATEGY` per testarle.

### Multi-Symbol

Per tradare più crypto contemporaneamente, modifica `config/symbols.yaml`.

### Custom Indicators

Aggiungi indicatori personalizzati in `etl/indicator_calculator.py`.

---

**Buon Trading! 🚀**

Per domande o problemi, consulta `ARCHITECTURE.md` per dettagli tecnici.
