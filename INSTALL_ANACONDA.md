# Guida Installazione con Anaconda

Questa guida spiega come installare il Trading System usando Anaconda/Miniconda. Questo metodo è **RACCOMANDATO** specialmente per Windows, perché:

- TA-Lib si installa automaticamente senza problemi
- Non servono compilatori o Visual C++ Build Tools
- Gestione dipendenze più robusta
- Funziona su tutti i sistemi operativi (Windows, Linux, macOS)

## Indice

- [Prerequisiti](#prerequisiti)
- [Installazione Rapida](#installazione-rapida)
- [Installazione Passo-Passo](#installazione-passo-passo)
- [Verifica Installazione](#verifica-installazione)
- [Configurazione](#configurazione)
- [Uso dell'Ambiente](#uso-dellambiente)
- [Risoluzione Problemi](#risoluzione-problemi)

## Prerequisiti

### 1. Installa Anaconda o Miniconda

Se non hai già Anaconda/Miniconda installato:

**Anaconda (completo, ~3GB):**
- Scarica da: https://www.anaconda.com/download
- Include molti pacchetti scientifici pre-installati
- Raccomandato per principianti

**Miniconda (leggero, ~400MB):**
- Scarica da: https://docs.conda.io/en/latest/miniconda.html
- Include solo conda e Python
- Raccomandato per utenti esperti

Installa seguendo le istruzioni per il tuo sistema operativo.

### 2. Verifica Installazione

Apri un terminale (o Anaconda Prompt su Windows) e verifica:

```bash
conda --version
```

Dovresti vedere qualcosa come: `conda 24.x.x`

## Installazione Rapida

Una volta installato Anaconda/Miniconda:

```bash
# 1. Naviga nella cartella del progetto
cd /percorso/alla/Trading-system

# 2. Crea l'ambiente da file
conda env create -f environment.yml

# 3. Attiva l'ambiente
conda activate trading-system

# 4. Verifica che tutto funzioni
python -c "import talib, ccxt, pandas, numpy; print('Installazione completata con successo!')"
```

**Fatto!** L'ambiente è pronto all'uso.

## Installazione Passo-Passo

Se preferisci capire ogni passaggio:

### Step 1: Crea l'Ambiente

```bash
# Naviga nella cartella del progetto
cd /percorso/alla/Trading-system

# Crea l'ambiente Python con conda
conda create -n trading-system python=3.11
```

### Step 2: Attiva l'Ambiente

```bash
conda activate trading-system
```

Dovresti vedere `(trading-system)` all'inizio della riga di comando.

### Step 3: Installa TA-Lib

Questo è il vantaggio principale di conda - TA-Lib si installa con un comando:

```bash
conda install -c conda-forge ta-lib
```

### Step 4: Installa le Dipendenze Base

```bash
conda install -c conda-forge pandas numpy matplotlib seaborn pyarrow pyyaml aiohttp websockets pytest pytest-asyncio
```

### Step 5: Installa Dipendenze da pip

```bash
pip install python-binance ccxt ta backtrader vectorbt anthropic openai python-telegram-bot pygame plotly mplfinance python-dotenv schedule loguru
```

### Step 6: Verifica Installazione

```bash
python -c "import talib; print(f'TA-Lib version: {talib.__version__}')"
python -c "import ccxt; print(f'CCXT version: {ccxt.__version__}')"
python -c "import pandas; print(f'Pandas version: {pandas.__version__}')"
```

## Verifica Installazione

### Test Completo

Crea un file `test_install.py`:

```python
import sys
print(f"Python version: {sys.version}")

try:
    import talib
    print(f"✓ TA-Lib: {talib.__version__}")
except ImportError as e:
    print(f"✗ TA-Lib: {e}")

try:
    import ccxt
    print(f"✓ CCXT: {ccxt.__version__}")
except ImportError as e:
    print(f"✗ CCXT: {e}")

try:
    import pandas
    print(f"✓ Pandas: {pandas.__version__}")
except ImportError as e:
    print(f"✗ Pandas: {e}")

try:
    import numpy
    print(f"✓ NumPy: {numpy.__version__}")
except ImportError as e:
    print(f"✗ NumPy: {e}")

try:
    import backtrader
    print(f"✓ Backtrader: {backtrader.__version__}")
except ImportError as e:
    print(f"✗ Backtrader: {e}")

try:
    import anthropic
    print(f"✓ Anthropic: {anthropic.__version__}")
except ImportError as e:
    print(f"✗ Anthropic: {e}")

try:
    import matplotlib
    print(f"✓ Matplotlib: {matplotlib.__version__}")
except ImportError as e:
    print(f"✗ Matplotlib: {e}")

print("\n✓ Installazione completata con successo!")
```

Esegui:

```bash
python test_install.py
```

### Test Specifico TA-Lib

```bash
python -c "import talib; import numpy as np; data = np.random.random(100); sma = talib.SMA(data, timeperiod=10); print('TA-Lib funziona correttamente!')"
```

## Configurazione

### 1. Copia il File di Esempio

```bash
cp .env.example .env
```

### 2. Modifica il File .env

Apri `.env` con un editor di testo e inserisci le tue API key:

```env
# Binance API
BINANCE_API_KEY=la_tua_api_key_qui
BINANCE_API_SECRET=il_tuo_api_secret_qui

# LLM Provider (scegli uno)
# Anthropic (Claude)
ANTHROPIC_API_KEY=la_tua_anthropic_key_qui
# OpenAI (GPT)
# OPENAI_API_KEY=la_tua_openai_key_qui

# Telegram Notifications (opzionale)
TELEGRAM_BOT_TOKEN=il_tuo_bot_token_qui
TELEGRAM_CHAT_ID=il_tuo_chat_id_qui
```

### 3. Configura i Parametri di Trading

Modifica i file nella cartella `config/`:

- `symbols.yaml` - Coppie di trading
- `schedule.yaml` - Orari di trading
- `trading_rules.py` - Regole di entrata/uscita
- `settings.py` - Impostazioni generali

## Uso dell'Ambiente

### Attivare l'Ambiente

Ogni volta che vuoi usare il sistema:

**Windows (Anaconda Prompt):**
```cmd
conda activate trading-system
```

**Linux/macOS:**
```bash
conda activate trading-system
```

### Eseguire il Sistema

```bash
# Modalità backtesting
python main.py --mode backtest

# Modalità simulazione
python main.py --mode simulation

# Modalità live (attenzione!)
python main.py --mode live
```

### Disattivare l'Ambiente

Quando hai finito:

```bash
conda deactivate
```

## Gestione dell'Ambiente

### Aggiornare le Dipendenze

```bash
# Aggiorna conda
conda update conda

# Aggiorna tutti i pacchetti nell'ambiente
conda activate trading-system
conda update --all
```

### Esportare l'Ambiente

Se vuoi condividere o fare backup:

```bash
conda env export > environment_backup.yml
```

### Ricreare l'Ambiente

```bash
# Elimina ambiente esistente
conda env remove -n trading-system

# Ricrea da file
conda env create -f environment.yml
```

### Elencare gli Ambienti

```bash
conda env list
```

### Installare Nuovi Pacchetti

```bash
# Con conda (preferibile)
conda install -c conda-forge nome-pacchetto

# Con pip (se non disponibile su conda)
pip install nome-pacchetto
```

## Risoluzione Problemi

### Problema: "conda: command not found"

**Soluzione:**
- Su Windows: Usa "Anaconda Prompt" invece del Command Prompt normale
- Su Linux/macOS: Aggiungi conda al PATH o usa il percorso completo

### Problema: "PackagesNotFoundError"

**Soluzione:**
```bash
# Aggiungi il canale conda-forge
conda config --add channels conda-forge
conda config --set channel_priority strict

# Riprova l'installazione
conda env create -f environment.yml
```

### Problema: "Solving environment: failed"

**Soluzione:**
```bash
# Pulisci la cache
conda clean --all

# Aggiorna conda
conda update conda

# Riprova
conda env create -f environment.yml
```

### Problema: Conflitti di Versione

**Soluzione:**
```bash
# Crea un ambiente pulito
conda create -n trading-system-new python=3.11
conda activate trading-system-new

# Installa manualmente i pacchetti uno alla volta
conda install -c conda-forge ta-lib pandas numpy matplotlib
pip install -r requirements.txt
```

### Problema: ImportError dopo l'installazione

**Soluzione:**
```bash
# Verifica che l'ambiente sia attivo
conda info --envs

# Verifica quale Python stai usando
which python  # Linux/macOS
where python  # Windows

# Dovrebbe puntare all'ambiente trading-system
```

### Problema: TA-Lib non funziona

**Soluzione:**
```bash
# Disinstalla e reinstalla
conda remove ta-lib
conda install -c conda-forge ta-lib

# Verifica
python -c "import talib; print(talib.__version__)"
```

## Vantaggi di Anaconda

1. **Installazione TA-Lib Semplificata**: Niente compilatori, build tools o configurazioni complesse
2. **Gestione Dipendenze**: Risolve automaticamente i conflitti tra pacchetti
3. **Isolamento**: Ogni progetto ha il suo ambiente separato
4. **Riproducibilità**: Il file `environment.yml` garantisce che tutti abbiano lo stesso setup
5. **Multi-piattaforma**: Stesso comando funziona su Windows, Linux e macOS
6. **Performance**: Pacchetti scientifici ottimizzati (NumPy, Pandas, etc.)

## Differenze con pip/venv

| Caratteristica | Anaconda | pip/venv |
|---------------|----------|----------|
| TA-Lib su Windows | ✓ Facile | ✗ Difficile |
| Gestione dipendenze C | ✓ Automatica | ✗ Manuale |
| Dimensione | ~3GB (Anaconda) | ~50MB |
| Pacchetti scientifici | ✓ Ottimizzati | Standard |
| Curva di apprendimento | Media | Bassa |

## Comandi Utili

```bash
# Info ambiente corrente
conda info

# Lista pacchetti installati
conda list

# Cerca un pacchetto
conda search nome-pacchetto

# Info su un pacchetto specifico
conda list nome-pacchetto

# Aggiorna un pacchetto
conda update nome-pacchetto

# Rimuovi un pacchetto
conda remove nome-pacchetto

# Clona un ambiente
conda create --name nuovo-env --clone trading-system
```

## Prossimi Passi

Dopo aver installato l'ambiente:

1. Leggi [QUICKSTART.md](QUICKSTART.md) per iniziare
2. Configura le API keys in `.env`
3. Esegui un backtest per familiarizzare:
   ```bash
   python backtest.py
   ```
4. Leggi [ARCHITECTURE.md](ARCHITECTURE.md) per capire come funziona il sistema

## Supporto

Per problemi specifici:

1. Controlla la sezione [Risoluzione Problemi](#risoluzione-problemi)
2. Cerca negli [Issues di GitHub](https://github.com/your-repo/issues)
3. Apri un nuovo issue con:
   - Output di `conda info`
   - Output di `conda list`
   - Messaggio di errore completo
   - Sistema operativo

---

**Nota**: Questa guida assume l'uso di Anaconda/Miniconda. Se preferisci pip/venv, consulta [INSTALL.md](INSTALL.md).
