# Binance Safe Order Execution System

Sistema completo per l'esecuzione sicura di ordini su Binance con gestione automatica di retry, verifica stato ordine, e prevenzione duplicati.

## Features

### 🛡️ Safe Order Executor

- ✅ **Retry Automatico**: Exponential backoff su errori di rete (max 5 tentativi)
- ✅ **Idempotency**: Prevenzione ordini duplicati tramite `client_order_id` univoco
- ✅ **Verifica Stato**: Controllo automatico stato ordine prima di reinviare
- ✅ **Gestione Parziali**: Supporto ordini parzialmente eseguiti
- ✅ **Cache Ordini**: Sistema cache per evitare invii duplicati
- ✅ **Timeout Handling**: Timeout configurabile per verifica completamento
- ✅ **Error Recovery**: Gestione intelligente errori Binance API

### 📊 Position Manager

- ✅ **Tracking Posizioni**: Gestione posizioni LONG/SHORT con P&L real-time
- ✅ **Scale In/Out**: Supporto apertura e chiusura parziale posizioni
- ✅ **Stop Loss / Take Profit**: Associazione ordini SL/TP a posizioni
- ✅ **Statistiche Trading**: Win rate, profit factor, P&L totale
- ✅ **Export Dati**: Esportazione storico posizioni chiuse

## Architettura

```
broker/
├── binance_broker.py       # Broker principale + SafeOrderExecutor
├── position_manager.py     # Gestione posizioni e P&L
├── example_usage.py        # Esempi di utilizzo completi
└── README.md              # Questa documentazione
```

## Installazione Dipendenze

```bash
pip install python-binance
```

## Quick Start

### 1. Ordine Market Semplice

```python
import asyncio
from broker import BinanceBroker

async def main():
    # Inizializza broker (testnet per sicurezza)
    broker = BinanceBroker(
        api_key="YOUR_API_KEY",
        api_secret="YOUR_API_SECRET",
        testnet=True
    )

    await broker.initialize()

    # Piazza ordine market con retry automatico
    result = await broker.place_market_order(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.001
    )

    if result.success:
        print(f"✓ Ordine eseguito: {result.executed_qty} @ {result.avg_price}")
        print(f"  Retry effettuati: {result.retry_count}")
    else:
        print(f"✗ Errore: {result.error_message}")

    await broker.close()

asyncio.run(main())
```

### 2. Gestione Completa Posizione

```python
from broker import BinanceBroker, PositionManager

async def main():
    broker = BinanceBroker(api_key="...", api_secret="...", testnet=True)
    position_manager = PositionManager()

    await broker.initialize()

    # Apri posizione LONG
    entry = await broker.place_market_order("BTCUSDT", "BUY", 0.001)

    position = position_manager.open_position(
        symbol="BTCUSDT",
        side="LONG",
        entry_price=entry.avg_price,
        quantity=entry.executed_qty,
        entry_order_id=entry.order_id
    )

    # Imposta stop loss al -2%
    stop_price = position.entry_price * 0.98
    sl = await broker.place_stop_loss("BTCUSDT", "SELL", position.quantity, stop_price)
    position_manager.set_stop_loss("BTCUSDT", sl.order_id)

    # Monitora P&L
    current_price = 45000  # Prezzo da API
    pnl = position.calculate_unrealized_pnl(current_price)
    print(f"P&L: {pnl:.2f}")

    # Chiudi posizione
    exit_result = await broker.place_market_order("BTCUSDT", "SELL", position.quantity)
    position_manager.close_position("BTCUSDT", exit_result.avg_price)

    # Statistiche
    print(position_manager.get_summary())

    await broker.close()
```

### 3. Scale Out (Chiusura Parziale)

```python
# Apri posizione con quantità maggiore
entry = await broker.place_market_order("BTCUSDT", "BUY", 0.01)

position = position_manager.open_position(
    symbol="BTCUSDT",
    side="LONG",
    entry_price=entry.avg_price,
    quantity=entry.executed_qty
)

# Primo take profit: chiudi 50% al +1%
tp1 = await broker.place_market_order("BTCUSDT", "SELL", position.quantity * 0.5)
pnl1 = position_manager.partial_close_position(
    "BTCUSDT",
    position.quantity * 0.5,
    tp1.avg_price
)

# Secondo take profit: chiudi restante al +2%
tp2 = await broker.place_market_order("BTCUSDT", "SELL", position.remaining_quantity)
position_manager.close_position("BTCUSDT", tp2.avg_price)

print(f"P&L totale: {position.realized_pnl:.2f} ({position.realized_pnl_percentage:.2f}%)")
```

## Come Funziona il Retry System

### Scenario 1: Errore di Rete

```
Tentativo 1: Invio ordine → Network Error
  ↓ Retry dopo 1s
Tentativo 2: Invio ordine → Network Error
  ↓ Retry dopo 2s
Tentativo 3: Invio ordine → Success ✓
```

### Scenario 2: Ordine Duplicato

