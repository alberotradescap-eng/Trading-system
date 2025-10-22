# Guida OpenRouter - Configurazione LLM

Questa guida ti spiega come configurare OpenRouter per usare diversi modelli LLM nel tuo sistema di trading.

## Cos'è OpenRouter?

OpenRouter è un servizio che ti dà accesso a **molti modelli LLM diversi** con una sola API key. Invece di dover creare account separati per Anthropic, OpenAI, Google, Meta, ecc., puoi usare OpenRouter per accedervi tutti.

### Vantaggi di OpenRouter

- **Una sola API key** per accedere a tutti i modelli
- **Prezzi competitivi** - spesso più economici dei provider diretti
- **Flessibilità** - cambi modello semplicemente modificando una stringa
- **Facilità** - API compatibile con OpenAI, quindi facile da integrare

## Setup Rapido

### 1. Ottieni API Key

1. Vai su https://openrouter.ai/
2. Crea un account (gratis)
3. Vai su https://openrouter.ai/keys
4. Clicca "Create Key"
5. Copia la tua API key

### 2. Configura il file .env

Aggiungi la tua API key al file `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Configura settings.py

Modifica `config/settings.py`:

```python
LLM_CONFIG = {
    'enabled': True,
    'provider': 'openrouter',  # Cambia da 'anthropic' a 'openrouter'
    'api_key': os.getenv('OPENROUTER_API_KEY'),  # Usa la chiave di OpenRouter
    'model': 'anthropic/claude-3.5-sonnet',  # Scegli il modello (vedi sotto)
    'temperature': 0.3,
    'max_tokens': 500,
    'timeout': 10,
    'retry_on_error': True,
    'fallback_to_approve': False,
}
```

## Modelli Disponibili

Ecco i modelli più popolari disponibili su OpenRouter:

### Claude (Anthropic) - Ottimo per analisi
```python
'model': 'anthropic/claude-3.5-sonnet'        # Veloce, accurato (consigliato)
'model': 'anthropic/claude-3-opus'            # Più potente ma più costoso
'model': 'anthropic/claude-3-haiku'           # Economico e velocissimo
```

### GPT (OpenAI) - Versatile
```python
'model': 'openai/gpt-4-turbo'                 # GPT-4 Turbo
'model': 'openai/gpt-4'                       # GPT-4 standard
'model': 'openai/gpt-3.5-turbo'               # Economico
```

### Llama (Meta) - Open Source
```python
'model': 'meta-llama/llama-3.1-70b-instruct'  # Llama 3.1 70B
'model': 'meta-llama/llama-3.1-405b-instruct' # Llama 3.1 405B (molto potente)
```

### Gemini (Google)
```python
'model': 'google/gemini-pro-1.5'              # Gemini Pro 1.5
'model': 'google/gemini-flash-1.5'            # Più veloce ed economico
```

### Altri Modelli Interessanti
```python
'model': 'mistralai/mistral-large'            # Mistral Large
'model': 'deepseek/deepseek-chat'             # DeepSeek (economico)
'model': 'qwen/qwen-2.5-72b-instruct'         # Qwen 2.5
'model': 'anthropic/claude-3.5-sonnet:beta'   # Claude con extended thinking
```

Lista completa: https://openrouter.ai/models

## Scelta del Modello

Per trading, consiglio:

### Per Analisi Approfondita
- `anthropic/claude-3.5-sonnet` ✅ **CONSIGLIATO**
- `openai/gpt-4-turbo`
- `meta-llama/llama-3.1-405b-instruct`

### Per Velocità ed Economia
- `anthropic/claude-3-haiku`
- `google/gemini-flash-1.5`
- `deepseek/deepseek-chat`

### Per Massima Potenza
- `anthropic/claude-3-opus`
- `meta-llama/llama-3.1-405b-instruct`

## Prezzi

OpenRouter ha prezzi competitivi. Alcuni esempi (per milione di token):

- Claude 3.5 Sonnet: ~$3 input / ~$15 output
- GPT-4 Turbo: ~$10 input / ~$30 output
- Llama 3.1 70B: ~$0.50 input / ~$0.75 output
- DeepSeek: ~$0.15 input / ~$0.60 output

**Per il trading con LLM_CONFIG max_tokens=500, un singolo trade costa circa $0.001-0.01 a seconda del modello.**

Vedi prezzi aggiornati: https://openrouter.ai/models

## Esempio Configurazione Completa

Ecco una configurazione completa in `config/settings.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

LLM_CONFIG = {
    # Abilita/disabilita LLM advisor
    'enabled': True,

    # Provider: usa OpenRouter
    'provider': 'openrouter',

    # API Key da file .env
    'api_key': os.getenv('OPENROUTER_API_KEY'),

    # Modello: Claude 3.5 Sonnet (ottimo rapporto qualità/prezzo)
    'model': 'anthropic/claude-3.5-sonnet',

    # Temperature: 0.3 = risposte consistenti e analitiche
    'temperature': 0.3,

    # Max tokens: 500 è sufficiente per APPROVE/REJECT + reasoning
    'max_tokens': 500,

    # Timeout: 10 secondi
    'timeout': 10,

    # Retry se API fallisce
    'retry_on_error': True,

    # IMPORTANTE: False = se LLM è offline, NON approvare il trade
    'fallback_to_approve': False,
}
```

## Test della Configurazione

Per testare che tutto funzioni:

```bash
python plugins/llm_advisor.py
```

Questo eseguirà un trade di esempio e ti mostrerà la risposta del LLM.

## Cambiare Modello al Volo

Puoi cambiare modello semplicemente modificando la stringa in `settings.py`:

```python
# Prova Claude
'model': 'anthropic/claude-3.5-sonnet',

# Poi prova GPT-4
'model': 'openai/gpt-4-turbo',

# Poi prova Llama
'model': 'meta-llama/llama-3.1-70b-instruct',
```

Non serve modificare altro codice!

## Monitoraggio Usage

Puoi vedere quanto spendi su OpenRouter:

1. Vai su https://openrouter.ai/activity
2. Vedi tutte le richieste e i costi
3. Imposta limiti di spesa se vuoi

## FAQ

### Q: Posso usare sia Anthropic diretto che OpenRouter?
A: Sì, basta cambiare `provider` e `api_key` in `settings.py`.

### Q: Quale modello è più accurato per trading?
A: Claude 3.5 Sonnet ha ottime performance per analisi tecnica. GPT-4 Turbo è ottimo per ragionamento complesso.

### Q: Come riduco i costi?
A: Usa modelli più economici come `claude-3-haiku` o `deepseek-chat`, oppure disabilita LLM per trade con alta confidence.

### Q: OpenRouter è affidabile?
A: Sì, è un servizio stabile usato da migliaia di developer. Ha SLA e monitoring.

## Supporto

- Documentazione OpenRouter: https://openrouter.ai/docs
- Discord OpenRouter: https://discord.gg/openrouter
- Status page: https://status.openrouter.ai/

## Conclusione

OpenRouter ti dà **massima flessibilità** per scegliere il miglior LLM per le tue esigenze di trading, con un setup semplicissimo.

Inizia con `anthropic/claude-3.5-sonnet` e sperimenta! 🚀
