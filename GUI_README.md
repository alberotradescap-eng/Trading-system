# Trading System - Interfaccia Grafica

Interfaccia grafica completa per gestire il sistema di trading automatizzato.

## Caratteristiche

### 1. Selezione Strategia
Scegli tra tre strategie di trading:

- **RSI + MACD Strategy** (Default)
  - Entry: RSI < 30 (oversold) + MACD bullish crossover
  - Exit: Take Profit 2% / Stop Loss 1%
  - Best for: Range-bound markets

- **Mean Reversion Strategy**
  - Entry: Bollinger Band extremes + RSI confirmation
  - Exit: Mean reversion to SMA 20
  - Best for: Volatile sideways markets

- **Trend Following Strategy**
  - Entry: SMA 20 > SMA 50 > SMA 200 (strong trend)
  - Exit: Take Profit 5% / Stop Loss 2%
  - Best for: Strong trending markets

### 2. Controlli Trading
- **Avvia Trading**: Inizia il trading automatico con la strategia selezionata
- **Ferma Trading**: Ferma il sistema (le posizioni aperte rimangono attive)
- **Status in tempo reale**: Visualizzazione dello stato del sistema

### 3. Dashboard Monitoraggio

#### Pannello Status
- **PnL Giornaliero**: Profitto/perdita totale della giornata
- **Posizioni Aperte**: Numero di trade attualmente aperti
- **Trade Oggi**: Contatore dei trade eseguiti
- **Win Rate**: Percentuale di trade vincenti

#### Tab Posizioni Aperte
Visualizza tutte le posizioni correntemente aperte:
- Symbol (es. BTCUSDT)
- Side (LONG/SHORT)
- Entry Price
- Current Price
- Quantity
- PnL (assoluto)
- PnL % (percentuale)
- Duration (durata della posizione)

#### Tab Storico Trade
Storico completo dei trade chiusi:
- Timestamp apertura/chiusura
- Symbol
- Side
- Entry/Exit Price
- Quantity
- PnL
- PnL %
- Duration

#### Tab Log Sistema
Log in tempo reale di tutti gli eventi del sistema:
- Avvio/Stop sistema
- Connessioni Binance
- Segnali di trading
- Esecuzione ordini
- Errori e warning

## Installazione

### Requisiti
```bash
pip install tkinter
```

**Nota**: tkinter è solitamente incluso con Python. Se non disponibile:

**Ubuntu/Debian**:
```bash
sudo apt-get install python3-tk
```

**macOS** (via Homebrew):
```bash
brew install python-tk
```

**Windows**: Incluso nell'installazione standard di Python

## Utilizzo

### Avvio GUI
```bash
python run_gui.py
```

oppure:
```bash
python gui.py
```

### Workflow Tipico

1. **Selezione Strategia**
   - Clicca sul radio button della strategia desiderata
   - Il sistema confermerà la selezione nel log

2. **Configurazione Parametri**
   - I parametri (Position Size, Max Positions, TP/SL) sono visualizzati nel pannello
   - Per modificarli, edita `config/settings.py`

3. **Avvio Trading**
   - Clicca "▶ AVVIA TRADING"
   - Conferma la strategia selezionata
   - Il sistema si connette a Binance e inizia il monitoraggio

4. **Monitoraggio**
   - Il dashboard si aggiorna automaticamente ogni secondo
   - Controlla il PnL in tempo reale
   - Verifica le posizioni aperte
   - Leggi i log per dettagli sugli eventi

5. **Stop Trading**
   - Clicca "⬛ FERMA TRADING"
   - Conferma lo stop
   - Le posizioni aperte NON vengono chiuse automaticamente

## Sicurezza

### Limiti di Rischio (Final TP/SL)
Il sistema implementa due livelli di protezione:

1. **Per-Trade TP/SL**: Ogni trade ha stop loss e take profit individuali
2. **Daily Final TP/SL**: Limiti giornalieri che bloccano il sistema

Quando i limiti giornalieri vengono raggiunti:
- **Take Profit Final**: +$500 → Sistema si blocca
- **Stop Loss Final**: -$200 → Sistema si blocca

Per sbloccare dopo il blocco:
```bash
python main.py --unlock
```

### Modalità di Esecuzione
La GUI esegue il trading in modalità **LIVE REALE**:
- Connessione all'API Binance reale
- Ordini eseguiti sul mercato reale
- Utilizzo di capitale reale

**ATTENZIONE**: Assicurati di:
1. Aver configurato correttamente le API Binance in `.env`
2. Aver testato la strategia in backtest prima
3. Iniziare con capitale ridotto per i test

## Configurazione

### File di Configurazione

**`.env`** - Credenziali API:
```env
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

**`config/settings.py`** - Parametri trading:
```python
POSITION_SIZE_PCT = 2.0        # 2% del capitale per trade
MAX_POSITIONS = 3              # Max 3 posizioni simultanee
TAKE_PROFIT_FINAL = 500        # Blocco a +$500 giornalieri
STOP_LOSS_FINAL = -200         # Blocco a -$200 giornalieri
```

**`config/symbols.yaml`** - Simboli da tradare:
```yaml
symbols:
  - symbol: BTCUSDT
    timeframes: [1m, 5m, 15m, 1h]
  - symbol: ETHUSDT
    timeframes: [1m, 5m, 15m, 1h]
```

## Troubleshooting

### Errore: "No module named 'tkinter'"
Installa tkinter seguendo le istruzioni nella sezione Installazione

### Errore: "Cannot connect to Binance"
- Verifica le credenziali API in `.env`
- Controlla la connessione internet
- Verifica che l'IP sia whitelisted su Binance

### La GUI si blocca
- Il trading viene eseguito in un thread separato
- Se la GUI si blocca, potrebbe essere un problema con asyncio/tkinter
- Controlla i log in `logs/trading.log`

### I dati non si aggiornano
- Verifica che il trading sia stato avviato
- Controlla che `is_running = True` nel log
- Riavvia la GUI

## Funzionalità Future

Possibili miglioramenti:
- [ ] Grafici in tempo reale (candlestick chart)
- [ ] Modifica parametri TP/SL dalla GUI
- [ ] Export trade history in CSV/Excel
- [ ] Statistiche avanzate (Sharpe ratio, drawdown, ecc.)
- [ ] Notifiche desktop
- [ ] Multi-account support
- [ ] Dark/Light theme toggle
- [ ] Strategy backtesting dalla GUI

## Support

Per problemi o domande:
1. Controlla i log in `logs/trading.log`
2. Verifica la configurazione in `config/settings.py`
3. Testa in modalità backtest prima

## License

Vedi LICENSE file nel repository principale.
