"""
Esempi di utilizzo del LLM Advisor con OpenRouter

Questo file mostra come configurare e usare diversi modelli LLM
attraverso OpenRouter per ottenere consenso sui trade.
"""

from plugins.llm_advisor import LLMAdvisor
from loguru import logger
import os
from dotenv import load_dotenv

# Carica variabili ambiente
load_dotenv()

# ============================================================================
# ESEMPIO 1: Claude 3.5 Sonnet (Premium - Consigliato per produzione)
# ============================================================================

def example_claude_sonnet():
    """Usa Claude 3.5 Sonnet via OpenRouter"""

    advisor = LLMAdvisor(
        provider='openrouter',
        api_key=os.getenv('OPENROUTER_API_KEY'),
        model='anthropic/claude-3.5-sonnet',
        temperature=0.3
    )

    # Esempio signal BUY
    signal = {
        'symbol': 'BTCUSDT',
        'type': 'BUY',
        'price': 43250.50,
        'rsi': 28.5,  # Oversold
        'macd': 0.0023,
        'signal': -0.0012,  # MACD crossover bullish
        'sma_20': 43100,
        'sma_50': 42800,
        'atr': 250.5,
        'volume': 1250000,
        'volume_sma_20': 1000000,  # Volume sopra media
        'market_context': 'Bitcoin ha rotto resistenza a 43k con volume elevato'
    }

    approved, reason = advisor.ask_trade_consent(signal)

    print(f"\n{'='*60}")
    print(f"ESEMPIO 1: Claude 3.5 Sonnet")
    print(f"{'='*60}")
    print(f"Trade: {signal['type']} {signal['symbol']} @ ${signal['price']}")
    print(f"Decisione: {'✅ APPROVED' if approved else '❌ REJECTED'}")
    print(f"Motivazione:\n{reason}")
    print(f"{'='*60}\n")


# ============================================================================
# ESEMPIO 2: GPT-4 Turbo (Premium)
# ============================================================================

def example_gpt4_turbo():
    """Usa GPT-4 Turbo via OpenRouter"""

    advisor = LLMAdvisor(
        provider='openrouter',
        api_key=os.getenv('OPENROUTER_API_KEY'),
        model='openai/gpt-4-turbo',
        temperature=0.3
    )

    # Esempio signal SELL con segnali contrastanti
    signal = {
        'symbol': 'ETHUSDT',
        'type': 'SELL',
        'price': 2350.75,
        'rsi': 68.5,  # Vicino a overbought ma non estremo
        'macd': -0.0015,
        'signal': -0.0008,  # MACD ancora negativo
        'sma_20': 2340,
        'sma_50': 2320,  # Prezzo sopra SMA = trend rialzista
        'atr': 45.3,
        'volume': 850000,
        'volume_sma_20': 950000,  # Volume sotto media
        'market_context': 'ETH in consolidamento dopo rally. Volume in calo.'
    }

    approved, reason = advisor.ask_trade_consent(signal)

    print(f"\n{'='*60}")
    print(f"ESEMPIO 2: GPT-4 Turbo")
    print(f"{'='*60}")
    print(f"Trade: {signal['type']} {signal['symbol']} @ ${signal['price']}")
    print(f"Decisione: {'✅ APPROVED' if approved else '❌ REJECTED'}")
    print(f"Motivazione:\n{reason}")
    print(f"{'='*60}\n")


# ============================================================================
# ESEMPIO 3: Llama 3.1 70B (Economico - Consigliato per testing)
# ============================================================================