```
Tentativo 1: Invio ordine → Network timeout (ma ordine inviato!)
  ↓ Retry dopo 1s
Tentativo 2: Verifica se ordine esiste → Trovato!
  ↓ Return ordine esistente (no duplicato) ✓
```

### Scenario 3: Ordine Parzialmente Eseguito

```
Invio ordine LIMIT → Status: NEW
  ↓ Polling ogni 500ms
Status: PARTIALLY_FILLED (50% eseguito)
  ↓ Attesa timeout (30s)
Status: FILLED (100% eseguito) ✓
```

## Configurazione Avanzata

### Personalizza Retry Logic

```python
from broker import SafeOrderExecutor

executor = SafeOrderExecutor(
    client=binance_client,
    max_retries=10,              # Numero max retry
    base_retry_delay=2.0,        # Delay iniziale (secondi)
    max_retry_delay=60.0,        # Delay massimo
    order_check_timeout=60,      # Timeout verifica ordine
    enable_test_mode=False       # True per test order
)
```

### Stati Ordine

- `PENDING` - In attesa di invio
- `NEW` - Inviato ma non eseguito
- `PARTIALLY_FILLED` - Parzialmente eseguito
- `FILLED` - Completamente eseguito ✓
- `CANCELED` - Cancellato
- `REJECTED` - Rifiutato (es. saldo insufficiente)
- `EXPIRED` - Scaduto
- `FAILED` - Fallito dopo tutti i retry

## Error Handling

Il sistema gestisce automaticamente:

### Errori Recuperabili (con retry):
- `-1003`: Too many requests
- `-1021`: Timestamp desync
- Network timeouts
- Connection errors

### Errori Non Recuperabili (no retry):
- `-2010`: Insufficient balance
- `-1013`: Invalid quantity/price
- `-2011`: Duplicate order → Verifica ordine esistente

## Test Mode

**IMPORTANTE**: Usa sempre `testnet=True` per testare!

```python
# TESTNET (sicuro per testing)
broker = BinanceBroker(api_key="...", api_secret="...", testnet=True)

# PRODUCTION (solo dopo test!)
broker = BinanceBroker(api_key="...", api_secret="...", testnet=False)
```

## Logging

Il sistema usa Python logging per tracciare tutte le operazioni:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Output:
```
2025-10-22 10:30:15 - broker.binance_broker - INFO - Inizio esecuzione ordine: BTCUSDT BUY 0.001 @ MARKET
2025-10-22 10:30:16 - broker.binance_broker - INFO - ✓ Ordine completato: 0.001 @ 43250.50
2025-10-22 10:30:16 - broker.position_manager - INFO - ✓ Posizione BTCUSDT aperta: LONG 0.001 @ 43250.50
```

## Best Practices

### ✅ DO:
- Usa sempre `testnet=True` per testing
- Verifica saldo prima di aprire posizioni
- Imposta sempre stop loss
- Monitora `result.retry_count` per problemi di rete
- Usa `client_order_id` univoci per ogni ordine
- Chiudi connessioni con `await broker.close()`

### ❌ DON'T:
- Non rimuovere retry logic
- Non ignorare `result.success == False`
- Non aprire più posizioni sullo stesso simbolo
- Non usare credenziali production in codice
- Non bypassare idempotency checks

## Integrazione con Trading System

Per integrare nel sistema esistente:

```python
# In main.py
from broker import BinanceBroker, PositionManager

class TradingSystem:
    def __init__(self):
        self.broker = BinanceBroker(...)
        self.position_manager = PositionManager()

    async def execute_signal(self, signal):
        # Genera segnale da strategia
        if signal['type'] == 'BUY' and not self.position_manager.has_open_position(symbol):
            # Esegui ordine con retry automatico
            result = await self.broker.place_market_order(
                symbol=signal['symbol'],
                side='BUY',
                quantity=signal['quantity']
            )

            if result.success:
                # Registra posizione
                self.position_manager.open_position(...)

                # Imposta stop loss
                await self.broker.place_stop_loss(...)
```

## Troubleshooting

### Problema: "Insufficient balance"
**Soluzione**: Verifica saldo con `await broker.get_account_balance()`

### Problema: Tutti i retry falliscono
**Soluzione**:
1. Verifica connessione internet
2. Controlla API key valide
3. Verifica limits Binance (weight limits)

### Problema: Ordini duplicati
**Soluzione**: Il sistema previene automaticamente con `client_order_id` univoco

### Problema: Ordine parzialmente eseguito
**Soluzione**: Il sistema gestisce automaticamente, controlla `result.executed_qty`

## Esempi Completi

Vedi `example_usage.py` per esempi dettagliati di:
- Ordini market/limit
- Gestione posizioni
- Scale in/out
- Error handling
- Verifica saldi

## Supporto

Per problemi o domande, consulta:
- [Binance API Docs](https://binance-docs.github.io/apidocs/spot/en/)
- [python-binance](https://python-binance.readthedocs.io/)

## License

Parte del Trading System - Adaptive SuperTrend Strategy
