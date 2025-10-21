"""
LLM Advisor Plugin

Chiede consenso a un LLM prima di eseguire un trade.
L'LLM analizza indicatori tecnici e contesto di mercato.

Provider supportati:
- Anthropic (Claude)
- OpenAI (GPT)
- OpenRouter (accesso a multipli modelli: Claude, GPT, Gemini, Llama, Mistral, etc.)
"""

import anthropic
import openai
from loguru import logger
from typing import Dict, Tuple


class LLMAdvisor:
    """
    Plugin che consulta un LLM per ottenere consenso sui trade
    """

    def __init__(self, provider='anthropic', api_key=None, model=None, temperature=0.3):
        """
        Args:
            provider: 'anthropic', 'openai' o 'openrouter'
            api_key: API key del provider
            model: Modello da usare (opzionale)
            temperature: Temperature per risposte (0-1)
        """
        self.provider = provider
        self.api_key = api_key
        self.temperature = temperature

        if provider == 'anthropic':
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model or 'claude-3-5-sonnet-20241022'
        elif provider == 'openai':
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model or 'gpt-4-turbo'
        elif provider == 'openrouter':
            # OpenRouter usa l'API di OpenAI ma con base_url personalizzato
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            # Modelli consigliati OpenRouter:
            # - anthropic/claude-3.5-sonnet
            # - openai/gpt-4-turbo
            # - google/gemini-pro-1.5
            # - meta-llama/llama-3.1-70b-instruct
            # - mistralai/mistral-large
            self.model = model or 'anthropic/claude-3.5-sonnet'
        else:
            raise ValueError(f"Provider non supportato: {provider}")

        logger.info(f"LLM Advisor inizializzato: {provider} - {self.model}")

    def ask_trade_consent(self, signal_data: Dict) -> Tuple[bool, str]:
        """
        Chiede consenso all'LLM per un trade

        Args:
            signal_data: Dictionary con:
                - symbol: simbolo (es. BTCUSDT)
                - type: 'BUY' o 'SELL'
                - price: prezzo corrente
                - indicatori tecnici (rsi, macd, etc.)
                - market_context: contesto aggiuntivo

        Returns:
            tuple: (approved: bool, reason: str)
        """
        logger.info(f"Chiedendo consenso LLM per {signal_data['type']} {signal_data['symbol']}")

        prompt = self._build_prompt(signal_data)

        try:
            if self.provider == 'anthropic':
                response = self._call_anthropic(prompt)
            elif self.provider in ['openai', 'openrouter']:
                response = self._call_openai(prompt)
            else:
                raise ValueError(f"Provider non supportato: {self.provider}")

            # Parsa risposta
            approved = self._parse_response(response)

            logger.info(f"LLM risposta: {'APPROVED' if approved else 'REJECTED'}")
            logger.debug(f"LLM reasoning: {response}")

            return approved, response

        except Exception as e:
            logger.error(f"Errore chiamata LLM: {e}")
            return False, f"Errore LLM: {str(e)}"

    def _build_prompt(self, signal_data: Dict) -> str:
        """Costruisce il prompt per l'LLM"""

        prompt = f"""Sei un esperto trader di criptovalute. Analizza questa opportunità di trading e decidi se approvarla o rifiutarla.

TRADE PROPOSTO:
- Symbol: {signal_data['symbol']}
- Type: {signal_data['type']}
- Price: ${signal_data['price']:.2f}

INDICATORI TECNICI:
- RSI (14): {signal_data.get('rsi', 'N/A'):.2f}
- MACD: {signal_data.get('macd', 'N/A'):.4f}
- MACD Signal: {signal_data.get('signal', 'N/A'):.4f}
- SMA 20: ${signal_data.get('sma_20', 'N/A'):.2f}
- SMA 50: ${signal_data.get('sma_50', 'N/A'):.2f}
- ATR: {signal_data.get('atr', 'N/A'):.4f}
- Volume: {signal_data.get('volume', 'N/A'):.2f}
- Volume SMA: {signal_data.get('volume_sma_20', 'N/A'):.2f}

CONTESTO DI MERCATO:
{signal_data.get('market_context', 'N/A')}

ANALIZZA:
1. La direzione del trade (BUY/SELL) è coerente con gli indicatori?
2. Il momentum è favorevole?
3. Ci sono segnali contrastanti?
4. Il volume supporta il movimento?
5. Il livello di rischio è accettabile?

RISPONDI:
- Inizia con "APPROVE" se il trade è buono, oppure "REJECT" se ci sono dubbi
- Poi fornisci una breve motivazione (max 3 righe)

Esempio risposta:
APPROVE - RSI in oversold e MACD bullish cross confermano momentum rialzista. Volume sopra media supporta il movimento.

La tua analisi:"""

        return prompt

    def _call_anthropic(self, prompt: str) -> str:
        """Chiama API Anthropic (Claude)"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=self.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    def _call_openai(self, prompt: str) -> str:
        """Chiama API OpenAI (GPT)"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Sei un esperto trader di criptovalute."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=500
        )

        return response.choices[0].message.content

    def _parse_response(self, response: str) -> bool:
        """
        Parsa la risposta dell'LLM

        Returns:
            bool: True se APPROVE, False se REJECT
        """
        response_upper = response.upper()

        if 'APPROVE' in response_upper:
            return True
        elif 'REJECT' in response_upper:
            return False
        else:
            # Se non chiaro, rifiuta per sicurezza
            logger.warning(f"Risposta LLM ambigua: {response}")
            return False

    # ========================================================================
    # ADVANCED ANALYSIS
    # ========================================================================

    def get_market_analysis(self, symbol: str, timeframe_data: Dict) -> str:
        """
        Ottieni analisi di mercato dall'LLM per contesto

        Args:
            symbol: Simbolo crypto
            timeframe_data: Dati multi-timeframe

        Returns:
            str: Analisi testuale del mercato
        """
        prompt = f"""Analizza il contesto di mercato per {symbol} guardando diversi timeframes:

1m timeframe:
- Trend: {timeframe_data.get('1m', {}).get('trend', 'N/A')}
- RSI: {timeframe_data.get('1m', {}).get('rsi', 'N/A')}

5m timeframe:
- Trend: {timeframe_data.get('5m', {}).get('trend', 'N/A')}
- RSI: {timeframe_data.get('5m', {}).get('rsi', 'N/A')}

1h timeframe:
- Trend: {timeframe_data.get('1h', {}).get('trend', 'N/A')}
- RSI: {timeframe_data.get('1h', {}).get('rsi', 'N/A')}

Fornisci un breve riassunto (max 2 righe) del contesto di mercato generale."""

        try:
            if self.provider == 'anthropic':
                return self._call_anthropic(prompt)
            elif self.provider in ['openai', 'openrouter']:
                return self._call_openai(prompt)
            else:
                raise ValueError(f"Provider non supportato: {self.provider}")
        except Exception as e:
            logger.error(f"Errore market analysis: {e}")
            return "Market analysis not available"


# ============================================================================
# ESEMPIO DI UTILIZZO
# ============================================================================

if __name__ == '__main__':
    from config.settings import LLM_CONFIG

    advisor = LLMAdvisor(
        provider=LLM_CONFIG['provider'],
        api_key=LLM_CONFIG['api_key'],
        model=LLM_CONFIG['model']
    )

    # Esempio signal
    test_signal = {
        'symbol': 'BTCUSDT',
        'type': 'BUY',
        'price': 43250.50,
        'rsi': 28.5,
        'macd': 0.0023,
        'signal': -0.0012,
        'sma_20': 43100,
        'sma_50': 42800,
        'atr': 250.5,
        'volume': 1250000,
        'volume_sma_20': 1000000,
        'market_context': 'Bitcoin ha rotto resistenza a 43k con volume elevato'
    }

    approved, reason = advisor.ask_trade_consent(test_signal)

    print(f"Trade {'APPROVED' if approved else 'REJECTED'}")
    print(f"Reason: {reason}")