def example_llama_70b():
    """Usa Llama 3.1 70B Instruct via OpenRouter (economico)"""

    advisor = LLMAdvisor(
        provider='openrouter',
        api_key=os.getenv('OPENROUTER_API_KEY'),
        model='meta-llama/llama-3.1-70b-instruct',
        temperature=0.3
    )

    # Esempio signal BUY forte
    signal = {
        'symbol': 'SOLUSDT',
        'type': 'BUY',
        'price': 98.50,
        'rsi': 32.0,  # Oversold
        'macd': 0.0045,
        'signal': -0.0002,  # MACD appena crossato al rialzo
        'sma_20': 97.80,
        'sma_50': 95.20,  # Golden cross
        'atr': 3.2,
        'volume': 2500000,
        'volume_sma_20': 1800000,  # Volume molto sopra media
        'market_context': 'SOL in forte accumulation, rottura netta di resistenza'
    }

    approved, reason = advisor.ask_trade_consent(signal)

    print(f"\n{'='*60}")
    print(f"ESEMPIO 3: Llama 3.1 70B (Economico)")
    print(f"{'='*60}")
    print(f"Trade: {signal['type']} {signal['symbol']} @ ${signal['price']}")
    print(f"Decisione: {'✅ APPROVED' if approved else '❌ REJECTED'}")
    print(f"Motivazione:\n{reason}")
    print(f"{'='*60}\n")


# ============================================================================
# ESEMPIO 4: Gemini Pro 1.5 (Buon bilanciamento qualità/prezzo)
# ============================================================================

def example_gemini_pro():
    """Usa Google Gemini Pro 1.5 via OpenRouter"""

    advisor = LLMAdvisor(
        provider='openrouter',
        api_key=os.getenv('OPENROUTER_API_KEY'),
        model='google/gemini-pro-1.5',
        temperature=0.3
    )

    # Esempio signal SELL in trend ribassista
    signal = {
        'symbol': 'ADAUSDT',
        'type': 'SELL',
        'price': 0.4850,
        'rsi': 72.0,  # Overbought
        'macd': -0.0002,
        'signal': 0.0001,  # MACD crossover bearish
        'sma_20': 0.4920,
        'sma_50': 0.5050,  # Death cross
        'atr': 0.015,
        'volume': 450000,
        'volume_sma_20': 420000,
        'market_context': 'ADA mostra debolezza, resistenza a 0.50 non superata'
    }

    approved, reason = advisor.ask_trade_consent(signal)

    print(f"\n{'='*60}")
    print(f"ESEMPIO 4: Gemini Pro 1.5")
    print(f"{'='*60}")
    print(f"Trade: {signal['type']} {signal['symbol']} @ ${signal['price']}")
    print(f"Decisione: {'✅ APPROVED' if approved else '❌ REJECTED'}")
    print(f"Motivazione:\n{reason}")
    print(f"{'='*60}\n")


# ============================================================================
# ESEMPIO 5: DeepSeek Chat (Ultra economico)
# ============================================================================

def example_deepseek():
    """Usa DeepSeek Chat via OpenRouter (molto economico)"""

    advisor = LLMAdvisor(
        provider='openrouter',
        api_key=os.getenv('OPENROUTER_API_KEY'),
        model='deepseek/deepseek-chat',
        temperature=0.3
    )

    # Esempio signal con alta volatilità
    signal = {
        'symbol': 'DOGEUSDT',
        'type': 'BUY',
        'price': 0.0825,
        'rsi': 45.0,  # Neutrale
        'macd': 0.00001,
        'signal': -0.000005,
        'sma_20': 0.0820,
        'sma_50': 0.0815,
        'atr': 0.0035,  # Alta volatilità
        'volume': 5500000,
        'volume_sma_20': 3200000,  # Volume esplosivo
        'market_context': 'DOGE pump da news Elon Musk, alta volatilità'
    }

    approved, reason = advisor.ask_trade_consent(signal)

    print(f"\n{'='*60}")
    print(f"ESEMPIO 5: DeepSeek Chat (Ultra Economico)")
    print(f"{'='*60}")
    print(f"Trade: {signal['type']} {signal['symbol']} @ ${signal['price']}")
    print(f"Decisione: {'✅ APPROVED' if approved else '❌ REJECTED'}")
    print(f"Motivazione:\n{reason}")
    print(f"{'='*60}\n")


# ============================================================================
# ESEMPIO 6: Confronto tra modelli sullo stesso signal
# ============================================================================

