# Guida OpenRouter per Trading System

## Cos'è OpenRouter?

OpenRouter è un servizio che fornisce accesso unificato a molteplici modelli LLM attraverso una singola API. Questo ti permette di:

- **Scegliere tra molti modelli**: Claude, GPT-4, Gemini, Llama, Mistral, DeepSeek e altri
- **Pagare solo quello che usi**: prezzi competitivi e trasparenti
- **Fallback automatico**: se un modello non è disponibile, passa automaticamente a un altro
- **Nessun rate limiting aggressivo**: più flessibile rispetto agli API diretti

## Setup

### 1. Ottieni la tua API Key

1. Vai su [https://openrouter.ai](https://openrouter.ai)
2. Crea un account
3. Vai su [https://openrouter.ai/keys](https://openrouter.ai/keys)
4. Crea una nuova API key

### 2. Configura il file `.env`

Copia `.env.example` in `.env` e inserisci la tua chiave:

```bash
cp .env.example .env
```

Modifica `.env`:

```bash
# OpenRouter API Key
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
```

### 3. Scegli il modello

Modifica `config/settings.py` per selezionare il modello che preferisci:

```python
LLM_CONFIG = {
    'enabled': True,
    'provider': 'openrouter',
    'api_key': os.getenv('OPENROUTER_API_KEY'),
    'model': 'anthropic/claude-3.5-sonnet',  # Cambia qui
    'temperature': 0.3,
}
```

## Modelli Consigliati per Trading

### Modelli Premium (alta qualità)

| Modello | Descrizione | Costo per 1M tokens |
|---------|-------------|---------------------|
| `anthropic/claude-3.5-sonnet` | Eccellente per analisi complesse | $3 input / $15 output |
| `openai/gpt-4-turbo` | Ottimo per ragionamento strutturato | $10 input / $30 output |
| `google/gemini-pro-1.5` | Buon bilanciamento qualità/prezzo | $1.25 input / $5 output |
| `anthropic/claude-3-opus` | Massima qualità (più costoso) | $15 input / $75 output |

### Modelli Economici (buon rapporto qualità/prezzo)

| Modello | Descrizione | Costo per 1M tokens |
|---------|-------------|---------------------|
| `meta-llama/llama-3.1-70b-instruct` | Open source, ottima qualità | $0.35 input / $0.40 output |
| `mistralai/mistral-large` | Veloce ed economico | $2 input / $6 output |
| `deepseek/deepseek-chat` | Molto economico, buona qualità | $0.14 input / $0.28 output |
| `google/gemini-flash-1.5` | Ultra economico e veloce | $0.075 input / $0.30 output |

### Modelli Gratuiti (per testing)

| Modello | Descrizione | Note |
|---------|-------------|------|
| `meta-llama/llama-3-8b-instruct:free` | Llama 3 gratuito | Rate limits più bassi |
| `google/gemma-7b-it:free` | Gemma gratuito | Buono per test |

## Configurazioni Consigliate

### Per Produzione (alta affidabilità)

```python
LLM_CONFIG = {
    'enabled': True,
    'provider': 'openrouter',
    'api_key': os.getenv('OPENROUTER_API_KEY'),
    'model': 'anthropic/claude-3.5-sonnet',
    'temperature': 0.3,  # Bassa temperatura per decisioni conservative
    'max_tokens': 500,
    'timeout': 10,
    'retry_on_error': True,
    'fallback_to_approve': False,  # IMPORTANTE: non approvare se LLM offline
}
```

### Per Testing (economico)

```python
LLM_CONFIG = {
    'enabled': True,
    'provider': 'openrouter',
    'api_key': os.getenv('OPENROUTER_API_KEY'),
    'model': 'meta-llama/llama-3.1-70b-instruct',  # Economico ma buono
    'temperature': 0.3,
    'max_tokens': 500,
    'timeout': 10,
    'retry_on_error': True,
    'fallback_to_approve': False,
}
```

### Per Sviluppo (gratis)

```python
LLM_CONFIG = {
    'enabled': True,
    'provider': 'openrouter',
    'api_key': os.getenv('OPENROUTER_API_KEY'),
    'model': 'meta-llama/llama-3-8b-instruct:free',  # Gratuito
    'temperature': 0.3,
    'max_tokens': 500,
    'timeout': 15,  # Timeout più lungo per modelli gratuiti
    'retry_on_error': True,
    'fallback_to_approve': False,
}
```

## Come Cambiare Modello

Puoi cambiare modello in qualsiasi momento modificando solo la riga `'model'` in `config/settings.py`:

```python
# Esempio: passa da Claude a GPT-4
'model': 'openai/gpt-4-turbo',

# Esempio: passa a Gemini
'model': 'google/gemini-pro-1.5',

# Esempio: passa a Llama (economico)
'model': 'meta-llama/llama-3.1-70b-instruct',
```

Poi riavvia il sistema:

```bash
python main.py
```

## Monitorare i Costi

OpenRouter fornisce una dashboard dove puoi monitorare:
- Costi in tempo reale
- Numero di richieste
- Modelli utilizzati
- Rate limits

Dashboard: [https://openrouter.ai/activity](https://openrouter.ai/activity)

## Confronto con Altri Provider

### OpenRouter vs Anthropic Diretto

**Vantaggi OpenRouter:**
- Accesso a più modelli (Claude, GPT, Gemini, etc.)
- Fallback automatico se un modello è offline
- Dashboard unificata per tutti i modelli
- Spesso più economico per volumi bassi

**Vantaggi Anthropic Diretto:**
- Latenza leggermente inferiore
- Accesso anticipato a nuovi modelli
- Maggiore quota mensile

### OpenRouter vs OpenAI Diretto

**Vantaggi OpenRouter:**
- Prezzi spesso migliori
- Accesso a modelli oltre GPT (Claude, Gemini, etc.)
- Nessun rate limiting aggressivo
- Fallback automatico

**Vantaggi OpenAI Diretto:**
- Latenza leggermente inferiore
- Accesso immediato a GPT-4 Turbo/GPT-4o

## Troubleshooting

### Errore: Invalid API Key

Verifica che:
1. La chiave API sia corretta in `.env`
2. La chiave inizi con `sk-or-v1-`
3. Hai crediti sufficienti su OpenRouter

### Errore: Model not found

Verifica che il nome del modello sia corretto:
- Deve includere il provider: `anthropic/claude-3.5-sonnet`
- Non solo il nome: ~~`claude-3.5-sonnet`~~ (errato)

### Timeout troppo frequenti

Aumenta il timeout in `config/settings.py`:

```python
'timeout': 20,  # Aumenta da 10 a 20 secondi
```

### Rate limit raggiunto

Passa a un modello a pagamento o:
1. Aggiungi crediti su OpenRouter
2. Riduci la frequenza dei trade
3. Disabilita temporaneamente LLM: `'enabled': False`

## Risorse Utili

- **Lista completa modelli**: https://openrouter.ai/models
- **Documentazione API**: https://openrouter.ai/docs
- **Discord community**: https://discord.gg/openrouter
- **Status page**: https://status.openrouter.ai

## Sicurezza

⚠️ **IMPORTANTE**:

1. **Non condividere la tua API key**: è come una password
2. **Usa file `.env`**: mai hardcodare la key nel codice
3. **Aggiungi `.env` a `.gitignore`**: già configurato nel progetto
4. **Monitora i costi**: imposta limiti su OpenRouter dashboard
5. **Fallback sicuro**: mantieni `'fallback_to_approve': False`

## Supporto

Per problemi con OpenRouter:
- Documentazione: https://openrouter.ai/docs
- Discord: https://discord.gg/openrouter
- Email: support@openrouter.ai

Per problemi con il Trading System:
- Controlla i log: `logs/trading.log`
- Abilita debug: `LOGGING_CONFIG['level'] = 'DEBUG'`