def example_model_comparison():
    """Confronta le decisioni di diversi modelli LLM sullo stesso signal"""

    # Signal ambiguo (segnali contrastanti)
    signal = {
        'symbol': 'BNBUSDT',
        'type': 'BUY',
        'price': 315.50,
        'rsi': 55.0,  # Neutrale
        'macd': 0.0008,  # Debolmente positivo
        'signal': 0.0006,
        'sma_20': 314.00,
        'sma_50': 316.00,  # Prezzo tra le medie
        'atr': 8.5,
        'volume': 780000,
        'volume_sma_20': 820000,  # Volume leggermente sotto
        'market_context': 'BNB in range trading, nessun trend chiaro'
    }

    models = [
        ('anthropic/claude-3.5-sonnet', 'Claude 3.5 Sonnet'),
        ('openai/gpt-4-turbo', 'GPT-4 Turbo'),
        ('meta-llama/llama-3.1-70b-instruct', 'Llama 3.1 70B'),
        ('google/gemini-pro-1.5', 'Gemini Pro 1.5'),
    ]

    print(f"\n{'='*80}")
    print(f"ESEMPIO 6: Confronto Modelli su Signal Ambiguo")
    print(f"{'='*80}")
    print(f"Trade: {signal['type']} {signal['symbol']} @ ${signal['price']}")
    print(f"RSI: {signal['rsi']} (neutrale) | MACD: debolmente positivo | Volume: sotto media")
    print(f"{'='*80}\n")

    results = []

    for model_id, model_name in models:
        try:
            advisor = LLMAdvisor(
                provider='openrouter',
                api_key=os.getenv('OPENROUTER_API_KEY'),
                model=model_id,
                temperature=0.3
            )

            approved, reason = advisor.ask_trade_consent(signal)
            results.append((model_name, approved, reason))

            print(f"📊 {model_name}:")
            print(f"   Decisione: {'✅ APPROVED' if approved else '❌ REJECTED'}")
            print(f"   Motivazione: {reason[:150]}...")
            print()

        except Exception as e:
            print(f"❌ {model_name}: Errore - {e}\n")

    # Statistiche
    approvals = sum(1 for _, approved, _ in results if approved)
    rejections = len(results) - approvals

    print(f"{'='*80}")
    print(f"Risultati Confronto:")
    print(f"  ✅ Approvazioni: {approvals}/{len(results)}")
    print(f"  ❌ Rifiuti: {rejections}/{len(results)}")
    print(f"{'='*80}\n")


# ============================================================================
# MAIN - Esegui tutti gli esempi
# ============================================================================

if __name__ == '__main__':

    print("\n" + "="*80)
    print("ESEMPI DI UTILIZZO OPENROUTER CON TRADING SYSTEM")
    print("="*80 + "\n")

    # Verifica API key
    if not os.getenv('OPENROUTER_API_KEY'):
        print("❌ ERRORE: OPENROUTER_API_KEY non trovata in .env")
        print("   Segui la guida in docs/OPENROUTER_SETUP.md")
        exit(1)

    # Menu scelta esempi
    print("Scegli quale esempio eseguire:")
    print("1. Claude 3.5 Sonnet (Premium)")
    print("2. GPT-4 Turbo (Premium)")
    print("3. Llama 3.1 70B (Economico)")
    print("4. Gemini Pro 1.5 (Bilanciato)")
    print("5. DeepSeek Chat (Ultra Economico)")
    print("6. Confronto tra tutti i modelli")
    print("7. Esegui tutti gli esempi")
    print()

    choice = input("Scelta (1-7): ").strip()

    if choice == '1':
        example_claude_sonnet()
    elif choice == '2':
        example_gpt4_turbo()
    elif choice == '3':
        example_llama_70b()
    elif choice == '4':
        example_gemini_pro()
    elif choice == '5':
        example_deepseek()
    elif choice == '6':
        example_model_comparison()
    elif choice == '7':
        example_claude_sonnet()
        example_gpt4_turbo()
        example_llama_70b()
        example_gemini_pro()
        example_deepseek()
        example_model_comparison()
    else:
        print("❌ Scelta non valida")

    print("\n✅ Esempi completati!\n")
